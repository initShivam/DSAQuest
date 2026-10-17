from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from .tokens import email_verification_token_generator


def _frontend_link(path, query):
    return f"{settings.PUBLIC_FRONTEND_URL}/{path}?{urlencode(query)}"


def send_verification_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token_generator.make_token(user)
    link = _frontend_link("verify-email", {"uid": uid, "token": token})
    delivered = send_mail(
        "Verify your DSA Quest email",
        """Welcome to DSA Quest.

Verify your email address by opening this link:
{link}

This link expires in {hours} hours. If you did not create this account, you can ignore this email.
""".format(link=link, hours=settings.PASSWORD_RESET_TIMEOUT // 3600),
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
    if delivered != 1:
        raise EmailDeliveryError("The email backend accepted no recipients.")


def send_password_reset_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = _frontend_link("reset-password", {"uid": uid, "token": token})
    delivered = send_mail(
        "Reset your DSA Quest password",
        """A password reset was requested for your DSA Quest account.

Set a new password by opening this link:
{link}

This link expires in {hours} hours. If you did not request this, you can ignore this email.
""".format(link=link, hours=settings.PASSWORD_RESET_TIMEOUT // 3600),
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
    if delivered != 1:
        raise EmailDeliveryError("The email backend accepted no recipients.")
