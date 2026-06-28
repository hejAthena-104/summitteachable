from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import SetPasswordForm
from django.utils import timezone
from django.conf import settings
import random
from .forms import UserRegistrationForm, UserLoginForm
from .models import User, EmailVerificationToken, PasswordResetToken, LoginHistory, LoginCode
from .email_utils import EmailService


def login_view(request):
    """Handle user login"""
    # Redirect if already logged in
    if request.user.is_authenticated:
        return redirect('dashboard:index')  # We'll create this later

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me', False)

            # Authenticate user
            user = authenticate(request, username=username, password=password)

            if user is not None:
                # Email two-factor: don't log in yet — email a code and verify it.
                if user.two_factor_enabled:
                    code = ''.join(str(random.randint(0, 9)) for _ in range(6))
                    LoginCode.objects.create(user=user, code=code)
                    EmailService.send_login_code_email(user, code)
                    request.session['2fa_user_id'] = user.id
                    request.session['2fa_remember'] = remember_me
                    if settings.DEBUG:
                        messages.info(request, f'[LOCAL TEST] Your 2FA code is: {code}')
                    messages.info(request, 'We emailed you a 6-digit verification code to finish signing in.')
                    return redirect('accounts:two_factor_verify')

                login(request, user)

                # Set session expiry
                if not remember_me:
                    request.session.set_expiry(0)  # Session expires when browser closes
                else:
                    request.session.set_expiry(1209600)  # 2 weeks

                # Log login history
                ip_address = request.META.get('REMOTE_ADDR')
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                LoginHistory.objects.create(
                    user=user,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=True
                )

                # Send login alert email (optional - can be disabled)
                # EmailService.send_login_alert_email(user, ip_address, user_agent)

                messages.success(request, f'Welcome back, {user.get_full_name()}!')

                # Redirect to next page or dashboard
                next_url = request.GET.get('next', 'dashboard:index')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            # Check if username/email exists but password is wrong
            username = request.POST.get('username')
            if User.objects.filter(username=username).exists() or User.objects.filter(email=username).exists():
                messages.error(request, 'Invalid password. Please try again.')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()

    return render(request, 'auth/login.html', {'form': form})


def login_code_request(request):
    """Passwordless login — step 1: email a one-time code.

    Always shows a generic success message (no account enumeration). Used by
    course buyers (who have no password) and anyone who prefers a code."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip().lower()
        user = User.objects.filter(email=email).first()
        if user:
            code = ''.join(str(random.randint(0, 9)) for _ in range(6))
            LoginCode.objects.create(user=user, code=code)
            EmailService.send_login_code_email(user, code)
            # Local-only testing aid: surface the code on screen when DEBUG.
            if settings.DEBUG:
                messages.info(request, f'[LOCAL TEST] Login code for {email}: {code}')
        request.session['login_code_email'] = email
        messages.success(request, 'If that email is registered, we just sent it a 6-digit login code.')
        return redirect('accounts:login_code_verify')

    return render(request, 'auth/login-code-request.html')


def login_code_verify(request):
    """Passwordless login — step 2: enter the code and sign in."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    email = request.session.get('login_code_email', '')

    if request.method == 'POST':
        email = (request.POST.get('email') or email or '').strip().lower()
        code = (request.POST.get('code') or '').strip()
        user = User.objects.filter(email=email).first()
        login_code = None
        if user:
            login_code = (
                LoginCode.objects.filter(user=user, code=code, is_used=False)
                .order_by('-created_at').first()
            )
        if login_code and login_code.is_valid():
            login_code.mark_as_used()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            LoginHistory.objects.create(
                user=user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                success=True,
            )
            request.session.pop('login_code_email', None)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('dashboard:index')
        messages.error(request, 'That code is invalid or has expired. Request a new one.')

    return render(request, 'auth/login-code-verify.html', {'email': email})


def two_factor_verify(request):
    """Second step of login for accounts with email 2FA: enter the emailed code."""
    user_id = request.session.get('2fa_user_id')
    if not user_id:
        return redirect('accounts:login')
    user = User.objects.filter(pk=user_id).first()
    if not user:
        request.session.pop('2fa_user_id', None)
        return redirect('accounts:login')

    if request.method == 'POST':
        code = (request.POST.get('code') or '').strip()
        login_code = (
            LoginCode.objects.filter(user=user, code=code, is_used=False)
            .order_by('-created_at').first()
        )
        if login_code and login_code.is_valid():
            login_code.mark_as_used()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            request.session.set_expiry(1209600 if request.session.pop('2fa_remember', False) else 0)
            request.session.pop('2fa_user_id', None)
            LoginHistory.objects.create(
                user=user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                success=True,
            )
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('dashboard:index')
        messages.error(request, 'That code is invalid or has expired.')

    return render(request, 'auth/two-factor-verify.html', {'email': user.email})


