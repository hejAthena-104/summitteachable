from django.contrib import admin

from .models import CopyRelationship, MasterTrader


@admin.register(MasterTrader)
class MasterTraderAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "headline",
        "win_rate",
        "return_pct",
        "followers",
        "risk_level",
        "is_active",
        "order",
    )
    list_editable = (
        "win_rate",
        "return_pct",
        "followers",
        "is_active",
        "order",
    )
    list_filter = ("risk_level", "is_active")
    search_fields = ("name", "headline", "markets")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order", "name")


@admin.register(CopyRelationship)
class CopyRelationshipAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "master",
        "allocated_demo_amount",
        "is_active",
        "created_at",
        "stopped_at",
    )
    list_filter = ("is_active", "master")
    search_fields = ("user__username", "user__email", "master__name")
    autocomplete_fields = ("master",)
    readonly_fields = ("created_at",)
