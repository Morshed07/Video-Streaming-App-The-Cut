from django.template.loader import render_to_string
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from .models import OtpLog, User
from django.core.mail import EmailMessage


def get_tokens_for_user(user):
    """Manually generate JWT tokens."""
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


def send_otp_email(user: User):
    otp_obj = OtpLog.objects.create(user=user)
    otp_code = otp_obj.generate_otp()
    html_message = render_to_string(
        'email/otp_email.html',
        {'otp': otp_code, 'user': user}
    )

    email = EmailMessage(
        subject='You requested a password reset OTP',
        body=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email]
    )
    email.content_subtype = 'html'
    return email.send()