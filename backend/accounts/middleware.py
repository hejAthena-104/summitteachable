"""Middleware that gates the courses + store behind a platform access code.

Authenticated users without `has_course_access` are redirected to the access
gate before they can reach any /education/ or /buy/ path. Staff bypass the gate
(handled by `User.has_course_access`). Anonymous users are sent to login first,
so the unlock can be persisted to their account afterwards.
"""

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


# Path prefixes that require a redeemed access code.
GATED_PREFIXES = ('/education/', '/buy/')


class CourseAccessGateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if any(path.startswith(p) for p in GATED_PREFIXES):
            user = request.user
            if not user.is_authenticated:
                login_url = getattr(settings, 'LOGIN_URL', '/auth/login/')
                return redirect(f'{login_url}?next={path}')
            if not user.has_course_access:
                gate_url = reverse('accounts:access_gate')
                return redirect(f'{gate_url}?next={path}')
        return self.get_response(request)
