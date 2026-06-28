from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from .models import User, LoginHistory, Notification, LoginCode, KYCVerification
from .email_utils import EmailService

# Remove the default Django "Groups" model from the admin — this platform does not
# use group-based permissions, so it is just clutter.
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for custom User model"""

    # Fields to display in the user list
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'balance',
        'btc_balance',
        'total_profit',
        'referral_code',
        'is_verified',
        'is_staff',
        'is_active',
        'created_at'
    )

    # Fields to filter by
    list_filter = (
        'is_staff',
        'is_active',
        'is_verified',
        'created_at',
        'date_joined'
    )

    # Fields to search
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
        'phone',
        'referral_code'
    )

    # Read-only fields
    readonly_fields = (
        'referral_code',
        'created_at',
        'updated_at',
        'date_joined',
        'last_login'
    )

    # Fieldsets for the user detail page
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Financial Information', {
            'fields': (
                'balance',
                'btc_balance',
                'total_profit',
                'total_bonus',
                'referral_bonus'
            )
        }),
        ('Referral Information', {
            'fields': ('referral_code', 'referred_by')
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_verified',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            )
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')
        }),
    )

    # Fieldsets for adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'password1',
                'password2',
                'first_name',
                'last_name',
                'phone',
                'is_staff',
                'is_active'
            ),
        }),
    )

    # Order by newest first
    ordering = ('-created_at',)

    actions = ['mark_as_verified', 'mark_as_unverified']

    def mark_as_verified(self, request, queryset):
        n = queryset.update(is_verified=True)
        self.message_user(request, f'{n} user(s) marked Verified.')
    mark_as_verified.short_description = 'Mark selected users as Verified'

    def mark_as_unverified(self, request, queryset):
        n = queryset.update(is_verified=False)
        self.message_user(request, f'{n} user(s) marked Unverified.')
    mark_as_unverified.short_description = 'Mark selected users as Unverified'


# EmailVerificationToken and PasswordResetToken are transient internal plumbing
# (auto-created and consumed during signup / password reset). They are intentionally
# NOT registered in the admin to keep it focused on platform management.


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    """Admin interface for Login History"""
    list_display = ('user', 'ip_address', 'login_time', 'success')
    list_filter = ('success', 'login_time')
    search_fields = ('user__username', 'user__email', 'ip_address')
    readonly_fields = ('user', 'ip_address', 'user_agent', 'location', 'login_time', 'success')
    ordering = ('-login_time',)

    def has_add_permission(self, request):
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for Notifications"""
    list_display = ('user', 'title', 'type', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('user__username', 'user__email', 'title', 'message')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f"{queryset.count()} notification(s) marked as read.")
    mark_as_read.short_description = "Mark selected notifications as read"

    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f"{queryset.count()} notification(s) marked as unread.")
    mark_as_unread.short_description = "Mark selected notifications as unread"


