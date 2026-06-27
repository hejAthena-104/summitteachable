from django.contrib import admin

from .models import TradingAccount


@admin.register(TradingAccount)
class TradingAccountAdmin(admin.ModelAdmin):
    """Admins manually set the SIMULATED demo trading stats per user."""

    list_display = (
        'user', 'trading_balance', 'equity',
        'total_trades', 'trades_won', 'trades_drawn', 'trades_lost',
        'win_rate', 'updated_at',
    )
    list_editable = (
        'trading_balance', 'equity',
        'total_trades', 'trades_won', 'trades_drawn', 'trades_lost',
    )
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('win_rate', 'created_at', 'updated_at')
    fields = (
        'user', 'trading_balance', 'equity',
        'total_trades', 'trades_won', 'trades_drawn', 'trades_lost',
        'win_rate', 'created_at', 'updated_at',
    )

    @admin.display(description='Win Rate')
    def win_rate(self, obj):
        return f"{obj.win_rate}%"
