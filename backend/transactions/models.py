import secrets
import string

from django.db import models
from django.utils import timezone
from decimal import Decimal
from accounts.models import User


class Transaction(models.Model):
    """Model for all user transactions (deposits, withdrawals, transfers)"""

    TYPE_CHOICES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
        ('bonus', 'Bonus'),
        ('referral', 'Referral Bonus'),
        ('profit', 'Profit'),
        ('swap', 'Currency Swap'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('bitcoin', 'Bitcoin'),
        ('ethereum', 'Ethereum'),
        ('usdt', 'USDT (TRC20)'),
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
        ('stripe', 'Credit/Debit Card'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')

    # Transaction details
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Payment details
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    payment_reference = models.CharField(max_length=255, blank=True, help_text="Transaction ID or reference")
    payment_address = models.CharField(max_length=255, blank=True, help_text="Wallet address or account number")

    # Additional info
    description = models.TextField(blank=True)
    admin_note = models.TextField(blank=True, help_text="Internal notes for administrators")

    # For transfers
    recipient = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_transfers')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.type} - ${self.amount} - {self.status}"

    def approve(self):
        """Approve transaction and update user balance"""
        if self.status != 'pending':
            return False

        self.status = 'approved'
        self.processed_at = timezone.now()

        # Update user balance based on transaction type
        if self.type == 'deposit':
            self.user.balance += self.amount
        elif self.type == 'withdrawal':
            if self.user.balance >= self.amount:
                self.user.balance -= self.amount
            else:
                return False  # Insufficient balance
        elif self.type in ['bonus', 'referral', 'profit']:
            self.user.balance += self.amount

        self.user.save()
        self.save()
        return True

    def reject(self, reason=''):
        """Reject transaction"""
        self.status = 'rejected'
        self.admin_note = reason
        self.processed_at = timezone.now()
        self.save()


class SiteSetting(models.Model):
    """Global site toggles managed from the admin (single row / singleton)."""

    withdrawals_enabled = models.BooleanField(
        default=True,
        help_text="When OFF, the 'Request code' and 'Complete Request' buttons are hidden on the "
                  "withdrawal page and withdrawal requests are blocked. Use during maintenance or "
                  "when you're having trouble processing withdrawals."
    )
    request_code_enabled = models.BooleanField(
        default=True,
        verbose_name='"Request code" button enabled',
        help_text="When OFF, users can no longer email themselves a one-time code — the "
                  "'Request code' button disappears and only admin-issued Withdrawal Access "
                  "Codes are accepted. Leave ON unless you want every withdrawal to go "
                  "through a code you issued yourself."
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Setting'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return 'Site Settings'

    def save(self, *args, **kwargs):
        # Force a single row so there's always exactly one settings record.
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def current(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class WithdrawalAccessCode(models.Model):
    """An admin-issued withdrawal code, delivered to the user out of band.

    Corporate clients often can't work with the emailed one-time code — shared
    mailboxes, formal mandates, sign-off by someone who isn't the account
    holder. An admin issues a long-lived code here and sends it however suits
    the client (a signed document, or the 'Email this code' action). The user
    types it into the same box on the withdrawal form as the emailed OTP, so
    nothing changes for everyone else.
    """

    CODE_LENGTH = 8

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='withdrawal_access_codes',
        help_text="The account this code authorises withdrawals for.",
    )
    code = models.CharField(max_length=16, unique=True, db_index=True)
    label = models.CharField(
        max_length=120, blank=True,
        help_text="Your own note — e.g. 'Acme Ltd — mandate of 12 Aug 2026'. Not shown to the user.",
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Untick to revoke the code immediately without deleting the record.",
    )
    expires_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Leave blank and the code never expires.",
    )
    max_uses = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Leave blank for unlimited uses. Set to 1 to make it single-use.",
    )

    times_used = models.PositiveIntegerField(default=0, editable=False)
    last_used_at = models.DateTimeField(null=True, blank=True, editable=False)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='issued_withdrawal_codes', editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Withdrawal Access Code'
        verbose_name_plural = 'Withdrawal Access Codes'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.code} — {self.user.username}'

    @classmethod
    def generate_code(cls):
        return ''.join(secrets.choice(string.digits) for _ in range(cls.CODE_LENGTH))

    @staticmethod
    def normalize(value):
        """Drop spaces and dashes so '4021 8873' matches '40218873'."""
        return ''.join(ch for ch in (value or '') if ch.isdigit())

    def save(self, *args, **kwargs):
        if not self.code:
            # unique=True makes a collision a hard error, so retry a few times.
            for _ in range(10):
                candidate = self.generate_code()
                if not type(self).objects.filter(code=candidate).exists():
                    self.code = candidate
                    break
            else:
                raise RuntimeError('Could not generate a unique withdrawal access code.')
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return bool(self.expires_at and timezone.now() >= self.expires_at)

    @property
    def is_exhausted(self):
        return bool(self.max_uses and self.times_used >= self.max_uses)

    def is_valid(self):
        return self.is_active and not self.is_expired and not self.is_exhausted

    @property
    def status(self):
        # Order matters: hitting the use limit also flips is_active off, and
        # "Used up" is the more useful thing to show than "Revoked".
        if self.is_exhausted:
            return 'Used up'
        if self.is_expired:
            return 'Expired'
        if not self.is_active:
            return 'Revoked'
        return 'Active'

    @classmethod
    def verify(cls, user, submitted):
        """Return the matching valid code for this user, or None."""
        submitted = cls.normalize(submitted)
        if not submitted:
            return None
        for candidate in cls.objects.filter(user=user, is_active=True):
            if secrets.compare_digest(cls.normalize(candidate.code), submitted) and candidate.is_valid():
                return candidate
        return None

    def register_use(self):
        self.times_used += 1
        self.last_used_at = timezone.now()
        if self.is_exhausted:
            self.is_active = False
        self.save(update_fields=['times_used', 'last_used_at', 'is_active'])


