from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class MasterTrader(models.Model):
    """
    A demo/illustrative "master trader" users can copy on their DEMO account.

    HARD CONSTRAINT: these are SIMULATED traders for practice only. All stats
    (win_rate, return_pct, followers) are demo/illustrative figures. No real
    person's real money or real performance is represented here.
    """

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
        help_text="Demo description of the trader's approach.",
    )
    win_rate = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0,
        help_text="Demo win rate %, e.g. 68.5.",
    )
    return_pct = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        default=0,
        help_text="Demo 30-day return %, e.g. 14.2.",
    )
    followers = models.PositiveIntegerField(
        default=0,
        help_text="Demo follower count (illustrative).",
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
        verbose_name = "Master Trader (Demo)"
        verbose_name_plural = "Master Traders (Demo)"

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
    """
    Records that a user is copying a master trader on their DEMO account.

    HARD CONSTRAINT: allocated_demo_amount is a SIMULATED allocation only. No
    real balance is ever moved when a relationship is created or stopped.
    """

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
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Simulated demo allocation. Not a real balance transfer.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    stopped_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Copy Relationship (Demo)"
        verbose_name_plural = "Copy Relationships (Demo)"
        constraints = [
            # One active copy per (user, master). Stopped ones may repeat.
            models.UniqueConstraint(
                fields=["user", "master"],
                condition=models.Q(is_active=True),
                name="unique_active_copy_per_user_master",
            )
        ]

    def __str__(self):
        return f"{self.user} → {self.master} (demo)"

    def stop(self):
        self.is_active = False
        self.stopped_at = timezone.now()
        self.save(update_fields=["is_active", "stopped_at"])
