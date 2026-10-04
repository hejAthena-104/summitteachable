"""Shared handling for user file uploads.

Writing an upload to ``MEDIA_ROOT`` can fail for reasons that have nothing to do
with what the user submitted — a full disk, or (as happened in production) a
bind-mounted media directory the container user cannot write to. Django raises
``OSError``/``PermissionError`` out of ``.save()`` and, unhandled, the user just
gets a bare 500 page.

Views that accept uploads catch ``OSError`` and show ``UPLOAD_FAILED_MESSAGE``
instead. The failure is still logged with a full traceback so it shows up in
``docker logs`` — this makes the outage visible without making it silent.

The permission problem itself is prevented at the container level; see the
root-only preamble in ``docker-entrypoint.sh``.
"""

import uuid
import warnings

from django.utils.html import format_html
from PIL import Image

UPLOAD_FAILED_MESSAGE = (
    'We could not save your upload just now. Please try again in a moment — '
    'if it keeps happening, contact support.'
)

MAX_IMAGE_UPLOAD_BYTES = 8 * 1024 * 1024
INVALID_IMAGE_MESSAGE = 'Please upload a JPG, PNG or WebP image (a screenshot or photo), up to 8 MB.'

# Pillow format name -> the extension the file is stored under.
_IMAGE_EXTENSIONS = {'JPEG': '.jpg', 'PNG': '.png', 'WEBP': '.webp'}


def clean_image_upload(upload):
    """Check that an upload really is an image. Returns an error message for the
    user, or ``None`` when the file is fine.

    Views that read ``request.FILES`` directly bypass the checks a form's
    ``ImageField`` would do, so anything at all could be stored: the checkout's
    proof-of-payment field accepted ``shell.php`` from a visitor who was not
    even logged in. The format is taken from the file's CONTENT (decoded by
    Pillow), never from its name or the browser's content type, and the file is
    renamed to a random name with the matching extension — so nothing an
    uploader types ends up in a path, and a stored file can never carry an
    extension like ``.php`` or ``.html``.
    """
    if upload.size > MAX_IMAGE_UPLOAD_BYTES:
        return INVALID_IMAGE_MESSAGE
    try:
        with warnings.catch_warnings():
            # A decompression bomb is a warning by default; treat it as an error.
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            upload.seek(0)
            image = Image.open(upload)
            fmt = image.format
            image.verify()
    except Exception:
        return INVALID_IMAGE_MESSAGE
    finally:
        upload.seek(0)
    extension = _IMAGE_EXTENSIONS.get(fmt)
    if not extension:
        return INVALID_IMAGE_MESSAGE
    upload.name = uuid.uuid4().hex + extension
    return None


def admin_image_preview(file_field, empty_text='Nothing uploaded'):
    """Render an uploaded image for a Django admin change form.

    The thumbnail is capped so it does not blow out the form, and links to the
    original so staff can zoom in on an ID number. A field that points at a file
    which is no longer on disk says so plainly instead of showing a broken image
    — that distinction matters when deciding whether to reject a submission.

    Note ``/media/kyc/…``, ``/media/deposits/…`` and ``/media/course_purchases/…``
    are staff-only; see ``protected_media`` in ``config/urls.py``.
    """
    if not file_field:
        return empty_text
    try:
        exists = file_field.storage.exists(file_field.name)
    except OSError:
        exists = False
    if not exists:
        return format_html(
            '<span style="color:#b00;">File missing from storage:</span> <code>{}</code>',
            file_field.name,
        )
    return format_html(
        '<a href="{0}" target="_blank" rel="noopener" title="Open full size">'
        '<img src="{0}" style="max-width:480px;max-height:480px;border:1px solid #ddd;" />'
        '</a><br><a href="{0}" target="_blank" rel="noopener">Open full size</a>',
        file_field.url,
    )
