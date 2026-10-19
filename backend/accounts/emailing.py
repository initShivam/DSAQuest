import logging
import socket
import smtplib
from abc import ABC, abstractmethod
from urllib.parse import urlencode

import requests

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from .tokens import email_verification_token_generator

logger = logging.getLogger(__name__)

class EmailDeliveryError(Exception):
    """Raised when the email backend accepts no recipients or API fails."""
    pass

class BaseEmailProvider(ABC):
    @abstractmethod
    def send(self, subject, message, recipient_list):
        pass

class SMTPProvider(BaseEmailProvider):
    def send(self, subject, message, recipient_list):
        delivered = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False,
        )
        if delivered != 1:
            raise EmailDeliveryError(f"SMTP backend accepted {delivered} recipients, expected 1.")
        return delivered

class ResendProvider(BaseEmailProvider):
    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        self.api_url = "https://api.resend.com/emails"

    def send(self, subject, message, recipient_list):
        if not self.api_key:
            raise EmailDeliveryError("Resend API key is missing.")

        try:
            payload = {
                "from": settings.DEFAULT_FROM_EMAIL,
                "to": recipient_list[0],
                "subject": subject,
                "html": message.replace("\n", "<br>"),
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            return 1

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "Unknown"
            logger.error(f"Resend API HTTP Error {status_code} for {recipient_list[0]}: {e}")
            raise EmailDeliveryError(f"Resend API error ({status_code})")
        except requests.exceptions.RequestException as e:
            logger.exception(f"Network error calling Resend API for {recipient_list[0]}: {e}")
            raise EmailDeliveryError(f"Network error calling Resend API")
        except Exception as e:
            logger.exception(f"Unexpected error during Resend API call for {recipient_list[0]}: {e}")
            raise EmailDeliveryError(f"Unexpected error calling Resend API")

def get_email_provider():
    provider = settings.EMAIL_PROVIDER.lower()
    if provider == "resend":
        return ResendProvider()
    # Default to SMTP (which includes Django's locmem/console backends)
    return SMTPProvider()

def _frontend_link(path, query):
    return f"{settings.PUBLIC_FRONTEND_URL}/{path}?{urlencode(query)}"

def _send_email_with_error_handling(subject, message, recipient_list, email_type):
    """
    Internal helper to send emails with consistent error handling and logging.
    """
    logger.info(f"Attempting to send {email_type} email to {recipient_list[0]} using provider {settings.EMAIL_PROVIDER}")

    try:
        provider = get_email_provider()
        delivered = provider.send(subject, message, recipient_list)
        logger.info(f"{email_type} email successfully delivered to {recipient_list[0]}")
        return delivered

    except (socket.timeout, smtplib.SMTPConnectError, smtplib.SMTPException, OSError) as e:
        logger.exception(f"Network or SMTP error during {email_type} to {recipient_list[0]}: {type(e).__name__}: {e}")
        raise
    except EmailDeliveryError as e:
        logger.error(f"Delivery error during {email_type} to {recipient_list[0]}: {e}")
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
