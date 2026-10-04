"""Abuse protections for the public endpoints: real client IP, per-IP
throttling and Cloudflare Turnstile.

Added after an automated attack (2026-10-03) made 232 admin password guesses
and minted ~40 accounts through the register and checkout forms, none of which
was slowed down or attributable to an address — everything the app logged was
Caddy's internal IP.
"""

import contextlib
import fcntl
import ipaddress
import json
import logging
import os
import re
import tempfile
import time
import urllib.parse
import urllib.request

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse

logger = logging.getLogger(__name__)


# --------------------------------------------------------------- client IP

def _valid_ip(value):
    try:
        return str(ipaddress.ip_address((value or '').strip()))
    except ValueError:
        return None


def client_ip(request):
    """The visitor's address, not the reverse proxy's.

    Gunicorn only ever sees Caddy (a private docker address), which sets
    ``X-Forwarded-For`` to the real peer. The header is trusted only when the
    direct peer is on a private network — i.e. it is our own proxy — so it
    cannot be spoofed by someone reaching the app some other way. The LAST
    entry is used because that is the one written by the nearest proxy.
    """
    remote = _valid_ip(request.META.get('REMOTE_ADDR')) or ''
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded and remote:
        peer = ipaddress.ip_address(remote)
        if peer.is_private or peer.is_loopback:
            candidate = _valid_ip(forwarded.split(',')[-1])
            if candidate:
                return candidate
    return remote or None


# --------------------------------------------------------------- throttling

# scope -> [(max POSTs, window seconds), ...]. Counted per client IP. Generous
# enough for people sharing an address, far below what a guessing script needs.
THROTTLE_RULES = {
    'login': [(10, 300), (40, 3600)],        # password + admin login
    'code': [(10, 600)],                     # 6-digit login / 2FA code entry
    'email': [(5, 900)],                     # endpoints that send an email
    'register': [(5, 3600)],
    'checkout': [(6, 3600)],
}


def _throttle_patterns():
    admin = re.escape(settings.ADMIN_PATH.strip('/'))
    return [
        ('login', re.compile(r'^/(auth/login|%s/login)/$' % admin)),
        ('code', re.compile(r'^/auth/(login-code/verify|two-factor/verify)/$')),
        ('email', re.compile(r'^/auth/(login-code|forgot-password|resend-verification)/$')),
        ('register', re.compile(r'^/auth/register/$')),
        ('checkout', re.compile(r'^/buy/[^/]+/$')),
    ]


def _bucket(ip):
    """The key a client is counted under. An IPv6 customer is handed a whole
    /64, so counting single addresses would let one machine rotate through
    billions of them; the /64 is the smallest unit that maps to one visitor."""
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return ip
    if addr.version == 6:
        return str(ipaddress.ip_network('%s/64' % addr, strict=False).network_address) + '/64'
    return str(addr)


_LOCK_PATH = os.path.join(tempfile.gettempdir(), 'summit-throttle.lock')


@contextlib.contextmanager
def _counter_lock():
    """Serialise counter updates across gunicorn workers. The file cache's
    incr() is a separate read and write, so parallel requests landing on
    different workers could all read the same value and be counted once —
    a burst would get through several times over the limit."""
    with open(_LOCK_PATH, 'a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _hit(scope, ident, limit, window):
    """Count one event in the current fixed window; return seconds to wait if
    this event is over the limit, else 0."""
    now = int(time.time())
    key = 'throttle:%s:%s:%d:%d' % (scope, ident, window, now // window)
    with _counter_lock():
        count = (cache.get(key) or 0) + 1
        cache.set(key, count, timeout=window)
    return (window - now % window) if count > limit else 0


_TOO_MANY = (
    '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    '<title>Too many attempts</title>'
    '<body style="font-family:system-ui,sans-serif;max-width:32rem;margin:15vh auto;padding:0 1rem;text-align:center">'
    '<h1 style="font-size:1.4rem">Too many attempts</h1>'
    '<p>For your security we have paused requests from your network for a few minutes. '
    'Please wait and try again.</p></body>'
)


class AuthThrottleMiddleware:
    """Cap POSTs to the login, code, registration and checkout endpoints per IP."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.patterns = _throttle_patterns()

    def __call__(self, request):
        if request.method == 'POST' and getattr(settings, 'AUTH_THROTTLE_ENABLED', True):
            for scope, pattern in self.patterns:
                if pattern.match(request.path):
                    ip = client_ip(request) or 'unknown'
                    # A list, not a generator: every window must be counted.
                    wait = max([_hit(scope, _bucket(ip), limit, window)
                                for limit, window in THROTTLE_RULES[scope]])
                    if wait:
                        logger.warning('Throttled %s POST %s from %s', scope, request.path, ip)
                        response = HttpResponse(_TOO_MANY, status=429)
                        response['Retry-After'] = str(wait)
                        return response
                    break
        return self.get_response(request)


# ---------------------------------------------------------------- Turnstile

TURNSTILE_VERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
TURNSTILE_FAILED_MESSAGE = (
    'We could not confirm you are human. Please complete the check below and try again.'
)


def turnstile_enabled():
    return bool(getattr(settings, 'TURNSTILE_SITEKEY', '') and getattr(settings, 'TURNSTILE_SECRET', ''))


def _siteverify(token, remote_ip):
    data = {'secret': settings.TURNSTILE_SECRET, 'response': token}
    if remote_ip:
        data['remoteip'] = remote_ip
    req = urllib.request.Request(TURNSTILE_VERIFY_URL, data=urllib.parse.urlencode(data).encode())
    with urllib.request.urlopen(req, timeout=8) as resp:
        return json.load(resp)


def turnstile_ok(request):
    """True when the submission carries a valid Turnstile token, or when
    Turnstile is not configured (no keys in the environment). An unreachable
    verification service counts as a failure — fail closed."""
    if not turnstile_enabled():
        return True
    token = (request.POST.get('cf-turnstile-response') or '').strip()
    if not token:
        return False
    try:
        result = _siteverify(token, client_ip(request))
    except (OSError, ValueError):
        logger.exception('Turnstile verification could not be completed')
        return False
    if not result.get('success'):
        logger.warning('Turnstile rejected a submission from %s: %s',
                       client_ip(request), result.get('error-codes'))
        return False
    return True
