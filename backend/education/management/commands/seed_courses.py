from django.core.management.base import BaseCommand

from education.models import Course, Lesson, Module

# Public YouTube embed used as a harmless placeholder video for every lesson.
PLACEHOLDER_VIDEO = 'https://www.youtube.com/embed/p7HKvqRI_Bo'

LOREM = (
    'In this lesson we walk through the concept using Summit Teachable account '
    'tools. Follow the chart context, review the mechanics, then apply the '
    'workflow from your dashboard.'
)

# Each course: slug, title, thumbnail_slug, level, short_description, duration,
# and a list of modules; each module is (title, [lesson_title, ...]).
COURSES = [
    {
        'slug': 'stock-money-glitch',
        'title': 'Stock Market Money Glitch',
        'thumbnail_slug': 'course-stock-glitch',
        'level': 'beginner',
        'short_description': 'Spot repeatable, high-probability setups in the stock market.',
        'duration_label': '4h 15m',
        'modules': [
            ('Reading the Tape', [
                'What the "glitch" really is',
                'Order flow basics',
                'Spotting imbalance on the chart',
            ]),
            ('Building the Setup', [
                'Defining your entry trigger',
                'Stop placement on an account',
                'Sizing a position',
            ]),
            ('Putting It Together', [
                'Walking through a live example',
                'Reviewing the result',
            ]),
        ],
    },
    {
        'slug': 'million-beginners-guide',
        'title': "$1 Million: Ultimate Beginner's Guide to Trading",
        'thumbnail_slug': 'course-million',
        'level': 'beginner',
        'short_description': 'A from-scratch roadmap for the brand-new trader.',
        'duration_label': '6h 30m',
        'modules': [
            ('Foundations', [
                'How markets actually work',
                'Brokers, orders and the account wallet',
                'Your first trade workflow',
            ]),
            ('Strategy 101', [
                'Trend vs range',
                'Support and resistance',
                'Building a simple plan',
            ]),
            ('Scaling Up Safely', [
                'Compounding an account',
                'Tracking your performance',
                'Avoiding beginner traps',
            ]),
        ],
    },
    {
        'slug': 'futures-trading',
        'title': 'Futures Trading',
        'thumbnail_slug': 'course-futures',
        'level': 'intermediate',
        'short_description': 'Leverage, contracts and margin — explained with practical examples.',
        'duration_label': '5h 45m',
        'modules': [
            ('Futures Fundamentals', [
                'Contracts, ticks and multipliers',
                'Margin and leverage',
                'Rollover and expiry',
            ]),
            ('Intraday Execution', [
                'Scalping the open',
                'Managing a runner',
                'When to stand aside',
            ]),
        ],
    },
    {
        'slug': 'so-many-options',
        'title': 'So Many Options',
        'thumbnail_slug': 'course-options',
        'level': 'intermediate',
        'short_description': 'Calls, puts and spreads demystified for every strategy.',
        'duration_label': '7h 10m',
        'modules': [
            ('Options Basics', [
                'Calls and puts explained',
                'Strike, expiry and premium',
                'The greeks at a glance',
            ]),
            ('Core Strategies', [
                'Covered calls',
                'Vertical spreads',
                'Defined-risk plays',
            ]),
            ('Risk & Review', [
                'Sizing an options position',
                'Reviewing a trade',
            ]),
        ],
    },
    {
        'slug': 'crypto-stocks-university',
        'title': 'Crypto & Stocks University',
        'thumbnail_slug': 'course-csu',
        'level': 'beginner',
        'short_description': 'One curriculum, two asset classes on Summit Teachable.',
        'duration_label': '8h 00m',
        'modules': [
            ('Crypto Track', [
                'Wallets, exchanges and the BTC balance',
                'Reading a crypto chart',
                'Your first swap',
            ]),
            ('Stocks Track', [
                'Equities vs crypto',
                'Earnings and catalysts',
                'Reviewing a stock trade',
            ]),
            ('Bringing It Together', [
                'Building a mixed portfolio',
                'Rebalancing an account',
            ]),
        ],
    },
    {
        'slug': 'bear-market-money',
        'title': 'Bear Market Money',
        'thumbnail_slug': 'course-bear-market',
        'level': 'advanced',
        'short_description': 'Navigating down markets with hedges and shorts.',
        'duration_label': '6h 50m',
        'modules': [
            ('Shorting the Market', [
                'How shorting works',
                'Borrow, margin and risk',
                'Timing the breakdown',
            ]),
            ('Hedging Playbook', [
                'Protective puts',
                'Inverse instruments',
                'Managing drawdown',
            ]),
        ],
    },
    {
        'slug': 'trading-psychology',
        'title': 'Trading Psychology & Risk Management',
        'thumbnail_slug': 'course-psychology',
        'level': 'intermediate',
        'short_description': 'Master the mental game and protect your capital.',
        'duration_label': '4h 40m',
        'modules': [
            ('The Mental Game', [
                'Fear, greed and the trading account',
                'Building discipline',
                'Journaling your trades',
            ]),
            ('Risk Management', [
                'Position sizing rules',
                'Defining max loss',
                'Surviving a losing streak',
            ]),
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed the academy with courses, modules and lessons (idempotent).'

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
                        f"{data['short_description']} This Summit Teachable course "
                        f"helps learners study each concept with practical examples."
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
