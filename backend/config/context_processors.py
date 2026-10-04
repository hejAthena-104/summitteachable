"""Project-wide template context."""
from decouple import config
from django.conf import settings


def site_globals(request):
    return {
        'SITE_NAME': config('SITE_NAME', default='Summit Teachable'),
        'SITE_URL': config('SITE_URL', default='http://localhost:8000'),
        # Empty unless both Turnstile keys are configured — see config/security.py.
        'TURNSTILE_SITEKEY': settings.TURNSTILE_SITEKEY if settings.TURNSTILE_SECRET else '',
    }
