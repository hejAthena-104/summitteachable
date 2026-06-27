from django.core.management.base import BaseCommand
from django.utils.text import slugify

from copytrading.models import MasterTrader

# Demo / illustrative master traders. None of these are real people and none of
# the stats represent real performance — this platform is simulated practice only.
DEMO_TRADERS = [
    {
        "name": "Alex Rivera",
        "headline": "Swing trader · FX & indices",
        "strategy": (
            "Demo profile. Multi-day swing positions on major FX pairs and "
            "index CFDs, leaning on trend continuation and pullback entries. "
            "Illustrative strategy for practice only."
        ),
        "win_rate": "68.0",
        "return_pct": "14.2",
        "followers": 1840,
        "risk_level": MasterTrader.RISK_MEDIUM,
        "markets": "Forex, Indices",
        "accent": MasterTrader.ACCENT_EMERALD,
        "order": 1,
    },
    {
        "name": "Mia Chen",
        "headline": "Crypto momentum · high conviction",
        "strategy": (
            "Demo profile. Momentum-driven crypto entries riding breakouts and "
            "volatility expansion. Higher risk, illustrative figures only."
        ),
        "win_rate": "61.0",
        "return_pct": "22.8",
        "followers": 3120,
        "risk_level": MasterTrader.RISK_HIGH,
        "markets": "Crypto",
        "accent": MasterTrader.ACCENT_VIOLET,
        "order": 2,
    },
    {
        "name": "Daniel Okoro",
        "headline": "Indices scalper · tight risk",
        "strategy": (
            "Demo profile. Intraday scalps on index futures with strict stops "
            "and small, frequent targets. Low-risk illustrative profile."
        ),
        "win_rate": "73.0",
        "return_pct": "9.4",
        "followers": 2270,
        "risk_level": MasterTrader.RISK_LOW,
        "markets": "Indices",
        "accent": MasterTrader.ACCENT_BLUE,
        "order": 3,
    },
    {
        "name": "Sofia Marenko",
        "headline": "Gold & commodities · macro swing",
        "strategy": (
            "Demo profile. Macro-driven swing trades in gold and commodity "
            "markets, blending fundamentals with technical levels. "
            "Illustrative practice profile."
        ),
        "win_rate": "65.0",
        "return_pct": "11.1",
        "followers": 1490,
        "risk_level": MasterTrader.RISK_MEDIUM,
        "markets": "Gold, Commodities",
        "accent": MasterTrader.ACCENT_AMBER,
        "order": 4,
    },
    {
        "name": "Liam Brooks",
        "headline": "S&P swing · trend follower",
        "strategy": (
            "Demo profile. Patient trend-following swing trades on the S&P 500, "
            "holding winners across multiple sessions. Low-risk illustrative "
            "profile for practice."
        ),
        "win_rate": "70.0",
        "return_pct": "8.7",
        "followers": 1985,
        "risk_level": MasterTrader.RISK_LOW,
        "markets": "Indices, Stocks",
        "accent": MasterTrader.ACCENT_TEAL,
        "order": 5,
    },
    {
        "name": "Priya Nair",
        "headline": "FX breakout · session opens",
        "strategy": (
            "Demo profile. Breakout entries around London and New York session "
            "opens on major FX pairs. Medium risk, illustrative only."
        ),
        "win_rate": "64.0",
        "return_pct": "12.6",
        "followers": 1320,
        "risk_level": MasterTrader.RISK_MEDIUM,
        "markets": "Forex",
        "accent": MasterTrader.ACCENT_EMERALD,
        "order": 6,
    },
]


class Command(BaseCommand):
    help = "Seed demo/illustrative master traders for the simulated copy-trading app (idempotent)."

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        for data in DEMO_TRADERS:
            slug = slugify(data["name"])
            defaults = {k: v for k, v in data.items() if k != "name"}
            defaults["slug"] = slug
            obj, created = MasterTrader.objects.update_or_create(
                name=data["name"],
                defaults=defaults,
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded demo master traders: {created_count} created, "
                f"{updated_count} updated. (All simulated / practice only.)"
            )
        )
