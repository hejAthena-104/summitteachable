"""Tests for the abuse protections in ``config.security``: real client IP,
per-IP throttling of the auth/checkout endpoints, Turnstile gating and the
configurable admin path."""

from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from accounts.models import LoginHistory
from config import security

User = get_user_model()

_TEST_STATIC = override_settings(
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage'
)


class ClientIpTests(TestCase):
    def _req(self, remote, xff=None):
        extra = {'REMOTE_ADDR': remote}
        if xff is not None:
            extra['HTTP_X_FORWARDED_FOR'] = xff
        return RequestFactory().get('/', **extra)

    def test_uses_forwarded_ip_when_request_comes_from_the_proxy(self):
        self.assertEqual(security.client_ip(self._req('172.18.0.3', '203.0.113.9')), '203.0.113.9')

    def test_takes_the_entry_added_by_the_nearest_proxy(self):
        req = self._req('172.18.0.3', '1.2.3.4, 203.0.113.9')
        self.assertEqual(security.client_ip(req), '203.0.113.9')

    def test_ignores_forwarded_header_from_a_public_peer(self):
        # Only our own proxy (private network) may vouch for another address.
        self.assertEqual(security.client_ip(self._req('8.8.8.8', '203.0.113.9')), '8.8.8.8')

    def test_falls_back_to_remote_addr_on_garbage(self):
        self.assertEqual(security.client_ip(self._req('172.18.0.3', 'not-an-ip')), '172.18.0.3')
        self.assertEqual(security.client_ip(self._req('172.18.0.3')), '172.18.0.3')


@_TEST_STATIC
@override_settings(AUTH_THROTTLE_ENABLED=True)
class AuthThrottleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        p = mock.patch('accounts.email_utils.EmailService.send_email', return_value=True)
        p.start()
        self.addCleanup(p.stop)

    def _post_login(self, ip='203.0.113.9', url=None):
        return self.client.post(
            url or reverse('accounts:login'),
            {'username': 'nobody', 'password': 'wrong'},
            REMOTE_ADDR='172.18.0.3', HTTP_X_FORWARDED_FOR=ip,
        )

    def test_login_attempts_are_cut_off_per_ip(self):
        limit = security.THROTTLE_RULES['login'][0][0]
        for _ in range(limit):
            self.assertEqual(self._post_login().status_code, 200)
        resp = self._post_login()
        self.assertEqual(resp.status_code, 429)
        self.assertIn('Retry-After', resp)

    def test_other_ips_are_not_affected(self):
        limit = security.THROTTLE_RULES['login'][0][0]
        for _ in range(limit + 1):
            self._post_login(ip='203.0.113.9')
        self.assertEqual(self._post_login(ip='203.0.113.10').status_code, 200)

    def test_admin_login_shares_the_login_budget(self):
        limit = security.THROTTLE_RULES['login'][0][0]
        admin_login = reverse('admin:login')
        for _ in range(limit):
            self._post_login(url=admin_login)
        self.assertEqual(self._post_login(url=admin_login).status_code, 429)

    def test_registration_is_throttled(self):
        limit = security.THROTTLE_RULES['register'][0][0]
        for _ in range(limit):
            self.client.post(reverse('accounts:register'), {}, REMOTE_ADDR='203.0.113.9')
        resp = self.client.post(reverse('accounts:register'), {}, REMOTE_ADDR='203.0.113.9')
        self.assertEqual(resp.status_code, 429)

    def test_ipv6_addresses_in_one_64_share_a_budget(self):
        limit = security.THROTTLE_RULES['login'][0][0]
        for i in range(limit):
            self._post_login(ip='2001:db8:1:2::%x' % (i + 1))
        self.assertEqual(self._post_login(ip='2001:db8:1:2:ffff::1').status_code, 429)
        self.assertEqual(self._post_login(ip='2001:db8:1:3::1').status_code, 200)

    def test_get_requests_are_never_throttled(self):
        for _ in range(security.THROTTLE_RULES['login'][0][0] + 5):
            resp = self.client.get(reverse('accounts:login'), REMOTE_ADDR='203.0.113.9')
        self.assertEqual(resp.status_code, 200)

    @override_settings(AUTH_THROTTLE_ENABLED=False)
    def test_can_be_switched_off(self):
        for _ in range(security.THROTTLE_RULES['login'][0][0] + 2):
            resp = self._post_login()
        self.assertEqual(resp.status_code, 200)


