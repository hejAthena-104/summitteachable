"""Public course storefront — REAL course purchases.

HARD FIREWALL: a CoursePurchase is a real purchase of a real product (course
access). It is completely separate from the demo `transactions` wallet and MUST
NEVER touch `user.balance` (the simulated paper-trading balance). Approving a
purchase grants an `education.Enrollment` — nothing else. There is no path from
this app to the demo trading balance.
"""
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from education.models import Course, Enrollment


class CoursePurchase(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending review'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='course_purchases',
        on_delete=models.CASCADE,
    )
    course = models.ForeignKey(Course, related_name='purchases', on_delete=models.CASCADE)

    # Buyer details captured at checkout (account is created from these).
    buyer_email = models.EmailField()
    buyer_name = models.CharField(max_length=160, blank=True)
    buyer_phone = models.CharField(max_length=40, blank=True)
    buyer_country = models.CharField(max_length=80, blank=True)

    # Real payment details (crypto + manual proof, admin-verified).
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    payment_method = models.CharField(max_length=60, blank=True, help_text='e.g. USDT, Bitcoin')
    tx_reference = models.CharField(max_length=255, blank=True, help_text='On-chain tx hash / reference')
    proof_image = models.ImageField(upload_to='course_purchases/', null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Course purchase'
        verbose_name_plural = 'Course purchases'

    def __str__(self):
        return f'{self.buyer_email} → {self.course.title} ({self.status})'

    def approve(self):
        """Grant course access. Creates an Enrollment ONLY — never credits any
        balance. Idempotent on status."""
        if self.status == 'approved':
            return False
        self.status = 'approved'
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])
        Enrollment.objects.get_or_create(user=self.user, course=self.course)
        return True

    def decline(self, reason=''):
        self.status = 'declined'
        if reason:
            self.admin_note = reason
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'admin_note', 'processed_at'])
        return True
