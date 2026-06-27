"""Project-wide template context.

Exposes the persistent DEMO/paper-account framing and basic site identity to
every template. The DEMO badge that this drives MUST stay visible on the
dashboard, wallet, and every deposit/withdraw/transfer/copy-trading screen —
this is a hard product constraint: Summit Teachable is a simulated paper-trading
education platform and never takes or holds real money.
"""
from decouple import config


def site_globals(request):
    return {
        'SITE_NAME': config('SITE_NAME', default='Summit Teachable'),
        'SITE_URL': config('SITE_URL', default='http://localhost:8000'),
        # Demo framing — read by the global badge include and labels everywhere.
        'DEMO_MODE': config('DEMO_MODE', default=True, cast=bool),
        'DEMO_LABEL': 'DEMO · Paper Account',
        'DEMO_NOTE': 'Simulated funds — not real money.',
    }
