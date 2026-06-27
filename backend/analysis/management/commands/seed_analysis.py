from django.core.management.base import BaseCommand

from analysis.models import AnalysisPost


# House "market bias & flow" notes.
HOUSE_POSTS = [
    {
        'title': 'EURUSD — Bullish continuation above 1.0850',
        'symbol': 'EURUSD',
        'market': 'forex',
        'bias': 'bullish',
        'timeframe': '4H',
        'tv_symbol': 'FX:EURUSD',
        'body': (
            'Educational flow note: price is holding above the 1.0850 area with higher '
            'lows on the 4H. As a learning exercise, observe how a bullish bias often '
            'looks for pullbacks into prior support rather than chasing extension. '
            'Use this as chart context while reviewing pullbacks into prior support.'
        ),
    },
    {
        'title': 'BTCUSD — Neutral, range-bound',
        'symbol': 'BTCUSD',
        'market': 'crypto',
        'bias': 'neutral',
        'timeframe': '1D',
        'tv_symbol': 'BINANCE:BTCUSDT',
        'body': (
            'Educational flow note: BTC is compressing between range support and '
            'resistance with no clear directional commitment. Use this as a study of '
            'how a neutral bias favours patience and reacting to a confirmed breakout '
            'rather than predicting one.'
        ),
    },
    {
        'title': 'S&P 500 — Risk-on bias into earnings',
        'symbol': 'SPX500',
        'market': 'indices',
        'bias': 'bullish',
        'timeframe': '1D',
        'tv_symbol': 'SP:SPX',
        'body': (
            'Educational flow note: broad index breadth has improved into the earnings '
            'window, a textbook risk-on backdrop. Notice how index strength often '
            'correlates with appetite for higher-beta names. Provided for learning on '
            'the platform.'
        ),
    },
    {
        'title': 'GBPJPY — Bearish rejection at range highs',
        'symbol': 'GBPJPY',
        'market': 'forex',
        'bias': 'bearish',
        'timeframe': '4H',
        'tv_symbol': 'FX:GBPJPY',
        'body': (
            'Educational flow note: repeated wicks into the range high suggest sellers '
            'defending the level. A bearish study here would watch for a lower-high and '
            'a break of intraday structure.'
        ),
    },
    {
        'title': 'AAPL — Neutral ahead of the print',
        'symbol': 'AAPL',
        'market': 'stocks',
        'bias': 'neutral',
        'timeframe': '1D',
        'tv_symbol': 'NASDAQ:AAPL',
        'body': (
            'Educational flow note: price is coiling near the 50-day average with mixed '
            'momentum into the report. A neutral stance is a good lesson in sizing down '
            'and waiting for the event to resolve.'
        ),
    },
    {
        'title': 'XAUUSD (Gold) — Bullish flow on safe-haven demand',
        'symbol': 'XAUUSD',
        'market': 'commodities',
        'bias': 'bullish',
        'timeframe': '1D',
        'tv_symbol': 'OANDA:XAUUSD',
        'body': (
            'Educational flow note: gold is grinding higher with steady demand on '
            'pullbacks. Use it to study how a trend can persist while staying above a '
            'rising moving average.'
        ),
    },
]


class Command(BaseCommand):
    help = 'Seed idempotent house market-analysis posts (educational, not advice).'

    def handle(self, *args, **options):
        created = 0
        for data in HOUSE_POSTS:
            _, was_created = AnalysisPost.objects.get_or_create(
                title=data['title'],
                is_house=True,
                defaults={
                    'author': None,
                    'symbol': data['symbol'],
                    'market': data['market'],
                    'bias': data['bias'],
                    'timeframe': data['timeframe'],
                    'tv_symbol': data['tv_symbol'],
                    'body': data['body'],
                    'status': 'published',
                },
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Seeded analysis: {created} created, '
            f'{len(HOUSE_POSTS) - created} already present.'
        ))
