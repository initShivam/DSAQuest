import logging
import socket
import smtplib
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from .tokens import email_verification_token_generator

logger = logging.getLogger(__name__)

class EmailDeliveryError(Exception):
    """Raised when the email backend accepts no recipients."""
    pass

def _frontend_link(path, query):
    return f"{settings.PUBLIC_FRONTEND_URL}/{path}?{urlencode(query)}"

def _send_email_with_error_handling(subject, message, recipient_list, email_type):
    """
    Internal helper to send emails with consistent error handling and logging.
    """
    logger.info(f"Attempting to send {email_type} email to {recipient_list[0]} using backend {settings.EMAIL_BACKEND}")

    try:
        delivered = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False,
        )
        if delivered != 1:
            logger.error(f"{email_type} delivery failed: {delivered} recipients accepted for {recipient_list[0]}")
            raise EmailDeliveryError(f"The email backend accepted no recipients for {email_type}.")

        logger.info(f"{email_type} email successfully delivered to {recipient_list[0]}")
        return delivered

    except (socket.timeout, smtplib.SMTPConnectError, smtplib.SMTPException, OSError) as e:
        logger.exception(f"Network or SMTP error during {email_type} to {recipient_list[0]}: {type(e).__name__}: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during {email_type} to {recipient_list[0]}: {type(e).__name__}: {e}")
        raise

def send_verification_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token_generator.make_token(user)
    link = _frontend_link("verify-email", {"uid": uid, "token": token})

    subject = "Verify your DSA Quest email"
    message = f"""Welcome to DSA Quest.

Verify your email address by opening this link:
{link}

This link expires in {settings.PASSWORD_RESET_TIMEOUT // 3600} hours. If you did not create this account, you can ignore this email."""

    return _send_email_with_error_handling(
        subject,
        message,
        [user.email],
        "verification"
    )

def send_password_reset_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = _frontend_link("reset-password", {"uid": uid, "token": token})

    subject = "Reset your DSA Quest password"
    message = f"""A password reset was requested for your DSA Quest account.

Set your password by opening this link:
{link}

This link expires in {settings.PASSWORD_RESET_TIMEOUT // 3600} hours. If you did not request this, you can ignore this email."""

    return _send_email_with_error_handling(
        subject,
        message,
        [user.email],
        "password reset"
    )
