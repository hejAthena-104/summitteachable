from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('login-code/', views.login_code_request, name='login_code_request'),
    path('login-code/verify/', views.login_code_verify, name='login_code_verify'),
    path('two-factor/verify/', views.two_factor_verify, name='two_factor_verify'),
    path('register/', views.register_view, name='register'),
    path('verify-email-sent/', views.verify_email_sent_view, name='verify_email_sent'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/<uuid:token>/', views.reset_password_view, name='reset_password'),
    path('verify-email/<uuid:token>/', views.verify_email_view, name='verify_email'),
    path('resend-verification/', views.resend_verification_email, name='resend_verification'),
    path('logout/', views.logout_view, name='logout'),
]
