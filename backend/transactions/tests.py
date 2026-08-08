from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import KYCVerification, User
from transactions.models import PaymentMethod, Transaction, WithdrawalAccessCode


class WithdrawalAccessCodeModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='corp', email='corp@example.com', password='pw')
        self.other = User.objects.create_user(username='other', email='other@example.com', password='pw')

    def test_code_is_generated_on_save(self):
        code = WithdrawalAccessCode.objects.create(user=self.user)
        self.assertTrue(code.code.startswith('STC-'))
        self.assertEqual(len(code.code), 18)

    def test_generated_codes_avoid_ambiguous_characters(self):
        for _ in range(25):
            generated = WithdrawalAccessCode.generate_code()
            self.assertNotRegex(generated.removeprefix('STC-'), r'[01OIL]')

    def test_verify_accepts_the_code_however_it_is_typed(self):
        code = WithdrawalAccessCode.objects.create(user=self.user)
        typed = code.code.lower().replace('-', ' ')
        self.assertEqual(WithdrawalAccessCode.verify(self.user, typed), code)

    def test_verify_rejects_another_users_code(self):
        code = WithdrawalAccessCode.objects.create(user=self.user)
        self.assertIsNone(WithdrawalAccessCode.verify(self.other, code.code))

    def test_verify_rejects_blank_and_wrong_codes(self):
        WithdrawalAccessCode.objects.create(user=self.user)
        self.assertIsNone(WithdrawalAccessCode.verify(self.user, ''))
        self.assertIsNone(WithdrawalAccessCode.verify(self.user, 'STC-AAAA-BBBB-CCCC'))

    def test_verify_rejects_revoked_expired_and_exhausted_codes(self):
        revoked = WithdrawalAccessCode.objects.create(user=self.user, is_active=False)
        expired = WithdrawalAccessCode.objects.create(
            user=self.user, expires_at=timezone.now() - timedelta(minutes=1))
        exhausted = WithdrawalAccessCode.objects.create(user=self.user, max_uses=1)
        exhausted.register_use()

        for code in (revoked, expired, exhausted):
            self.assertIsNone(WithdrawalAccessCode.verify(self.user, code.code), code.status)

    def test_blank_expiry_and_max_uses_mean_unlimited(self):
        code = WithdrawalAccessCode.objects.create(user=self.user)
        for _ in range(5):
            code.register_use()
        code.refresh_from_db()
        self.assertTrue(code.is_valid())
        self.assertEqual(code.status, 'Active')
        self.assertEqual(code.times_used, 5)

    def test_register_use_deactivates_a_code_that_hits_its_limit(self):
        code = WithdrawalAccessCode.objects.create(user=self.user, max_uses=2)
        code.register_use()
        self.assertTrue(code.is_valid())
        code.register_use()
        code.refresh_from_db()
        self.assertFalse(code.is_active)
        self.assertEqual(code.status, 'Used up')
        self.assertIsNotNone(code.last_used_at)


# The dashboard templates use {% static %} against the hashed manifest storage,
# which has no manifest under test. Plain storage keeps the view tests runnable.
@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class WithdrawalCodeViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='corp', email='corp@example.com', password='pw')
        self.user.balance = Decimal('5000')
        self.user.usdt_address = 'TXyz1234567890abcdefgh'
        self.user.save()
        KYCVerification.objects.create(user=self.user, status=KYCVerification.STATUS_APPROVED)
        PaymentMethod.objects.create(
            name='USDT', type='withdrawal', is_active=True, min_amount=Decimal('10'))

        self.client.force_login(self.user)
        session = self.client.session
        session['withdrawal_method'] = 'USDT'
        session.save()

    def _withdraw(self, code, amount='100'):
        return self.client.post(
            reverse('dashboard:withdraw_funds'), {'amount': amount, 'otp': code}, follow=True)

    def _restore_session(self):
        session = self.client.session
        session['withdrawal_method'] = 'USDT'
        session.save()

    def test_admin_access_code_authorises_a_withdrawal(self):
        code = WithdrawalAccessCode.objects.create(user=self.user)
        self._withdraw(code.code)

        self.assertEqual(Transaction.objects.filter(user=self.user, type='withdrawal').count(), 1)
        code.refresh_from_db()
        self.assertEqual(code.times_used, 1)

    def test_emailed_otp_still_works(self):
        self.user.withdrawal_otp = '123456'
        self.user.save()
        self._withdraw('123456')

        self.assertEqual(Transaction.objects.filter(user=self.user, type='withdrawal').count(), 1)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.withdrawal_otp)

    def test_wrong_code_creates_no_transaction(self):
        WithdrawalAccessCode.objects.create(user=self.user)
        self._withdraw('STC-AAAA-BBBB-CCCC')
        self.assertFalse(Transaction.objects.filter(user=self.user).exists())

    def test_revoked_code_creates_no_transaction(self):
        code = WithdrawalAccessCode.objects.create(user=self.user, is_active=False)
        self._withdraw(code.code)
        self.assertFalse(Transaction.objects.filter(user=self.user).exists())

    def test_unlimited_access_code_authorises_repeat_withdrawals(self):
        code = WithdrawalAccessCode.objects.create(user=self.user)
        self._withdraw(code.code)
        self._restore_session()
        self._withdraw(code.code)

        self.assertEqual(Transaction.objects.filter(user=self.user, type='withdrawal').count(), 2)
        code.refresh_from_db()
        self.assertEqual(code.times_used, 2)