def register_view(request):
    """Handle user registration"""
    # Redirect if already logged in
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)

        if form.is_valid():
            # Create user
            user = form.save()

            # Create verification token
            verification_token = EmailVerificationToken.objects.create(user=user)

            # Send verification email
            email_sent = EmailService.send_verification_email(user, str(verification_token.token))

            # Store email in session for the verification page
            request.session['verification_email'] = user.email
            request.session['user_name'] = user.get_full_name()

            if email_sent:
                messages.success(
                    request,
                    f'Account created successfully! Please check your email to verify your account.'
                )
            else:
                messages.warning(
                    request,
                    f'Account created but we could not send the verification email. Please contact support.'
                )

            # Redirect to verification waiting page (NOT logging in yet)
            return redirect('accounts:verify_email_sent')
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = UserRegistrationForm()

    return render(request, 'auth/register.html', {'form': form})


def forgot_password_view(request):
    """Handle password reset request"""
    if request.method == 'POST':
        email = request.POST.get('email')

        # Check if email exists
        try:
            user = User.objects.get(email=email)

            # Create password reset token
            reset_token = PasswordResetToken.objects.create(user=user)

            # Send password reset email
            EmailService.send_password_reset_email(user, str(reset_token.token))

        except User.DoesNotExist:
            pass  # Don't reveal if email doesn't exist

        # Always show same message (security best practice)
        messages.success(
            request,
            'If an account with this email exists, you will receive password reset instructions shortly.'
        )

        return redirect('accounts:login')

    return render(request, 'auth/forgot-password.html')


def verify_email_view(request, token):
    """Handle email verification"""
    try:
        verification_token = EmailVerificationToken.objects.get(token=token)

        if verification_token.is_valid():
            user = verification_token.user
            user.is_verified = True
            user.save()

            verification_token.mark_as_used()

            # Send welcome email
            EmailService.send_welcome_email(user)

            messages.success(
                request,
                'Your email has been verified successfully! You can now login to access your dashboard.'
            )

            # Store user info for success page
            request.session['verified_user_name'] = user.get_full_name()
            request.session['verified_user_email'] = user.email

            # Redirect to success page (will auto-redirect to login)
            return render(request, 'auth/verify-email-success.html', {'user': user})
        else:
            messages.error(
                request,
                'This verification link has expired or been used. Please request a new one.'
            )
            return redirect('accounts:login')

    except EmailVerificationToken.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('accounts:login')


def reset_password_view(request, token):
    """Handle password reset"""
    try:
        reset_token = PasswordResetToken.objects.get(token=token)

        if not reset_token.is_valid():
            messages.error(
                request,
                'This password reset link has expired or been used. Please request a new one.'
            )
            return redirect('accounts:forgot_password')

        if request.method == 'POST':
            form = SetPasswordForm(reset_token.user, request.POST)

            if form.is_valid():
                form.save()
                reset_token.mark_as_used()

                messages.success(
                    request,
                    'Your password has been reset successfully. You can now log in with your new password.'
                )
                return redirect('accounts:login')
        else:
            form = SetPasswordForm(reset_token.user)

        return render(request, 'auth/reset-password.html', {
            'form': form,
            'token': token
        })

    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Invalid password reset link.')
        return redirect('accounts:forgot_password')


@require_POST
@login_required
def logout_view(request):
    """Handle user logout. POST-only so a GET (e.g. an <img> tag) can't force a
    logout (logout-CSRF). All sign-out controls submit a CSRF-protected form."""
    user_name = request.user.get_full_name()
    logout(request)
    messages.success(request, f'Goodbye, {user_name}! You have been logged out successfully.')
    return redirect('accounts:login')


def verify_email_sent_view(request):
    """Show verification email sent page"""
    email = request.session.get('verification_email', '')
    user_name = request.session.get('user_name', '')

    if not email:
        # If no email in session, redirect to register
        return redirect('accounts:register')

    return render(request, 'auth/verify-email-sent.html', {
        'email': email,
        'user_name': user_name
    })


def resend_verification_email(request):
    """Resend verification email to user"""
    # Get email from session or logged in user
    if request.user.is_authenticated:
        user = request.user
    else:
        email = request.session.get('verification_email')
        if not email:
            messages.error(request, 'Please register first.')
            return redirect('accounts:register')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('accounts:register')

    if user.is_verified:
        messages.info(request, 'Your email is already verified.')
        return redirect('accounts:login')

    # Invalidate old tokens
    EmailVerificationToken.objects.filter(user=user, is_used=False).update(is_used=True)

    # Create new token
    verification_token = EmailVerificationToken.objects.create(user=user)

    # Send verification email
    EmailService.send_verification_email(user, str(verification_token.token))

    messages.success(request, 'Verification email sent! Please check your inbox.')
    return redirect('accounts:verify_email_sent')


# Backend authentication (allows login with email)
class EmailOrUsernameModelBackend:
    """
    Custom authentication backend that allows users to log in with either username or email
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to fetch the user by email first
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            try:
                # Try to fetch the user by username
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None

        # Check password
        if user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
