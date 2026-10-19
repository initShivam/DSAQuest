"""Django email transport for Brevo's documented transactional HTTPS API.

Only provider acceptance is recorded here, not inbox delivery. No request bodies,
response bodies, authorization headers, or raw exceptions may be logged.
"""

import logging
from email.utils import parseaddr

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

from .emailing import EmailDeliveryError


logger = logging.getLogger(__name__)
BREVO_SEND_URL = "https://api.brevo.com/v3/smtp/email"


def _address(value):
    name, address = parseaddr(value)
    if not address:
        raise EmailDeliveryError("Email address is not configured correctly.")
    return {"email": address, **({"name": name} if name else {})}


class BrevoEmailBackend(BaseEmailBackend):
    """Send the project's account emails over HTTPS rather than blocked SMTP."""

    def send_messages(self, email_messages):
        accepted = 0
        for message in email_messages or []:
            if not message.recipients():
                continue
            try:
                self._send(message)
            except EmailDeliveryError:
                if not self.fail_silently:
                    raise
            else:
                accepted += 1
        return accepted

    def _send(self, message):
        api_key = settings.BREVO_API_KEY.strip()
        if not api_key or not message.from_email:
            logger.error("Email submission failed: provider=brevo reason=missing_configuration")
            raise EmailDeliveryError("Email provider is not configured.")

        # Retain Django's header-injection checks before serializing addresses.
        message.message()
        if message.attachments or getattr(message, "alternatives", None):
            raise EmailDeliveryError("This email transport does not support attachments or multipart email.")

        payload = {
            "sender": _address(message.from_email),
            "subject": message.subject,
            "htmlContent" if message.content_subtype == "html" else "textContent": message.body,
        }
        for field in ("to", "cc", "bcc"):
            addresses = getattr(message, field)
            if addresses:
                payload[field] = [_address(address) for address in addresses]
        if message.reply_to:
            payload["replyTo"] = _address(message.reply_to[0])

        # No redirects (which could leak the API key) and no automatic POST retries.
        try:
            response = requests.post(
                BREVO_SEND_URL,
                json=payload,
                headers={"api-key": api_key, "accept": "application/json", "content-type": "application/json"},
                timeout=settings.EMAIL_TIMEOUT,
                allow_redirects=False,
            )
        except requests.Timeout:
            logger.error("Email submission failed: provider=brevo reason=timeout acceptance=unknown")
            raise EmailDeliveryError("Email provider request timed out.") from None
        except requests.RequestException:
            logger.error("Email submission failed: provider=brevo reason=connection_error acceptance=unknown")
            raise EmailDeliveryError("Email provider could not be reached.") from None

        # HTTP 201 is the documented response for immediate transactional submission.
        # A generic 2xx or the public API's HTTP 200 is not evidence of acceptance.
        if response.status_code != 201:
            logger.error("Email submission failed: provider=brevo http_status=%s", response.status_code)
            raise EmailDeliveryError("Email provider did not accept the message.")

        try:
            result = response.json()
        except ValueError:
            result = None
        if not isinstance(result, dict) or not isinstance(result.get("messageId"), str) or not result["messageId"].strip():
            logger.error("Email submission failed: provider=brevo reason=invalid_response acceptance=unknown")
            raise EmailDeliveryError("Email provider returned an invalid acknowledgement.")

        logger.info("Email submission accepted: provider=brevo http_status=201")
