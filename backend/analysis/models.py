from django.conf import settings
from django.db import models


class AnalysisPost(models.Model):
    """An educational market-analysis note.

    Posts authored by the house team (author=None, is_house=True) are seeded
    "market bias & flow" notes. Member submissions default to status='pending'
    and are surfaced through the admin moderation actions before publishing.
    """

    MARKET_CHOICES = [
        ('forex', 'Forex'),
        ('crypto', 'Crypto'),
        ('stocks', 'Stocks'),
        ('indices', 'Indices'),
        ('commodities', 'Commodities'),
    ]

    BIAS_CHOICES = [
        ('bullish', 'Bullish'),
        ('bearish', 'Bearish'),
        ('neutral', 'Neutral'),
    ]

    STATUS_CHOICES = [
        ('published', 'Published'),
        ('pending', 'Pending review'),
        ('rejected', 'Rejected'),
    ]

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='analysis_posts',
        help_text='Null means an admin/house post.',
    )
    title = models.CharField(max_length=200)
    symbol = models.CharField(max_length=20, help_text='e.g. EURUSD, BTCUSD, AAPL')
    market = models.CharField(max_length=20, choices=MARKET_CHOICES, default='forex')
    bias = models.CharField(max_length=10, choices=BIAS_CHOICES, default='neutral')
    timeframe = models.CharField(max_length=20, help_text='e.g. 4H, 1D')
    body = models.TextField()
    tv_symbol = models.CharField(
        max_length=50,
        blank=True,
        help_text='TradingView symbol for the mini widget, e.g. FX:EURUSD',
    )
    chart_image = models.ImageField(upload_to='analysis/', blank=True, null=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')
    is_house = models.BooleanField(
        default=False,
        help_text='Admin/seeded "market biases & flow" content.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.get_bias_display()})'

    @property
    def bias_color(self):
        """Hex color used for bias-coded cards in the templates."""
        return {
            'bullish': '#10B981',
            'bearish': '#EF4444',
            'neutral': '#F59E0B',
        }.get(self.bias, '#F59E0B')
