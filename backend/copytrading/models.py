from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class MasterTrader(models.Model):
    """A master trader users can copy."""

    RISK_LOW = "low"
    RISK_MEDIUM = "medium"
    RISK_HIGH = "high"
    RISK_CHOICES = [
        (RISK_LOW, "Low"),
        (RISK_MEDIUM, "Medium"),
        (RISK_HIGH, "High"),
    ]

    # Emerald-family accents used to tint the initials avatar in templates.
    ACCENT_EMERALD = "emerald"
    ACCENT_TEAL = "teal"
    ACCENT_BLUE = "blue"
    ACCENT_VIOLET = "violet"
    ACCENT_AMBER = "amber"
    ACCENT_CHOICES = [
        (ACCENT_EMERALD, "Emerald"),
        (ACCENT_TEAL, "Teal"),
        (ACCENT_BLUE, "Blue"),
        (ACCENT_VIOLET, "Violet"),
        (ACCENT_AMBER, "Amber"),
    ]

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    headline = models.CharField(
        max_length=160,
        help_text='Short tagline, e.g. "Swing trader · FX & indices".',
    )
    strategy = models.TextField(
        help_text="Description of the trader's approach.",
    )
    win_rate = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0,
        help_text="Win rate %, e.g. 68.5.",
    )
    return_pct = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        default=0,
        help_text="30-day return %, e.g. 14.2.",
    )
    followers = models.PositiveIntegerField(
        default=0,
        help_text="Follower count.",
    )
    risk_level = models.CharField(
        max_length=10,
        choices=RISK_CHOICES,
        default=RISK_MEDIUM,
    )
    markets = models.CharField(
        max_length=120,
        help_text='Markets traded, e.g. "Forex, Indices".',
    )
    accent = models.CharField(
        max_length=10,
        choices=ACCENT_CHOICES,
        default=ACCENT_EMERALD,
        help_text="Avatar accent colour for the initials circle.",
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Master Trader"
        verbose_name_plural = "Master Traders"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def initials(self):
        parts = [p for p in self.name.split() if p]
        if not parts:
            return "?"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()

    @property
    def risk_badge_class(self):
        return {
            self.RISK_LOW: "bg-success-subtle text-success",
            self.RISK_MEDIUM: "bg-warning-subtle text-warning",
            self.RISK_HIGH: "bg-danger-subtle text-danger",
        }.get(self.risk_level, "bg-secondary-subtle text-secondary")


class CopyRelationship(models.Model):
    """Records that a user is copying a master trader."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="copies",
    )
    master = models.ForeignKey(
        MasterTrader,
        on_delete=models.CASCADE,
        related_name="relationships",
    )
    allocated_demo_amount = models.DecimalField(
        "Allocation",
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Allocation amount.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    stopped_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Copy Relationship"
        verbose_name_plural = "Copy Relationships"
        constraints = [
            # One active copy per (user, master). Stopped ones may repeat.
            models.UniqueConstraint(
                fields=["user", "master"],
                condition=models.Q(is_active=True),
                name="unique_active_copy_per_user_master",
            )
        ]

    def __str__(self):
        return f"{self.user} → {self.master}"

    def stop(self):
        self.is_active = False
        self.stopped_at = timezone.now()
        self.save(update_fields=["is_active", "stopped_at"])


class MasterTrade(models.Model):
    """An individual trade taken by a master trader.

    Copiers see these on their Trading (Contracts Log) page for any master they
    are actively copying. An admin reviews/verifies each trade before it counts;
    unverified trades still show, badged "Pending review"."""

    DIRECTION_CHOICES = [("rise", "Rise"), ("fall", "Fall")]
    RESULT_CHOICES = [
        ("pending", "Pending"), ("win", "Win"), ("loss", "Loss"), ("draw", "Draw"),
    ]
    STATUS_CHOICES = [
        ("open", "Open"), ("closed", "Closed"), ("cancelled", "Cancelled"),
    ]

    master = models.ForeignKey(
        MasterTrader, on_delete=models.CASCADE, related_name="trades"
    )
    crypto_currency = models.CharField(max_length=120, help_text="e.g. Bitcoin")
    crypto_symbol = models.CharField(max_length=40, help_text="e.g. BTC/USD")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    direction = models.CharField(max_length=4, choices=DIRECTION_CHOICES, default="rise")
    result = models.CharField(max_length=8, choices=RESULT_CHOICES, default="pending")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="open")
    is_verified = models.BooleanField(
        default=False,
        help_text="Verified by an admin — the trade has been checked and meets standards.",
    )
    notes = models.CharField(max_length=255, blank=True)
    opened_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Trade"
        verbose_name_plural = "Trades"
        ordering = ["-opened_at"]

    def __str__(self):
        return f"{self.master.name} · {self.crypto_symbol} {self.get_direction_display()}"

    @property
    def result_badge_class(self):
        return {
            "win": "bg-success", "loss": "bg-danger",
            "draw": "bg-secondary", "pending": "bg-warning",
        }.get(self.result, "bg-secondary")

    @property
    def status_badge_class(self):
        return {
            "open": "bg-info", "closed": "bg-success", "cancelled": "bg-secondary",
        }.get(self.status, "bg-secondary")