class Deposit(models.Model):
    """Model for deposit requests (extends Transaction)"""

    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='deposit_details')

    # Proof of payment
    proof_image = models.ImageField(upload_to='deposits/', null=True, blank=True)

    class Meta:
        verbose_name = 'Deposit'
        verbose_name_plural = 'Deposits'
        ordering = ['-transaction__created_at']

    def __str__(self):
        return f"Deposit - {self.transaction}"


class Withdrawal(models.Model):
    """Model for withdrawal requests (extends Transaction)"""

    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='withdrawal_details')

    # Withdrawal details
    withdrawal_address = models.CharField(max_length=255, help_text="Wallet address or account details")
    withdrawal_method = models.CharField(max_length=50)

    class Meta:
        verbose_name = 'Withdrawal'
        verbose_name_plural = 'Withdrawals'
        ordering = ['-transaction__created_at']

    def __str__(self):
        return f"Withdrawal - {self.transaction}"


class Transfer(models.Model):
    """Model for internal fund transfers between users"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transfers_sent')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transfers_received')

    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True)

    # Fees
    fee_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_deducted = models.DecimalField(max_digits=15, decimal_places=2, help_text="Amount + Fee")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Transfer'
        verbose_name_plural = 'Transfers'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender.username} → {self.recipient.username} - ${self.amount}"

    def save(self, *args, **kwargs):
        # Calculate total deducted (amount + fee)
        if not self.total_deducted or self.total_deducted == 0:
            self.total_deducted = self.amount + self.fee_amount
        super().save(*args, **kwargs)

    def complete(self):
        """Complete the transfer - deduct from sender and credit recipient"""
        if self.status != 'pending':
            return False

        # Check if sender has sufficient balance
        if self.sender.balance < self.total_deducted:
            self.status = 'failed'
            self.save()
            return False

        # Deduct from sender
        self.sender.balance -= self.total_deducted
        self.sender.save()

        # Credit recipient
        self.recipient.balance += self.amount
        self.recipient.save()

        # Update status
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

        return True

    def cancel(self):
        """Cancel the transfer"""
        if self.status == 'pending':
            self.status = 'cancelled'
            self.save()
            return True
        return False


class PaymentMethod(models.Model):
    """Payment methods (deposit & withdrawal). Relocated from the removed investments app."""

    TYPE_CHOICES = [
        ('deposit', 'Deposit Only'),
        ('withdrawal', 'Withdrawal Only'),
        ('both', 'Both'),
    ]

    CHARGE_TYPE_CHOICES = [
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage'),
    ]

    name = models.CharField(max_length=50, unique=True, help_text="e.g., USDT, Bitcoin, Ethereum")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='both')
    icon = models.ImageField(upload_to='payment_methods/', blank=True, null=True)

    min_amount = models.DecimalField(max_digits=15, decimal_places=2, default=10.00)
    max_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Leave blank for no limit")

    charge_type = models.CharField(max_length=20, choices=CHARGE_TYPE_CHOICES, default='percentage')
    charge_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Amount or percentage based on charge type")

    duration = models.CharField(max_length=100, blank=True, help_text="e.g., '1-24 hours', 'Instant'")

    wallet_address = models.CharField(max_length=200, blank=True, help_text="Platform wallet address for receiving payments")
    qr_code = models.ImageField(upload_to='payment_qr_codes/', blank=True, null=True)

    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Display order")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Payment Method'
        verbose_name_plural = 'Payment Methods'
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

    def calculate_charge(self, amount):
        if self.charge_type == 'fixed':
            return self.charge_amount
        return (amount * self.charge_amount) / 100

    def get_total_amount(self, base_amount):
        return base_amount + self.calculate_charge(base_amount)


class SwapRate(models.Model):
    """Admin-set USD price of 1 BTC. Single active row drives the USD<->BTC swap."""
    btc_usd_price = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('65000.00'),
                                        help_text="Price of 1 BTC in USD")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Swap Rate'
        verbose_name_plural = 'Swap Rate'
        ordering = ['-updated_at']

    def __str__(self):
        return f"1 BTC = ${self.btc_usd_price}"

    @classmethod
    def current(cls):
        rate = cls.objects.filter(is_active=True).order_by('-updated_at').first()
        if not rate:
            rate = cls.objects.create()
        return rate


class Swap(models.Model):
    """Instant USD<->BTC conversion at the admin-set rate."""
    DIRECTION_CHOICES = [
        ('usd_to_btc', 'USD to BTC'),
        ('btc_to_usd', 'BTC to USD'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='swaps')
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES)
    from_amount = models.DecimalField(max_digits=20, decimal_places=8)
    to_amount = models.DecimalField(max_digits=20, decimal_places=8)
    rate_used = models.DecimalField(max_digits=15, decimal_places=2, help_text="BTC/USD price applied")
    status = models.CharField(max_length=20, default='completed')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Swap'
        verbose_name_plural = 'Swaps'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_direction_display()} - {self.from_amount}"


class Beneficiary(models.Model):
    """Saved transfer recipient (bank / wire / crypto / wallet service)."""
    TYPE_CHOICES = [
        ('local_bank', 'Local Bank'),
        ('wire', 'International Wire'),
        ('crypto', 'Cryptocurrency'),
        ('paypal', 'PayPal'),
        ('wise', 'Wise'),
        ('cashapp', 'Cash App'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='beneficiaries')
    nickname = models.CharField(max_length=100, help_text="Label for this beneficiary")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='local_bank')

    account_holder_name = models.CharField(max_length=150, blank=True)
    account_number = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=150, blank=True)
    account_type = models.CharField(max_length=50, blank=True)
    routing_number = models.CharField(max_length=50, blank=True)
    swift_code = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=100, blank=True)
    extra = models.JSONField(default=dict, blank=True, help_text="Method-specific details (email, tag, wallet, etc.)")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Beneficiary'
        verbose_name_plural = 'Beneficiaries'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.nickname} ({self.get_type_display()})"


class ExternalTransfer(models.Model):
    """Local / International outbound transfer detail. OneToOne to a pending withdrawal
    Transaction so it reuses Transaction.approve() to debit balance on admin approval."""
    TRANSFER_TYPE_CHOICES = [
        ('local', 'Local Transfer'),
        ('international', 'International Transfer'),
    ]
    METHOD_CHOICES = [
        ('local_bank', 'Local Bank'),
        ('wire', 'Wire Transfer'),
        ('crypto', 'Cryptocurrency'),
        ('paypal', 'PayPal'),
        ('wise', 'Wise'),
        ('cashapp', 'Cash App'),
        ('other', 'Other'),
    ]

    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='external_transfer')
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfers')

    transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPE_CHOICES)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='local_bank')
    fee = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    # Snapshot of recipient details at submission time
    account_holder_name = models.CharField(max_length=150, blank=True)
    account_number = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=150, blank=True)
    account_type = models.CharField(max_length=50, blank=True)
    routing_number = models.CharField(max_length=50, blank=True)
    swift_code = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=100, blank=True)
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'External Transfer'
        verbose_name_plural = 'External Transfers'
        ordering = ['-transaction__created_at']

    def __str__(self):
        return f"{self.get_transfer_type_display()} - {self.transaction}"
