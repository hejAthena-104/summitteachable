"""Storefront checkout tests — the proof-of-payment upload is reachable without
logging in, so it must only ever store real images."""

import io
import shutil
import tempfile
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts import upload_utils
from education.models import Course
from store.models import CoursePurchase

User = get_user_model()

_TEST_STATIC = override_settings(
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage'
)

_PHP = b'<?php echo "SHELL_OK"; phpinfo(); ?>'


def _image_bytes(fmt='PNG'):
    from PIL import Image
    buf = io.BytesIO()
    Image.new('RGB', (4, 4), (120, 90, 200)).save(buf, fmt)
    return buf.getvalue()


class CleanImageUploadTests(TestCase):
    def test_accepts_real_images_and_renames_them(self):
        for fmt, ext in (('PNG', '.png'), ('JPEG', '.jpg'), ('WEBP', '.webp')):
            f = SimpleUploadedFile('My Receipt.final.png', _image_bytes(fmt), content_type='image/png')
            self.assertIsNone(upload_utils.clean_image_upload(f))
            self.assertTrue(f.name.endswith(ext), f.name)
            self.assertNotIn('Receipt', f.name)
            self.assertEqual(f.tell(), 0)

    def test_extension_follows_the_content_not_the_claimed_name(self):
        f = SimpleUploadedFile('shell.php', _image_bytes('PNG'), content_type='image/png')
        self.assertIsNone(upload_utils.clean_image_upload(f))
        self.assertTrue(f.name.endswith('.png'))

    def test_rejects_non_images(self):
        for name in ('shell.php', 'shell.php.png', 'shell.phtml', 'note.png'):
            f = SimpleUploadedFile(name, _PHP, content_type='image/png')
            self.assertIsNotNone(upload_utils.clean_image_upload(f))

    def test_rejects_fake_png_header(self):
        f = SimpleUploadedFile('x.png', b'\x89PNG\r\n\x1a\n' + b'\x00' * 100, content_type='image/png')
        self.assertIsNotNone(upload_utils.clean_image_upload(f))

    def test_rejects_svg(self):
        svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
        f = SimpleUploadedFile('x.svg', svg, content_type='image/svg+xml')
        self.assertIsNotNone(upload_utils.clean_image_upload(f))

    def test_rejects_oversized_files(self):
        f = SimpleUploadedFile('big.png', _image_bytes(), content_type='image/png')
        with mock.patch.object(upload_utils, 'MAX_IMAGE_UPLOAD_BYTES', 10):
            self.assertIsNotNone(upload_utils.clean_image_upload(f))


@_TEST_STATIC
class CheckoutUploadTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._media_dir = tempfile.mkdtemp(prefix='summit-test-media-')
        cls._media_override = override_settings(MEDIA_ROOT=cls._media_dir)
        cls._media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._media_override.disable()
        shutil.rmtree(cls._media_dir, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        p = mock.patch('accounts.email_utils.EmailService.send_email', return_value=True)
        p.start()
        self.addCleanup(p.stop)
        self.course = Course.objects.create(title='Test Course', slug='test-course', price=1000,
                                            is_published=True)
        self.url = reverse('store:checkout', args=[self.course.slug])

    def _buy(self, upload, email='buyer@example.com'):
        return self.client.post(self.url, {
            'email': email, 'name': 'Buyer One', 'payment_method': 'USDT', 'proof_image': upload,
        })

    def test_real_image_creates_a_pending_purchase(self):
        self._buy(SimpleUploadedFile('receipt.png', _image_bytes(), content_type='image/png'))
        purchase = CoursePurchase.objects.get()
        self.assertEqual(purchase.status, 'pending')
        self.assertTrue(purchase.proof_image.name.startswith('course_purchases/'))
        self.assertTrue(purchase.proof_image.name.endswith('.png'))

    def test_script_upload_is_rejected_and_leaves_nothing_behind(self):
        for name in ('shell.php', 'shell.php.png', 'shell.phtml'):
            resp = self._buy(SimpleUploadedFile(name, _PHP, content_type='image/png'))
            self.assertEqual(resp.status_code, 200)
        self.assertEqual(CoursePurchase.objects.count(), 0)
        # A rejected submission must not create an account either — that is how
        # an attacker minted dozens of users through this form.
        self.assertFalse(User.objects.filter(email='buyer@example.com').exists())

    def test_stored_name_never_keeps_an_executable_extension(self):
        self._buy(SimpleUploadedFile('shell.php', _image_bytes(), content_type='image/png'))
        self.assertFalse(CoursePurchase.objects.get().proof_image.name.endswith('.php'))
