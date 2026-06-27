from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
import secrets
import string
import uuid


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    Adds investment-related fields for the platform
    """
    # Contact Information
    phone = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    # Profile
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    # Financial Fields
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="User's available balance"
    )
    total_profit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Total profit earned from investments"
    )
    total_bonus = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Total bonuses received"
    )
    referral_bonus = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Total earnings from referrals"
    )
    btc_balance = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=0,
        help_text="User's BTC balance (from USD<->BTC swaps)"
    )

    # Referral System
    referral_code = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
        help_text="Unique referral code for this user"
    )
    referred_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals',
        help_text="User who referred this user"
    )

    # Account Status
    is_verified = models.BooleanField(
        default=False,
        help_text="Email verification status"
    )

    # Platform access gate — users must enter a valid access code (e.g. SUMMIT26)
    # before they can browse courses or buy anything. Unlock is permanent per account.
    course_access_unlocked = models.BooleanField(
        default=False,
        help_text="Whether this user has entered a valid platform access code.",
    )
    course_access_unlocked_at = models.DateTimeField(null=True, blank=True)

    # Security
    withdrawal_otp = models.CharField(max_length=6, blank=True, null=True)
    transaction_pin = models.CharField(
        max_length=128, blank=True,
        help_text="Hashed transaction PIN for authorising transfers"
    )

    # Bank Details
    bank_name = models.CharField(max_length=200, blank=True)
    account_name = models.CharField(max_length=200, blank=True)
    account_number = models.CharField(max_length=100, blank=True)
    swift_code = models.CharField(max_length=50, blank=True)

    # Cryptocurrency Addresses
    btc_address = models.CharField(max_length=200, blank=True, verbose_name="Bitcoin Address")
    eth_address = models.CharField(max_length=200, blank=True, verbose_name="Ethereum Address")
    ltc_address = models.CharField(max_length=200, blank=True, verbose_name="Litecoin Address")
    usdt_address = models.CharField(max_length=200, blank=True, verbose_name="USDT Address")

    # Email Notification Preferences
    email_on_withdrawal = models.BooleanField(default=True, help_text="Receive email on withdrawal requests")
    email_on_roi = models.BooleanField(default=True, help_text="Receive email on ROI/profit credits")
    email_on_expiration = models.BooleanField(default=True, help_text="Receive email on plan expiration")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return self.username

    @property
    def has_course_access(self):
        """Staff always pass; everyone else needs to have entered an access code."""
        return self.is_staff or self.course_access_unlocked

    def grant_course_access(self):
        if not self.course_access_unlocked:
            self.course_access_unlocked = True
            self.course_access_unlocked_at = timezone.now()
            self.save(update_fields=['course_access_unlocked', 'course_access_unlocked_at'])

    def save(self, *args, **kwargs):
        # Generate referral code if not exists
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)

    def generate_referral_code(self):
        """Generate a unique 8-character referral code"""
        while True:
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            if not User.objects.filter(referral_code=code).exists():
                return code

    @property
    def total_deposited(self):
        """Calculate total amount deposited by user"""
        from transactions.models import Transaction
        return Transaction.objects.filter(
            user=self,
            type='deposit',
            status='approved'
        ).aggregate(models.Sum('amount'))['amount__sum'] or 0

    @property
    def total_withdrawn(self):
        """Calculate total amount withdrawn by user"""
        from transactions.models import Transaction
        return Transaction.objects.filter(
            user=self,
            type='withdrawal',
            status='approved'
        ).aggregate(models.Sum('amount'))['amount__sum'] or 0

    @property
    def referral_count(self):
        """Count number of users referred by this user"""
        return self.referrals.count()

    def get_full_name(self):
        """Return user's full name or username"""
        full_name = super().get_full_name()
        return full_name if full_name else self.username

    # ---- Transaction PIN (hashed; never stored in plaintext) ----
    def set_transaction_pin(self, raw_pin):
        from django.contrib.auth.hashers import make_password
        self.transaction_pin = make_password(str(raw_pin))

    def check_transaction_pin(self, raw_pin):
        from django.contrib.auth.hashers import check_password
        if not self.transaction_pin:
            return False
        return check_password(str(raw_pin), self.transaction_pin)

    @property
    def has_transaction_pin(self):
        return bool(self.transaction_pin)


