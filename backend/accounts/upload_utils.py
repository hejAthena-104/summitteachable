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

from django.utils.html import format_html

UPLOAD_FAILED_MESSAGE = (
    'We could not save your upload just now. Please try again in a moment — '
    'if it keeps happening, contact support.'
)


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
