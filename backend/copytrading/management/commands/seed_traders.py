from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from copytrading.models import MasterTrader, MasterTrade

# Sample trade log seeded for each master (only when they have none yet).
# (currency, symbol, amount, direction, result, status, is_verified, days_ago)
SAMPLE_TRADES = [
    ("Bitcoin", "BTC/USD", "1200.00", "rise", "win", "closed", True, 1),
    ("Ethereum", "ETH/USD", "800.00", "fall", "loss", "closed", True, 2),
    ("Euro", "EUR/USD", "1500.00", "rise", "win", "closed", True, 3),
    ("Gold", "XAU/USD", "1000.00", "rise", "pending", "open", False, 0),
    ("Solana", "SOL/USD", "600.00", "fall", "draw", "closed", True, 4),
    ("Bitcoin", "BTC/USD", "950.00", "rise", "win", "closed", True, 6),
]

MASTER_TRADERS = [
    {
        "name": "Alex Rivera",
        "headline": "Swing trader · FX & indices",
        "strategy": (
            "Multi-day swing positions on major FX pairs and "
            "index CFDs, leaning on trend continuation and pullback entries. "
            "Built around structured risk and clean pullback entries."
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
            "Momentum-driven crypto entries riding breakouts and volatility "
            "expansion with higher-risk positioning."
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
            "Intraday scalps on index futures with strict stops and small, "
            "frequent targets."
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
            "Macro-driven swing trades in gold and commodity markets, blending "
            "fundamentals with technical levels."
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
            "Patient trend-following swing trades on the S&P 500, holding "
            "winners across multiple sessions."
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
            "Breakout entries around London and New York session opens on "
            "major FX pairs."
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
    help = "Seed master traders for the copy-trading app (idempotent)."

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        for data in MASTER_TRADERS:
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

            # Seed a sample trade log once (only if this master has no trades).
            if not obj.trades.exists():
                now = timezone.now()
                for cur, sym, amt, direction, result, status, verified, days_ago in SAMPLE_TRADES:
                    MasterTrade.objects.create(
                        master=obj, crypto_currency=cur, crypto_symbol=sym,
                        amount=amt, direction=direction, result=result,
                        status=status, is_verified=verified,
                        opened_at=now - timedelta(days=days_ago, hours=obj.order),
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded master traders: {created_count} created, "
                f"{updated_count} updated."
            )
        )
