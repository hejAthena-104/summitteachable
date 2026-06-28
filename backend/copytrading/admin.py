from django.contrib import admin
from django.utils.html import format_html, format_html_join

from .models import CopyRelationship, MasterTrader, MasterTrade


class MasterTradeInline(admin.TabularInline):
    """Manage a trader's trades inline on the trader page."""
    model = MasterTrade
    extra = 1
    fields = ("crypto_currency", "crypto_symbol", "amount", "direction",
              "result", "status", "is_verified", "opened_at")
    ordering = ("-opened_at",)


@admin.register(MasterTrader)
class MasterTraderAdmin(admin.ModelAdmin):
    list_display = (
        "name", "headline", "win_rate", "return_pct", "followers",
        "risk_level", "is_active", "order",
    )
    list_editable = ("win_rate", "return_pct", "followers", "is_active", "order")
    list_filter = ("risk_level", "is_active")
    search_fields = ("name", "headline", "markets")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order", "name")
    inlines = [MasterTradeInline]


@admin.register(MasterTrade)
class MasterTradeAdmin(admin.ModelAdmin):
    """Review, edit and verify every trade before copiers act on it."""
    list_display = (
        "id", "master", "crypto_currency", "crypto_symbol", "amount",
        "direction", "result", "status", "is_verified", "opened_at",
    )
    list_editable = ("result", "status", "is_verified")
    list_filter = ("is_verified", "result", "status", "direction", "master")
    search_fields = ("master__name", "crypto_currency", "crypto_symbol")
    autocomplete_fields = ("master",)
    ordering = ("-opened_at",)
    actions = ("verify_trades", "unverify_trades")

    @admin.action(description="Verify selected trades")
    def verify_trades(self, request, queryset):
        n = queryset.update(is_verified=True)
        self.message_user(request, f"{n} trade(s) verified.")

    @admin.action(description="Mark selected trades unverified")
    def unverify_trades(self, request, queryset):
        n = queryset.update(is_verified=False)
        self.message_user(request, f"{n} trade(s) marked unverified.")


@admin.register(CopyRelationship)
class CopyRelationshipAdmin(admin.ModelAdmin):
    list_display = (
        "user", "master", "allocated_demo_amount", "is_active",
        "created_at", "stopped_at",
    )
    list_filter = ("is_active", "master")
    search_fields = ("user__username", "user__email", "master__name")
    autocomplete_fields = ("master",)
    readonly_fields = ("created_at", "copied_trades")

    @admin.display(description="Trades this user is copying")
    def copied_trades(self, obj):
        """Show the master's trades so an admin can check they meet standards."""
        trades = list(obj.master.trades.all()[:25])
        if not trades:
            return "No trades logged for this trader yet."
        header = format_html(
            '<tr style="text-align:left;border-bottom:1px solid #ccc;">'
            '<th style="padding:4px 10px;">Symbol</th><th style="padding:4px 10px;">Dir</th>'
            '<th style="padding:4px 10px;">Amount</th><th style="padding:4px 10px;">Result</th>'
            '<th style="padding:4px 10px;">Status</th><th style="padding:4px 10px;">Verified</th>'
            '<th style="padding:4px 10px;">Date</th></tr>'
        )
        rows = format_html_join(
            "",
            '<tr style="border-bottom:1px solid #eee;">'
            '<td style="padding:4px 10px;">{}</td><td style="padding:4px 10px;">{}</td>'
            '<td style="padding:4px 10px;">${}</td><td style="padding:4px 10px;">{}</td>'
            '<td style="padding:4px 10px;">{}</td><td style="padding:4px 10px;">{}</td>'
            '<td style="padding:4px 10px;">{}</td></tr>',
            (
                (t.crypto_symbol, t.get_direction_display(), t.amount,
                 t.get_result_display(), t.get_status_display(),
                 "Yes" if t.is_verified else "Pending",
                 t.opened_at.strftime("%Y-%m-%d %H:%M"))
                for t in trades
            ),
        )
        return format_html('<table style="border-collapse:collapse;">{}{}</table>', header, rows)
