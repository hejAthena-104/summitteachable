from django.contrib import admin
from django.utils.html import format_html

from accounts.email_utils import EmailService

from .models import CoursePurchase


@admin.register(CoursePurchase)
class CoursePurchaseAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'buyer_email', 'course', 'amount', 'payment_method',
        'has_proof', 'status', 'created_at',
    )
    list_filter = ('status', 'payment_method', 'course', 'created_at')
    search_fields = ('buyer_email', 'buyer_name', 'tx_reference', 'user__username')
    readonly_fields = ('proof_preview', 'created_at', 'processed_at')
    actions = ['approve_purchases', 'decline_purchases']

    def has_proof(self, obj):
        return '✓ Yes' if obj.proof_image else '✗ No'
    has_proof.short_description = 'Proof'

    def proof_preview(self, obj):
        if obj.proof_image:
            return format_html('<img src="{}" style="max-width:480px;max-height:480px;" />', obj.proof_image.url)
        return 'No proof uploaded'
    proof_preview.short_description = 'Payment proof'

    def approve_purchases(self, request, queryset):
        n = 0
        for p in queryset:
            if p.status != 'approved' and p.approve():
                EmailService.send_course_purchase_approved_email(p)
                n += 1
        self.message_user(request, f'{n} purchase(s) approved — course access granted (no balance touched).')
    approve_purchases.short_description = 'Approve selected — grant course access'

    def decline_purchases(self, request, queryset):
        n = 0
        for p in queryset.exclude(status='declined'):
            p.decline('Declined by admin')
            n += 1
        self.message_user(request, f'{n} purchase(s) declined.')
    decline_purchases.short_description = 'Decline selected'
