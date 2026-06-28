"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import posixpath

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponseForbidden
from django.views.static import serve as _serve_media

# Media paths that contain personal documents / payment proofs — only staff may view.
_PRIVATE_MEDIA_PREFIXES = ('kyc/', 'deposits/', 'course_purchases/')


def protected_media(request, path):
    """Serve uploaded media in production. Sensitive uploads (KYC documents,
    payment proofs) are restricted to staff; the rest (icons, QR codes, avatars)
    are public.

    The prefix check runs on the NORMALISED path so it can't be bypassed with
    traversal tricks like ``/media/x/../kyc/...`` or a leading slash."""
    normalized = posixpath.normpath('/' + path).lstrip('/')
    if normalized.startswith(_PRIVATE_MEDIA_PREFIXES):
        if not (request.user.is_authenticated and request.user.is_staff):
            return HttpResponseForbidden("You do not have permission to view this file.")
    return _serve_media(request, normalized, document_root=settings.MEDIA_ROOT)


urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication URLs
    path('auth/', include('accounts.urls')),

    # Dashboard URLs
    path('dashboard/', include('dashboard.urls')),

    # Feature apps
    path('education/', include('education.urls')),
    path('analysis/', include('analysis.urls')),
    path('copy-trading/', include('copytrading.urls')),
    path('news/', include('news.urls')),

    # Public course storefront (real course sales)
    path('buy/', include('store.urls')),
]

# Serve uploaded media. In DEBUG, Django's static helper serves both media + static.
# In production WhiteNoise serves static, but media must be served explicitly — the
# protected_media view does this (with staff-only gating for sensitive uploads).
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', protected_media),
]
