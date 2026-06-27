from django.core.management.base import BaseCommand

from education.models import Course, Lesson, Module

# Public YouTube embed used as a harmless placeholder video for every lesson.
PLACEHOLDER_VIDEO = 'https://www.youtube.com/embed/p7HKvqRI_Bo'

LOREM = (
    'In this demo lesson we walk through the concept using the Summit Teachable '
    'paper account. Nothing here involves real money — every figure is simulated '
    'so you can practice the mechanics risk-free. Follow along, then try it in '
    'your demo wallet.'
)

# Each course: slug, title, thumbnail_slug, level, short_description, duration,
# and a list of modules; each module is (title, [lesson_title, ...]).
COURSES = [
    {
        'slug': 'stock-money-glitch',
        'title': 'Stock Market Money Glitch',
        'thumbnail_slug': 'course-stock-glitch',
        'level': 'beginner',
        'short_description': 'Spot repeatable, high-probability setups in the stock market — demo only.',
        'duration_label': '4h 15m',
        'modules': [
            ('Reading the Tape', [
                'What the "glitch" really is',
                'Order flow basics',
                'Spotting imbalance on the chart',
            ]),
            ('Building the Setup', [
                'Defining your entry trigger',
                'Stop placement on a demo account',
                'Sizing the play money',
            ]),
            ('Putting It Together', [
                'Paper-trading a live example',
                'Reviewing the result',
            ]),
        ],
    },
    {
        'slug': 'million-beginners-guide',
        'title': "$1 Million: Ultimate Beginner's Guide to Trading",
        'thumbnail_slug': 'course-million',
        'level': 'beginner',
        'short_description': 'A from-scratch roadmap for the brand-new trader, taught on a paper account.',
        'duration_label': '6h 30m',
        'modules': [
            ('Foundations', [
                'How markets actually work',
                'Brokers, orders and the demo wallet',
                'Your first simulated trade',
            ]),
            ('Strategy 101', [
                'Trend vs range',
                'Support and resistance',
                'Building a simple plan',
            ]),
            ('Scaling Up Safely', [
                'Compounding play money',
                'Tracking your demo performance',
                'Avoiding beginner traps',
            ]),
        ],
    },
    {
        'slug': 'futures-trading',
        'title': 'Futures Trading',
        'thumbnail_slug': 'course-futures',
        'level': 'intermediate',
        'short_description': 'Leverage, contracts and margin — explained and practiced risk-free.',
        'duration_label': '5h 45m',
        'modules': [
            ('Futures Fundamentals', [
                'Contracts, ticks and multipliers',
                'Margin and leverage on a demo',
                'Rollover and expiry',
            ]),
            ('Intraday Execution', [
                'Scalping the open',
                'Managing a simulated runner',
                'When to stand aside',
            ]),
        ],
    },
    {
        'slug': 'so-many-options',
        'title': 'So Many Options',
        'thumbnail_slug': 'course-options',
        'level': 'intermediate',
        'short_description': 'Calls, puts and spreads demystified — paper-trade every strategy.',
        'duration_label': '7h 10m',
        'modules': [
            ('Options Basics', [
                'Calls and puts explained',
                'Strike, expiry and premium',
                'The greeks at a glance',
            ]),
            ('Core Strategies', [
                'Covered calls on a demo',
                'Vertical spreads',
                'Defined-risk plays',
            ]),
            ('Risk & Review', [
                'Sizing an options position',
                'Reviewing a simulated trade',
            ]),
        ],
    },
    {
        'slug': 'crypto-stocks-university',
        'title': 'Crypto & Stocks University',
        'thumbnail_slug': 'course-csu',
        'level': 'beginner',
        'short_description': 'One curriculum, two asset classes — all on the Summit demo platform.',
        'duration_label': '8h 00m',
        'modules': [
            ('Crypto Track', [
                'Wallets, exchanges and the demo BTC balance',
                'Reading a crypto chart',
                'Your first simulated swap',
            ]),
            ('Stocks Track', [
                'Equities vs crypto',
                'Earnings and catalysts',
                'Paper-trading a stock',
            ]),
            ('Bringing It Together', [
                'Building a mixed demo portfolio',
                'Rebalancing play money',
            ]),
        ],
    },
    {
        'slug': 'bear-market-money',
        'title': 'Bear Market Money',
        'thumbnail_slug': 'course-bear-market',
        'level': 'advanced',
        'short_description': 'Profiting in down markets with hedges and shorts — demo execution.',
        'duration_label': '6h 50m',
        'modules': [
            ('Shorting the Market', [
                'How shorting works on a demo',
                'Borrow, margin and risk',
                'Timing the breakdown',
            ]),
            ('Hedging Playbook', [
                'Protective puts',
                'Inverse instruments',
                'Managing drawdown on play money',
            ]),
        ],
    },
    {
        'slug': 'trading-psychology',
        'title': 'Trading Psychology & Risk Management',
        'thumbnail_slug': 'course-psychology',
        'level': 'intermediate',
        'short_description': 'Master the mental game and protect your (demo) capital.',
        'duration_label': '4h 40m',
        'modules': [
            ('The Mental Game', [
                'Fear, greed and the demo account',
                'Building discipline',
                'Journaling your simulated trades',
            ]),
            ('Risk Management', [
                'Position sizing rules',
                'Defining max loss',
                'Surviving a losing streak on paper',
            ]),
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed the academy with demo courses, modules and lessons (idempotent).'

    def handle(self, *args, **options):
        created_courses = 0
        for c_order, data in enumerate(COURSES, start=1):
            course, created = Course.objects.get_or_create(
                slug=data['slug'],
                defaults={
                    'title': data['title'],
                    'thumbnail_slug': data['thumbnail_slug'],
                    'level': data['level'],
                    'short_description': data['short_description'],
                    'description': (
                        f"{data['short_description']} This is a simulated, demo-only "
                        f"course on Summit Teachable — practice every concept with play "
                        f"money, no real funds at risk."
                    ),
                    'duration_label': data['duration_label'],
                    'instructor': 'Summit Teachable',
                    'price': 1000,
                    'order': c_order,
                    'is_published': True,
                },
            )
            if created:
                created_courses += 1

            for m_order, (m_title, lessons) in enumerate(data['modules'], start=1):
                module, _ = Module.objects.get_or_create(
                    course=course,
                    title=m_title,
                    defaults={'order': m_order},
                )
                for l_order, l_title in enumerate(lessons, start=1):
                    Lesson.objects.get_or_create(
                        module=module,
                        title=l_title,
                        defaults={
                            'video_url': PLACEHOLDER_VIDEO,
                            'content': LOREM,
                            'duration_label': f'{8 + l_order * 3}m',
                            'order': l_order,
                            # First lesson of the first module is a free preview.
                            'is_preview': (m_order == 1 and l_order == 1),
                        },
                    )

        self.stdout.write(self.style.SUCCESS(
            f'Seeded academy: {Course.objects.count()} courses total '
            f'({created_courses} newly created).'
        ))
