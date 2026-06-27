"""Project-wide template context."""
from decouple import config


def site_globals(request):
    return {
        'SITE_NAME': config('SITE_NAME', default='Summit Teachable'),
        'SITE_URL': config('SITE_URL', default='http://localhost:8000'),
    }
