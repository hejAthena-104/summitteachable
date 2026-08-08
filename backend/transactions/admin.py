from django.contrib import admin, messages
from django.utils.html import format_html
from accounts.email_utils import EmailService
from .models import Transaction, Deposit, Withdrawal, Transfer


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin interface for Transactions"""
    list_display = (
        'id',
        'user',
        'type',
        'amount',
        'status_badge',
        'payment_method',
        'created_at',
        'processed_at'
    )
    list_filter = ('type', 'status', 'payment_method', 'created_at', 'processed_at')
    search_fields = (
        'user__username',
        'user__email',
        'payment_reference',
        'description'
    )
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 50

    def status_badge(self, obj):
        """Display colored status badge"""
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'approved': 'green',
            'rejected': 'red',
            'cancelled': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.status.upper()
        )

    status_badge.short_description = 'Status'

    fieldsets = (
        ('Transaction Details', {
            'fields': ('user', 'type', 'amount', 'status')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_reference', 'payment_address')
        }),
        ('Additional Information', {
            'fields': ('description', 'admin_note', 'recipient')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'processed_at')
        }),
    )

    actions = ['approve_transactions', 'reject_transactions']

    def approve_transactions(self, request, queryset):
        """Bulk approve transactions"""
        approved_count = 0
        for transaction in queryset.filter(status='pending'):
            if transaction.approve():
                approved_count += 1
        self.message_user(request, f'{approved_count} transaction(s) approved successfully.')

    approve_transactions.short_description = 'Approve selected transactions'

    def reject_transactions(self, request, queryset):
        """Bulk reject transactions"""
        rejected_count = 0
        for transaction in queryset.filter(status='pending'):
            transaction.reject()
            rejected_count += 1
        self.message_user(request, f'{rejected_count} transaction(s) rejected.')

    reject_transactions.short_description = 'Reject selected transactions'


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    """Admin interface for Deposits"""
    list_display = (
        'transaction',
        'get_user',
        'get_amount',
        'get_status',
        'get_payment_method',
        'has_proof',
        'get_created_at'
    )
    list_filter = (
        'transaction__status',
        'transaction__payment_method',
        'transaction__created_at'
    )
    search_fields = (
        'transaction__user__username',
        'transaction__user__email',
        'transaction__payment_reference'
    )
    readonly_fields = ('proof_preview',)

    fieldsets = (
        ('Transaction Info', {
            'fields': ('transaction',)
        }),
        ('Payment Proof', {
            'fields': ('proof_image', 'proof_preview')
        }),
    )

    actions = ['approve_deposits', 'reject_deposits']

    def proof_preview(self, obj):
        """Display proof image preview"""
        if obj.proof_image:
            return format_html(
                '<img src="{}" style="max-width: 500px; max-height: 500px;" />',
                obj.proof_image.url
            )
        return 'No proof uploaded'
    proof_preview.short_description = 'Payment Proof Preview'

    def has_proof(self, obj):
        """Check if proof is uploaded"""
        if obj.proof_image:
            return '✓ Yes'
        return '✗ No'
    has_proof.short_description = 'Proof Uploaded'

    def approve_deposits(self, request, queryset):
        """Approve selected deposits"""
        count = 0
        for deposit in queryset:
            if deposit.transaction.status == 'pending':
                deposit.transaction.approve()
                count += 1
        self.message_user(request, f'{count} deposit(s) approved successfully.')
    approve_deposits.short_description = 'Approve selected deposits'

    def reject_deposits(self, request, queryset):
        """Reject selected deposits"""
        count = 0
        for deposit in queryset:
            if deposit.transaction.status == 'pending':
                deposit.transaction.reject(reason='Rejected by admin')
                count += 1
        self.message_user(request, f'{count} deposit(s) rejected.')
    reject_deposits.short_description = 'Reject selected deposits'

    def get_user(self, obj):
        return obj.transaction.user.username
    get_user.short_description = 'User'
    get_user.admin_order_field = 'transaction__user__username'

    def get_amount(self, obj):
        return f"${obj.transaction.amount}"
    get_amount.short_description = 'Amount'
    get_amount.admin_order_field = 'transaction__amount'

    def get_status(self, obj):
        return obj.transaction.status
    get_status.short_description = 'Status'
    get_status.admin_order_field = 'transaction__status'

    def get_payment_method(self, obj):
        return obj.transaction.payment_method
    get_payment_method.short_description = 'Payment Method'

    def get_created_at(self, obj):
        return obj.transaction.created_at
    get_created_at.short_description = 'Created'
    get_created_at.admin_order_field = 'transaction__created_at'


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    """Admin interface for Withdrawals"""
    list_display = (
        'transaction',
        'get_user',
        'get_amount',
        'withdrawal_method',
        'get_status',
        'get_created_at'
    )
    list_filter = (
        'transaction__status',
        'withdrawal_method',
        'transaction__created_at'
    )
    search_fields = (
        'transaction__user__username',
        'transaction__user__email',
        'withdrawal_address'
    )

    def get_user(self, obj):
        return obj.transaction.user.username
    get_user.short_description = 'User'
    get_user.admin_order_field = 'transaction__user__username'

    def get_amount(self, obj):
        return f"${obj.transaction.amount}"
    get_amount.short_description = 'Amount'
    get_amount.admin_order_field = 'transaction__amount'

    def get_status(self, obj):
        return obj.transaction.status
    get_status.short_description = 'Status'
    get_status.admin_order_field = 'transaction__status'

    def get_created_at(self, obj):
        return obj.transaction.created_at
    get_created_at.short_description = 'Created'
    get_created_at.admin_order_field = 'transaction__created_at'


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    """Admin interface for Fund Transfers"""
    list_display = ('sender', 'recipient', 'amount', 'fee_amount', 'total_deducted', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('sender__username', 'sender__email', 'recipient__username', 'recipient__email')
    readonly_fields = ('total_deducted', 'created_at', 'completed_at')

    fieldsets = (
        ('Transfer Details', {
            'fields': ('sender', 'recipient', 'amount', 'description')
        }),
        ('Fees & Total', {
            'fields': ('fee_amount', 'total_deducted')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at')
        }),
    )

    actions = ['complete_transfers', 'cancel_transfers']

    def complete_transfers(self, request, queryset):
        """Bulk complete transfers"""
        completed_count = 0
        for transfer in queryset.filter(status='pending'):
            if transfer.complete():
                completed_count += 1
        self.message_user(request, f'{completed_count} transfer(s) completed successfully.')
    complete_transfers.short_description = 'Complete selected transfers'

    def cancel_transfers(self, request, queryset):
        """Bulk cancel transfers"""
        cancelled_count = 0
        for transfer in queryset.filter(status='pending'):
            if transfer.cancel():
                cancelled_count += 1
        self.message_user(request, f'{cancelled_count} transfer(s) cancelled.')
    cancel_transfers.short_description = 'Cancel selected transfers'


def _status_badge(status):
    colors = {'pending': 'orange', 'processing': 'blue', 'approved': 'green',
              'completed': 'green', 'active': 'green', 'rejected': 'red',
              'cancelled': 'gray', 'frozen': 'blue', 'blocked': 'red'}
    color = colors.get(status, 'gray')
    return format_html(
        '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
        color, str(status).upper())


from .models import (PaymentMethod, SwapRate, Swap, Beneficiary, ExternalTransfer,
                     SiteSetting, WithdrawalAccessCode)


@admin.register(WithdrawalAccessCode)
class WithdrawalAccessCodeAdmin(admin.ModelAdmin):
    """Issue long-lived withdrawal codes for clients who can't use the emailed OTP.

    Pick the user, save, and the code is generated for you. Copy it into your
    document, or use the 'Email this code to the user' action.
    """

    list_display = ('code_display', 'user', 'label', 'status_badge', 'uses_display',
                    'expires_display', 'created_by', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('code', 'label', 'user__username', 'user__email',
                     'user__first_name', 'user__last_name')
    autocomplete_fields = ('user',)
    readonly_fields = ('code_display', 'times_used', 'last_used_at', 'created_by', 'created_at')
    actions = ('email_code_to_user', 'revoke_codes', 'reactivate_codes')

    fieldsets = (
        ('Who it is for', {
            'fields': ('user', 'label'),
            'description': "Choose the account this code authorises withdrawals for. The label is "
                           "an internal note only — the user never sees it.",
        }),
        ('The code', {
            'fields': ('code_display',),
            'description': "Generated automatically when you save. Copy it into your document, or "
                           "select the row and run 'Email this code to the user'.",
        }),
        ('Validity', {
            'fields': ('is_active', 'expires_at', 'max_uses'),
            'description': "Leave 'Expires at' and 'Max uses' blank for a code that never expires "
                           "and works as often as needed. Untick 'Is active' to revoke it at once.",
        }),
        ('Usage', {'fields': ('times_used', 'last_used_at', 'created_by', 'created_at')}),
    )

    def get_fieldsets(self, request, obj=None):
        # No code exists yet on the add form — hide the placeholder box.
        if obj is None:
            return (
                ('Who it is for', {
                    'fields': ('user', 'label'),
                    'description': "Choose the account this code authorises withdrawals for. "
                                   "The code is generated when you save.",
                }),
                ('Validity', {
                    'fields': ('is_active', 'expires_at', 'max_uses'),
                    'description': "Leave 'Expires at' and 'Max uses' blank for a code that never "
                                   "expires and works as often as needed.",
                }),
            )
        return super().get_fieldsets(request, obj)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
        if not change:
            self.message_user(
                request,
                f'Access code {obj.code} issued for {obj.user.username}. '
                f'Copy it now — it is listed on this page whenever you need it again.',
                messages.SUCCESS,
            )

    @admin.display(description='Code', ordering='code')
    def code_display(self, obj):
        return format_html(
            '<code style="font-size:15px; font-weight:700; letter-spacing:1px; '
            'user-select:all;">{}</code>', obj.code or '—'
        )

    @admin.display(description='Status')
    def status_badge(self, obj):
        colours = {'Active': '#16a34a', 'Revoked': '#dc2626',
                   'Expired': '#b45309', 'Used up': '#6b7280'}
        status = obj.status
        return format_html('<b style="color:{}">{}</b>', colours.get(status, '#000'), status)

    @admin.display(description='Uses')
    def uses_display(self, obj):
        return f'{obj.times_used} / {obj.max_uses}' if obj.max_uses else f'{obj.times_used} / ∞'

    @admin.display(description='Expires', ordering='expires_at')
    def expires_display(self, obj):
        return obj.expires_at.strftime('%d %b %Y %H:%M') if obj.expires_at else 'Never'

    @admin.action(description='Email this code to the user')
    def email_code_to_user(self, request, queryset):
        sent = failed = 0
        for obj in queryset:
            try:
                ok = EmailService.send_withdrawal_access_code_email(obj)
            except Exception:
                ok = False
            if ok:
                sent += 1
            else:
                failed += 1
        if sent:
            self.message_user(request, f'{sent} code(s) emailed.', messages.SUCCESS)
        if failed:
            self.message_user(request, f'{failed} code(s) could not be emailed.', messages.ERROR)

    @admin.action(description='Revoke selected codes')
    def revoke_codes(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} code(s) revoked.', messages.SUCCESS)

    @admin.action(description='Reactivate selected codes')
    def reactivate_codes(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} code(s) reactivated.', messages.SUCCESS)


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    """Global site toggles (single row). Use 'Withdrawals enabled' to pause withdrawals."""
    list_display = ('__str__', 'withdrawals_enabled', 'request_code_enabled', 'updated_at')
    list_editable = ('withdrawals_enabled', 'request_code_enabled')
    readonly_fields = ('updated_at',)
    fieldsets = (
        ('Withdrawals', {
            'fields': ('withdrawals_enabled',),
            'description': "Turn this OFF to temporarily disable withdrawals (during maintenance or "
                           "processing issues). The 'Request code' and 'Complete Request' buttons are "
                           "hidden while it's off. Turn it back ON to restore them.",
        }),
        ('Security code', {
            'fields': ('request_code_enabled',),
            'description': "Controls only the 'Request code' button that emails a user a one-time "
                           "code. Turn it OFF to force every withdrawal through a Withdrawal Access "
                           "Code you issued from the admin. Withdrawals themselves stay open — "
                           "use 'Withdrawals enabled' above to close those.",
        }),
        ('Info', {'fields': ('updated_at',)}),
    )

    def has_add_permission(self, request):
        # Singleton — only allow the one row to exist.
        return not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'wallet_short', 'has_qr', 'has_icon', 'is_active', 'order')
    list_filter = ('type', 'is_active')
    search_fields = ('name', 'wallet_address')
    list_editable = ('is_active', 'order')
    fieldsets = (
        ('Method', {'fields': ('name', 'type', 'icon', 'is_active', 'order')}),
        ('Receiving wallet (shown to course buyers)', {
            'fields': ('wallet_address', 'qr_code'),
            'description': "Set the crypto wallet address that course payments are sent to. "
                           "A QR code is generated automatically from the address — uploading a "
                           "qr_code image here overrides the generated one.",
        }),
        ('Limits & fees', {'fields': ('min_amount', 'max_amount', 'charge_type', 'charge_amount', 'duration')}),
    )

    def wallet_short(self, obj):
        a = obj.wallet_address or ''
        return (a[:10] + '…' + a[-6:]) if len(a) > 18 else (a or '— not set —')
    wallet_short.short_description = 'Wallet address'

    def has_qr(self, obj):
        return '✓' if obj.qr_code else 'auto'
    has_qr.short_description = 'QR'

    def has_icon(self, obj):
        return '✓' if obj.icon else '—'
    has_icon.short_description = 'Logo'


@admin.register(SwapRate)
class SwapRateAdmin(admin.ModelAdmin):
    list_display = ('id', 'btc_usd_price', 'is_active', 'updated_at')
    list_editable = ('btc_usd_price', 'is_active')


@admin.register(Swap)
class SwapAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'direction', 'from_amount', 'to_amount', 'rate_used', 'created_at')
    list_filter = ('direction', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at',)


@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'nickname', 'type', 'account_number', 'bank_name', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ('user__username', 'nickname', 'account_number', 'bank_name')


@admin.register(ExternalTransfer)
class ExternalTransferAdmin(admin.ModelAdmin):
    list_display = ('id', 'transfer_user', 'transfer_type', 'method', 'amount', 'status_badge',
                    'account_holder_name', 'bank_name', 'created_at')
    list_filter = ('transfer_type', 'method')
    search_fields = ('transaction__user__username', 'account_holder_name', 'account_number', 'bank_name')
    actions = ['approve_transfers', 'reject_transfers']

    def transfer_user(self, obj):
        return obj.transaction.user
    transfer_user.short_description = 'User'

    def amount(self, obj):
        return obj.transaction.amount
    amount.short_description = 'Amount'

    def created_at(self, obj):
        return obj.transaction.created_at
    created_at.short_description = 'Created'

    def status_badge(self, obj):
        return _status_badge(obj.transaction.status)
    status_badge.short_description = 'Status'

    def approve_transfers(self, request, queryset):
        n = 0
        for et in queryset.select_related('transaction'):
            if et.transaction.status == 'pending' and et.transaction.approve():
                n += 1
        self.message_user(request, f'{n} transfer(s) approved (balance debited).')
    approve_transfers.short_description = 'Approve selected transfers'

    def reject_transfers(self, request, queryset):
        n = 0
        for et in queryset.select_related('transaction'):
            if et.transaction.status == 'pending':
                et.transaction.reject('Rejected by admin')
                n += 1
        self.message_user(request, f'{n} transfer(s) rejected.')
    reject_transfers.short_description = 'Reject selected transfers'
