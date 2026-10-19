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
    """Raised when Django cannot deliver an email."""

    pass


SMTP_EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"


def _recipient_domain(recipient_list):
    if not recipient_list or "@" not in recipient_list[0]:
        return "unknown"
    return recipient_list[0].rsplit("@", 1)[-1]


def _validate_email_configuration():
    """Validate runtime email settings without exposing credential values."""
    if settings.EMAIL_USE_TLS and settings.EMAIL_USE_SSL:
        raise EmailDeliveryError("Email delivery is not configured correctly.")

    if settings.EMAIL_BACKEND != SMTP_EMAIL_BACKEND:
        return

    missing = [
        name
        for name, value in (
            ("EMAIL_HOST", settings.EMAIL_HOST),
            ("EMAIL_HOST_USER", settings.EMAIL_HOST_USER),
            ("EMAIL_HOST_PASSWORD", settings.EMAIL_HOST_PASSWORD),
            ("DEFAULT_FROM_EMAIL", settings.DEFAULT_FROM_EMAIL),
        )
        if not value
    ]
    if missing:
        logger.error("Email delivery is unavailable; missing setting(s): %s", ", ".join(missing))
        raise EmailDeliveryError("Email delivery is not configured.")


def _frontend_link(path, query):
    return f"{settings.PUBLIC_FRONTEND_URL}/{path}?{urlencode(query)}"

def _send_email_with_error_handling(subject, message, recipient_list, email_type):
    """
    Internal helper to send emails with consistent error handling and logging.
    """
    if not recipient_list:
        raise EmailDeliveryError("Email delivery has no recipient.")

    recipient_domain = _recipient_domain(recipient_list)
    logger.info(
        "Attempting to send %s email using backend=%s host=%s recipient_domain=%s",
        email_type,
        settings.EMAIL_BACKEND,
        settings.EMAIL_HOST,
        recipient_domain,
    )

    try:
        _validate_email_configuration()
        delivered = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False,
        )
        if delivered != len(recipient_list):
            logger.error(
                "%s email backend accepted %s of %s recipient(s), recipient_domain=%s",
                email_type,
                delivered,
                len(recipient_list),
                recipient_domain,
            )
            raise EmailDeliveryError("Email delivery was not accepted.")

        logger.info("%s email successfully delivered, recipient_domain=%s", email_type, recipient_domain)
        return delivered

    except EmailDeliveryError:
        raise
    except (socket.timeout, TimeoutError, smtplib.SMTPException, OSError) as error:
        logger.exception(
            "SMTP delivery failed for %s email, recipient_domain=%s, error_type=%s",
            email_type,
            recipient_domain,
            type(error).__name__,
        )
        raise EmailDeliveryError("Email delivery failed. Please try again later.") from error
    except Exception as error:
        logger.exception(
            "Unexpected email delivery failure for %s email, recipient_domain=%s, error_type=%s",
            email_type,
            recipient_domain,
            type(error).__name__,
        )
        raise EmailDeliveryError("Email delivery failed. Please try again later.") from error

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