@admin.register(LoginCode)
class LoginCodeAdmin(admin.ModelAdmin):
    """Generate, view and deactivate passwordless login codes.

    Use the "Add login code" button to mint a code for a user as an email
    fallback — the 6-digit code is generated automatically and shown to you so
    you can pass it to the user. Use the row checkbox + "Deactivate" action (or
    untick "Is active" on the detail page) to revoke a code immediately.
    """
    list_display = ('user', 'code', 'status', 'created_by_admin', 'created_at', 'expires_at')
    list_filter = ('is_active', 'is_used', 'created_by_admin', 'created_at')
    search_fields = ('user__username', 'user__email', 'code')
    autocomplete_fields = ('user',)
    ordering = ('-created_at',)
    actions = ('deactivate_codes', 'reactivate_codes')

    @admin.display(description='Status')
    def status(self, obj):
        return obj.status

    def get_fields(self, request, obj=None):
        # On the add form the admin only picks the user; everything else
        # (code, expiry, audit fields) is filled in automatically.
        if obj is None:
            return ('user',)
        return (
            'user', 'code', 'is_active', 'is_used', 'created_by_admin',
            'generated_by', 'created_at', 'expires_at',
        )

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ()
        # After creation only `is_active` stays editable (so codes can be revoked
        # or restored); the code itself and the audit trail are immutable.
        return (
            'user', 'code', 'is_used', 'created_by_admin',
            'generated_by', 'created_at', 'expires_at',
        )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by_admin = True
            obj.generated_by = request.user
            # code + (longer) expiry are filled in by LoginCode.save()
        super().save_model(request, obj, form, change)
        if not change:
            self.message_user(
                request,
                f'Login code for {obj.user.email or obj.user.username}: '
                f'{obj.code}  —  expires {obj.expires_at:%Y-%m-%d %H:%M}. '
                f'Share it with the user; they enter it at /auth/login-code/verify/.',
                level=messages.SUCCESS,
            )

    @admin.action(description='Deactivate selected login codes')
    def deactivate_codes(self, request, queryset):
        n = queryset.update(is_active=False)
        self.message_user(request, f'{n} login code(s) deactivated.')

    @admin.action(description='Reactivate selected login codes')
    def reactivate_codes(self, request, queryset):
        n = queryset.update(is_active=True)
        self.message_user(request, f'{n} login code(s) reactivated.')


@admin.register(KYCVerification)
class KYCVerificationAdmin(admin.ModelAdmin):
    """Review and verify users' identity (KYC) submissions."""
    list_display = ('user', 'full_name', 'document_type', 'status', 'submitted_at', 'reviewed_at')
    list_filter = ('status', 'document_type', 'submitted_at')
    search_fields = ('user__username', 'user__email', 'first_name', 'last_name')
    ordering = ('-submitted_at',)
    actions = ('approve_kyc', 'reject_kyc')

    readonly_fields = (
        'user', 'first_name', 'last_name', 'phone', 'date_of_birth', 'gender',
        'telegram_username', 'country', 'state', 'city', 'postal_code',
        'address_line_1', 'address_line_2', 'document_type',
        'document_preview', 'selfie_preview', 'submitted_at', 'reviewed_at', 'reviewed_by',
    )
    fields = (
        'user', 'status', 'rejection_reason',
        ('first_name', 'last_name'), ('phone', 'date_of_birth'), ('gender', 'telegram_username'),
        ('country', 'state'), ('city', 'postal_code'), ('address_line_1', 'address_line_2'),
        'document_type', 'document_preview', 'selfie_preview',
        ('submitted_at', 'reviewed_at'), 'reviewed_by',
    )

    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Name'

    def document_preview(self, obj):
        if obj.document_image:
            return format_html('<img src="{}" style="max-width:480px;max-height:480px;" />', obj.document_image.url)
        return 'No document uploaded'
    document_preview.short_description = 'ID document'

    def selfie_preview(self, obj):
        if obj.selfie_image:
            return format_html('<img src="{}" style="max-width:480px;max-height:480px;" />', obj.selfie_image.url)
        return 'No selfie uploaded'
    selfie_preview.short_description = 'Selfie with document'

    @admin.action(description='Approve selected — verify identity')
    def approve_kyc(self, request, queryset):
        n = 0
        for k in queryset.exclude(status=KYCVerification.STATUS_APPROVED):
            k.approve(by_user=request.user)
            try:
                EmailService.send_kyc_approved_email(k.user)
            except Exception:
                pass
            n += 1
        self.message_user(request, f'{n} submission(s) approved — deposits & withdrawals unlocked.')

    @admin.action(description='Reject selected')
    def reject_kyc(self, request, queryset):
        n = 0
        for k in queryset.exclude(status=KYCVerification.STATUS_REJECTED):
            k.reject(reason=k.rejection_reason or 'Please re-submit clear, valid documents.', by_user=request.user)
            try:
                EmailService.send_kyc_rejected_email(k.user, k.rejection_reason)
            except Exception:
                pass
            n += 1
        self.message_user(request, f'{n} submission(s) rejected.')