@_TEST_STATIC
class TurnstileTests(TestCase):
    def setUp(self):
        p = mock.patch('accounts.email_utils.EmailService.send_email', return_value=True)
        p.start()
        self.addCleanup(p.stop)
        self.user = User.objects.create_user(username='tuser', email='tuser@example.com', password='pw-12345')

    def _register(self, **extra):
        data = {
            'username': 'newbie', 'email': 'newbie@example.com', 'first_name': 'New', 'last_name': 'Bie',
            'password1': 'S0me-long-passw0rd', 'password2': 'S0me-long-passw0rd',
        }
        data.update(extra)
        return self.client.post(reverse('accounts:register'), data)

    def test_disabled_without_keys(self):
        self.assertFalse(security.turnstile_enabled())
        self._register()
        self.assertTrue(User.objects.filter(username='newbie').exists())

    def test_widget_not_rendered_without_keys(self):
        self.assertNotContains(self.client.get(reverse('accounts:register')), 'cf-turnstile')

    @override_settings(TURNSTILE_SITEKEY='site-key', TURNSTILE_SECRET='secret')
    def test_widget_rendered_on_protected_forms(self):
        for name in ('accounts:register', 'accounts:login'):
            self.assertContains(self.client.get(reverse(name)), 'data-sitekey="site-key"')

    @override_settings(TURNSTILE_SITEKEY='site-key', TURNSTILE_SECRET='secret')
    def test_register_rejected_without_a_valid_token(self):
        with mock.patch('config.security._siteverify', return_value={'success': False}):
            resp = self._register(**{'cf-turnstile-response': 'bad'})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username='newbie').exists())

    @override_settings(TURNSTILE_SITEKEY='site-key', TURNSTILE_SECRET='secret')
    def test_missing_token_never_reaches_cloudflare(self):
        with mock.patch('config.security._siteverify') as sv:
            self._register()
        sv.assert_not_called()
        self.assertFalse(User.objects.filter(username='newbie').exists())

    @override_settings(TURNSTILE_SITEKEY='site-key', TURNSTILE_SECRET='secret')
    def test_register_accepted_with_a_valid_token(self):
        with mock.patch('config.security._siteverify', return_value={'success': True}) as sv:
            self._register(**{'cf-turnstile-response': 'good'})
        self.assertTrue(User.objects.filter(username='newbie').exists())
        self.assertEqual(sv.call_args[0][0], 'good')

    @override_settings(TURNSTILE_SITEKEY='site-key', TURNSTILE_SECRET='secret')
    def test_login_rejected_without_a_valid_token(self):
        with mock.patch('config.security._siteverify', return_value={'success': False}):
            self.client.post(reverse('accounts:login'),
                             {'username': 'tuser', 'password': 'pw-12345', 'cf-turnstile-response': 'bad'})
        self.assertNotIn('_auth_user_id', self.client.session)

    @override_settings(TURNSTILE_SITEKEY='site-key', TURNSTILE_SECRET='secret')
    def test_verification_outage_fails_closed(self):
        with mock.patch('config.security._siteverify', side_effect=OSError('network down')):
            self.client.post(reverse('accounts:login'),
                             {'username': 'tuser', 'password': 'pw-12345', 'cf-turnstile-response': 'tok'})
        self.assertNotIn('_auth_user_id', self.client.session)


@_TEST_STATIC
class LoginHistoryIpTests(TestCase):
    def test_login_history_records_the_real_client_ip(self):
        User.objects.create_user(username='huser', email='huser@example.com', password='pw-12345')
        self.client.post(reverse('accounts:login'), {'username': 'huser', 'password': 'pw-12345'},
                         REMOTE_ADDR='172.18.0.3', HTTP_X_FORWARDED_FOR='203.0.113.9')
        self.assertEqual(LoginHistory.objects.get().ip_address, '203.0.113.9')


@_TEST_STATIC
class AdminPathTests(TestCase):
    def test_blank_or_root_values_fall_back_to_the_default(self):
        from config.settings import _admin_path
        for raw in ('', ' ', '/', '//'):
            self.assertEqual(_admin_path(raw), 'admin-local-only/')

    def test_value_is_normalised(self):
        from config.settings import _admin_path
        self.assertEqual(_admin_path('/secret-desk/'), 'secret-desk/')
        self.assertEqual(_admin_path('secret-desk'), 'secret-desk/')

    def test_admin_is_not_served_at_the_default_path(self):
        self.assertEqual(self.client.get('/admin/login/').status_code, 404)
        self.assertEqual(self.client.get(reverse('admin:login')).status_code, 200)