class EmailVerificationToken(models.Model):
    """Model for email verification tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Email Verification Token'
        verbose_name_plural = 'Email Verification Tokens'
        ordering = ['-created_at']

    def __str__(self):
        return f"Verification token for {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Token expires in 24 hours
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_valid(self):
        """Check if token is still valid"""
        return not self.is_used and timezone.now() < self.expires_at

    def mark_as_used(self):
        """Mark token as used"""
        self.is_used = True
        self.save()


class PasswordResetToken(models.Model):
    """Model for password reset tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
        ordering = ['-created_at']

    def __str__(self):
        return f"Password reset token for {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Token expires in 1 hour
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)

    def is_valid(self):
        """Check if token is still valid"""
        return not self.is_used and timezone.now() < self.expires_at

    def mark_as_used(self):
        """Mark token as used"""
        self.is_used = True
        self.save()


class LoginCode(models.Model):
    """Short-lived 6-digit code for passwordless email login.

    Used by course buyers (who never set a password) and anyone who prefers a
    one-time code. Cloned from the email-verification token pattern but with a
    short numeric code and a 15-minute expiry.

    Admins can also generate a code manually from the Django admin as an email
    fallback (e.g. when a user never receives the email). Admin-generated codes
    get a longer expiry and can be deactivated at any time."""

    # Codes requested by the user via email expire quickly; codes an admin hands
    # over manually get a longer window since delivery is out-of-band.
    USER_EXPIRY_MINUTES = 15
    ADMIN_EXPIRY_MINUTES = 60

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_codes')
    code = models.CharField(max_length=6, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    is_used = models.BooleanField(default=False)
    is_active = models.BooleanField(
        default=True,
        help_text='Uncheck to deactivate this code so it can no longer be used to log in.',
    )
    created_by_admin = models.BooleanField(
        default=False,
        help_text='Generated by an admin as an email fallback.',
    )
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issued_login_codes',
        help_text='The admin who generated this code (if any).',
    )

    class Meta:
        verbose_name = 'Login Code'
        verbose_name_plural = 'Login Codes'
        ordering = ['-created_at']

    def __str__(self):
        return f"Login code for {self.user.username}"

    @staticmethod
    def generate_code():
        return ''.join(secrets.choice(string.digits) for _ in range(6))

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        if not self.expires_at:
            minutes = self.ADMIN_EXPIRY_MINUTES if self.created_by_admin else self.USER_EXPIRY_MINUTES
            self.expires_at = timezone.now() + timedelta(minutes=minutes)
        super().save(*args, **kwargs)

    def is_valid(self):
        return (
            self.is_active
            and not self.is_used
            and self.expires_at is not None
            and timezone.now() < self.expires_at
        )

    def mark_as_used(self):
        self.is_used = True
        self.save(update_fields=['is_used'])

    def deactivate(self):
        self.is_active = False
        self.save(update_fields=['is_active'])

    @property
    def status(self):
        """Human-readable lifecycle state for admin display."""
        if self.is_used:
            return 'Used'
        if not self.is_active:
            return 'Deactivated'
        if self.expires_at is not None and timezone.now() >= self.expires_at:
            return 'Expired'
        return 'Active'


class AccessCode(models.Model):
    """A shared platform access code (e.g. SUMMIT26).

    Users must enter a valid, active code once before they can browse courses or
    buy anything; the unlock is then saved permanently on their account. Admins
    manage these codes (create new ones, deactivate old ones) from the admin."""
    code = models.CharField(
        max_length=32,
        unique=True,
        help_text='The access code users type to unlock the platform (case-insensitive).',
    )
    label = models.CharField(
        max_length=120,
        blank=True,
        help_text='Optional note, e.g. "Launch cohort" or "Q3 promo".',
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Only active codes can be redeemed. Uncheck to retire a code.',
    )
    times_used = models.PositiveIntegerField(default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_access_codes',
    )

    class Meta:
        verbose_name = 'Access Code'
        verbose_name_plural = 'Access Codes'
        ordering = ['-created_at']

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        # Store codes normalised so matching is reliable and case-insensitive.
        if self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    @classmethod
    def match(cls, raw_code):
        """Return the active AccessCode matching the entered value, or None."""
        if not raw_code:
            return None
        return cls.objects.filter(code=raw_code.strip().upper(), is_active=True).first()


class LoginHistory(models.Model):
    """Model to track user login history"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    login_time = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Login History'
        verbose_name_plural = 'Login History'
        ordering = ['-login_time']

    def __str__(self):
        return f"{self.user.username} - {self.login_time.strftime('%Y-%m-%d %H:%M:%S')}"


class Notification(models.Model):
    """Model for user notifications"""
    TYPE_CHOICES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('investment', 'Investment'),
        ('profit', 'Profit'),
        ('bonus', 'Bonus'),
        ('referral', 'Referral'),
        ('system', 'System'),
        ('security', 'Security'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='system')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.save()
