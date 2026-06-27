"""Public course storefront views."""
from decimal import Decimal, InvalidOperation
import base64
import io
import random

from django.contrib import messages
from django.shortcuts import get_object_or_404, render

from accounts.models import User, EmailVerificationToken, LoginCode
from accounts.email_utils import EmailService
from education.models import Course
from transactions.models import PaymentMethod

from .models import CoursePurchase


def _unique_username(email):
    base = (email.split('@')[0] or 'learner')[:140]
    username = base
    i = 1
    while User.objects.filter(username=username).exists():
        username = f'{base}{i}'
        i += 1
    return username


# Map an admin PaymentMethod name to a crypto symbol + network label so the
# checkout can show the right logo and a generated QR. Falls back gracefully.
_CRYPTO = {
    'usdt': ('usdt', 'USDT'), 'tether': ('usdt', 'USDT'),
    'bitcoin': ('btc', 'Bitcoin'), 'btc': ('btc', 'Bitcoin'),
    'ethereum': ('eth', 'Ethereum'), 'eth': ('eth', 'Ethereum'),
    'litecoin': ('ltc', 'Litecoin'), 'ltc': ('ltc', 'Litecoin'),
    'usdc': ('usdc', 'USDC'), 'bnb': ('bnb', 'BNB'), 'tron': ('trx', 'Tron'), 'trx': ('trx', 'Tron'),
}


def _qr_data_uri(text):
    """Generate a QR PNG data URI for a wallet address (server-side, no CDN)."""
    if not text:
        return ''
    try:
        import qrcode
        img = qrcode.make(text)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ''


def _enrich_methods(pay_methods):
    """Build template/JS-friendly payment options with logo, symbol + QR."""
    out = []
    for pm in pay_methods:
        sym, net = _CRYPTO.get(pm.name.strip().lower(), ('', pm.name))
        addr = pm.wallet_address or ''
        out.append({
            'name': pm.name,
            'symbol': sym,
            'network': net,
            'address': addr,
            'logo': f'https://cdn.jsdelivr.net/npm/cryptocurrency-icons@0.18.1/svg/color/{sym}.svg' if sym else '',
            'icon_url': pm.icon.url if pm.icon else '',
            # Prefer an admin-uploaded QR; otherwise generate one from the address.
            'qr': pm.qr_code.url if pm.qr_code else _qr_data_uri(addr),
        })
    return out


def _ctx(course, pay_methods, request):
    # Curriculum preview — module titles + lesson titles/durations. Shown locked
    # (only is_preview lessons are watchable) so buyers see the full value.
    modules = list(course.modules.prefetch_related('lessons').all())
    return {
        'course': course,
        'pay_methods': pay_methods,
        'methods': _enrich_methods(pay_methods),
        'modules': modules,
        'form': request.POST if request.method == 'POST' else {},
    }


def catalog(request):
    """Public list of purchasable courses."""
    courses = Course.objects.filter(is_published=True)
    return render(request, 'store/catalog.html', {'courses': courses})


def checkout(request, slug):
    """Show a course + crypto payment details, and take a purchase submission."""
    course = get_object_or_404(Course, slug=slug, is_published=True)
    pay_methods = PaymentMethod.objects.filter(
        is_active=True, type__in=['deposit', 'both'],
    ).order_by('order')

    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip().lower()
        name = (request.POST.get('name') or '').strip()
        phone = (request.POST.get('phone') or '').strip()
        country = (request.POST.get('country') or '').strip()
        method = (request.POST.get('payment_method') or '').strip()
        tx_reference = (request.POST.get('tx_reference') or '').strip()
        proof = request.FILES.get('proof_image')

        try:
            amount = Decimal(request.POST.get('amount') or course.price or '0')
        except (InvalidOperation, TypeError):
            amount = course.price or Decimal('0')

        if not email:
            messages.error(request, 'Please enter your email address.')
            return render(request, 'store/checkout.html', _ctx(course, pay_methods, request))
        if not proof:
            messages.error(request, 'Please attach your proof of payment.')
            return render(request, 'store/checkout.html', _ctx(course, pay_methods, request))

        # Create or fetch the buyer's account (passwordless — they log in by code).
        user, created = User.objects.get_or_create(
            email=email,
            defaults={'username': _unique_username(email)},
        )
        if created:
            first, _, last = name.partition(' ')
            user.first_name = first
            user.last_name = last
            user.set_unusable_password()
            user.is_verified = False
        if phone and not user.phone:
            user.phone = phone
        if country and not user.country:
            user.country = country
        user.save()

        purchase = CoursePurchase.objects.create(
            user=user, course=course,
            buyer_email=email, buyer_name=name, buyer_phone=phone, buyer_country=country,
            amount=amount, payment_method=method, tx_reference=tx_reference, proof_image=proof,
            status='pending',
        )

        # Verify their email using the EXISTING verification flow.
        if not user.is_verified:
            token = EmailVerificationToken.objects.create(user=user)
            EmailService.send_verification_email(user, str(token.token))

        # Passwordless login code so they can log in to track status.
        code = ''.join(str(random.randint(0, 9)) for _ in range(6))
        LoginCode.objects.create(user=user, code=code)
        EmailService.send_login_code_email(user, code)

        # Purchase-received confirmation email.
        EmailService.send_course_purchase_received_email(purchase)

        return render(request, 'store/confirm.html',
                      {'course': course, 'purchase': purchase, 'email': email})

    return render(request, 'store/checkout.html', _ctx(course, pay_methods, request))
