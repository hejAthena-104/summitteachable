from django.contrib import admin

from .models import AnalysisPost


@admin.register(AnalysisPost)
class AnalysisPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'symbol', 'bias', 'status', 'is_house', 'created_at')
    list_filter = ('status', 'market', 'bias', 'is_house')
    search_fields = ('title', 'symbol', 'body', 'author__username', 'author__email')
    actions = ('approve_posts', 'reject_posts')

    @admin.action(description='Approve selected posts (publish)')
    def approve_posts(self, request, queryset):
        updated = queryset.update(status='published')
        self.message_user(request, f'{updated} post(s) published.')

    @admin.action(description='Reject selected posts')
    def reject_posts(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} post(s) rejected.')
