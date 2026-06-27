from decimal import Decimal

from django.db import models

from accounts.models import User


class TradingAccount(models.Model):
    """Per-user SIMULATED trading account.

    Everything here is paper-trading / demo data. Admins set the win/draw/loss
    stats manually from the admin so the dashboard can showcase a demo track
    record — no live broker is connected (that is a "coming soon" stub).
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='trading_account')

    # Simulated balances (play money)
    trading_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'),
                                          help_text="Simulated trading balance (demo funds)")
    equity = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'),
                                 help_text="Simulated equity (demo funds)")

    # Manually-set demo statistics
    total_trades = models.IntegerField(default=0)
    trades_won = models.IntegerField(default=0)
    trades_drawn = models.IntegerField(default=0)
    trades_lost = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Trading Account'
        verbose_name_plural = 'Trading Accounts'

    def __str__(self):
        return f"{self.user.username} - Demo Trading Account"

    @property
    def win_rate(self):
        """Percentage of trades won (simulated)."""
        if not self.total_trades:
            return Decimal('0.00')
        return (Decimal(self.trades_won) / Decimal(self.total_trades) * 100).quantize(Decimal('0.01'))
