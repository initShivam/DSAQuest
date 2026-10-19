import io
import logging
import os
import runpy
import traceback
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMessage, get_connection
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from requests.exceptions import ConnectionError as RequestsConnectionError, Timeout
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.email_backends import BrevoEmailBackend
from accounts.emailing import EmailDeliveryError
from accounts.models import User
from accounts.tokens import email_verification_token_generator


BREVO_URL = "https://api.brevo.com/v3/smtp/email"
API_KEY = "test-only-brevo-key-DO-NOT-LOG-123"
SENSITIVE_TOKEN = "synthetic-token-DO-NOT-LOG-456"
RESET_URL = f"https://frontend.example.test/reset-password?uid=dGVzdA&token={SENSITIVE_TOKEN}"
UNSAFE_DETAIL = f"unsafe-provider-detail api-key={API_KEY} token={SENSITIVE_TOKEN} reset={RESET_URL}"
RESEND_DETAIL = "If an account needs verification, a new email will arrive shortly."
RESET_DETAIL = "If an account exists for that email, a reset link will arrive shortly."
REGISTRATION_FAILURE = "We couldn't send the verification email. Please try again later."
PASSWORD = "strong-password-123"
BREVO_SETTINGS = {
    "EMAIL_BACKEND": "accounts.email_backends.BrevoEmailBackend",
    "BREVO_API_KEY": API_KEY,
    "DEFAULT_FROM_EMAIL": "DSA Quest <sender@example.com>",
    "EMAIL_TIMEOUT": 7,
    "EMAIL_HOST_USER": "",
    "EMAIL_HOST_PASSWORD": "",
    "EMAIL_USE_TLS": False,
    "EMAIL_USE_SSL": False,
    "PUBLIC_FRONTEND_URL": "https://frontend.example.test",
    "CACHES": {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "brevo-email-delivery-tests",
        }
    },
}


def provider_response(status_code=201):
    response = Mock(status_code=status_code)
    response.json.return_value = {"messageId": "<accepted-message@example.com>"}
    response.text = UNSAFE_DETAIL
    response.content = UNSAFE_DETAIL.encode()
    response.headers = {"Location": RESET_URL}
    return response


class BrevoTestSupport:
    def setUp(self):
        super().setUp()
        cache.clear()
        self.addCleanup(cache.clear)
        post_patch = patch("accounts.email_backends.requests.post")
        self.post = post_patch.start()
        self.addCleanup(post_patch.stop)
        self.post.return_value = provider_response()

        self.log_output = io.StringIO()
        accounts_logger = logging.getLogger("accounts")
        handler = logging.StreamHandler(self.log_output)
        previous_level = accounts_logger.level
        accounts_logger.setLevel(logging.INFO)
        accounts_logger.addHandler(handler)
        self.addCleanup(accounts_logger.setLevel, previous_level)
        self.addCleanup(accounts_logger.removeHandler, handler)

    def clear_logs(self):
        self.log_output.seek(0)
        self.log_output.truncate(0)

    def assert_no_sensitive_output(self, output, *extra_values):
        for value in (API_KEY, SENSITIVE_TOKEN, RESET_URL, "unsafe-provider-detail", *extra_values):
            self.assertNotIn(value, output)

    def assert_safe_failure_logs(self):
        output = self.log_output.getvalue()
        self.assert_no_sensitive_output(output)
        self.assertNotRegex(
            output.lower(), r"\bsuccess(?:ful(?:ly)?)?\b|\b(?:email|message)\s+(?:was\s+)?(?:sent|delivered)\b"
        )

    def assert_delivery_failure(self, operation):
        self.clear_logs()
        with self.assertRaises(EmailDeliveryError) as caught:
            operation()
        error = caught.exception
        self.assertTrue(str(error))
        self.assertIsNone(error.__cause__)
        self.assertTrue(error.__context__ is None or error.__suppress_context__)
        self.assert_no_sensitive_output(
            "".join(traceback.format_exception(type(error), error, error.__traceback__))
        )
        self.assert_safe_failure_logs()
        return str(error)

    def message(self, **kwargs):
        return EmailMessage("Test subject", f"Plain text message\n{RESET_URL}", to=["player@example.com"], **kwargs)


@override_settings(**BREVO_SETTINGS)
class BrevoEmailBackendTests(BrevoTestSupport, SimpleTestCase):
    def test_email_backend_setting_selects_brevo_or_existing_smtp(self):
        connection = get_connection()
        self.assertIsInstance(connection, BrevoEmailBackend)
        self.assertIsInstance(connection, BaseEmailBackend)
        with override_settings(EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"):
            self.assertIsInstance(get_connection(), SMTPEmailBackend)
        self.post.assert_not_called()

    def test_accepted_message_uses_exact_brevo_request_and_sender_format(self):
        for sender, expected_sender in (
            ("sender@example.com", {"email": "sender@example.com"}),
            ("DSA Quest <sender@example.com>", {"email": "sender@example.com", "name": "DSA Quest"}),
        ):
            with self.subTest(sender=sender), override_settings(DEFAULT_FROM_EMAIL=sender):
                self.post.reset_mock()
                message = self.message()
                self.assertEqual(get_connection().send_messages([message]), 1)
                self.post.assert_called_once_with(
                    BREVO_URL,
                    json={
                        "sender": expected_sender,
                        "to": [{"email": "player@example.com"}],
                        "subject": message.subject,
                        "textContent": message.body,
                    },
                    headers={"api-key": API_KEY, "accept": "application/json", "content-type": "application/json"},
                    timeout=7,
                    allow_redirects=False,
                )
                self.assert_no_sensitive_output(self.log_output.getvalue())

    def test_count_is_messages_rather_than_recipients(self):
        first = EmailMessage("First", "First body", to=["one@example.com", "two@example.com"])
        second = EmailMessage("Second", "Second body", to=["three@example.com"])

        self.assertEqual(get_connection().send_messages([first, second]), 2)
        self.assertEqual(self.post.call_count, 2)
        self.assertEqual(
            [call.kwargs["json"]["to"] for call in self.post.call_args_list],
            [[{"email": "one@example.com"}, {"email": "two@example.com"}], [{"email": "three@example.com"}]],
        )
        self.assertEqual([call.kwargs["json"]["subject"] for call in self.post.call_args_list], ["First", "Second"])

    def test_empty_message_batch_never_calls_provider(self):
        for messages in (None, []):
            with self.subTest(messages=messages):
                self.assertEqual(get_connection().send_messages(messages), 0)
        self.post.assert_not_called()

    def test_provider_rejections_raise_a_fixed_sanitized_error(self):
        for status_code in (400, 401, 403, 429, 500):
            errors = []
            for detail in ("safe-provider-detail", UNSAFE_DETAIL):
                with self.subTest(status_code=status_code, detail_is_sensitive=detail == UNSAFE_DETAIL):
                    self.post.reset_mock()
                    response = provider_response(status_code)
                    response.json.return_value = {"code": "provider_error", "message": detail}
                    response.text = detail
                    self.post.return_value = response
                    errors.append(self.assert_delivery_failure(lambda: get_connection().send_messages([self.message()])))
                    self.post.assert_called_once()
                    self.assertNotIn(detail, errors[-1])
                    self.assertNotIn(detail, self.log_output.getvalue())
            self.assertEqual(len(set(errors)), 1)

    def test_other_success_codes_and_redirects_are_not_provider_acceptance(self):
        for status_code in (200, 202, 204, 301, 302, 307, 308):
            with self.subTest(status_code=status_code):
                self.post.reset_mock()
                self.post.return_value = provider_response(status_code)
                self.assert_delivery_failure(lambda: get_connection().send_messages([self.message()]))
                self.post.assert_called_once()
                self.assertIs(self.post.call_args.kwargs["allow_redirects"], False)

    def test_timeout_and_network_errors_are_sanitized_without_exception_chains(self):
        for exception_type in (Timeout, RequestsConnectionError):
            errors = []
            for detail in ("safe-network-detail", UNSAFE_DETAIL):
                with self.subTest(exception=exception_type.__name__, detail_is_sensitive=detail == UNSAFE_DETAIL):
                    self.post.reset_mock()
                    self.post.side_effect = exception_type(detail)
                    errors.append(self.assert_delivery_failure(lambda: get_connection().send_messages([self.message()])))
                    self.post.assert_called_once()
                    self.assertNotIn(detail, errors[-1])
                    self.assertNotIn(detail, self.log_output.getvalue())
            self.assertEqual(len(set(errors)), 1)

    def test_201_with_malformed_json_is_not_accepted(self):
        errors = []
        for detail in ("safe-json-detail", UNSAFE_DETAIL):
            with self.subTest(detail_is_sensitive=detail == UNSAFE_DETAIL):
                self.post.reset_mock()
                response = provider_response()
                response.json.side_effect = ValueError(detail)
                self.post.return_value = response
                errors.append(self.assert_delivery_failure(lambda: get_connection().send_messages([self.message()])))
                self.post.assert_called_once()
                self.assertNotIn(detail, errors[-1])
                self.assertNotIn(detail, self.log_output.getvalue())
        self.assertEqual(len(set(errors)), 1)

    def test_201_requires_a_nonempty_string_message_id(self):
        payloads = (
            None, [], UNSAFE_DETAIL, {}, {"messageId": None}, {"messageId": ""},
            {"messageId": 123}, {"messageId": False}, {"messageId": []}, {"messageId": {}},
        )
        for payload in payloads:
            with self.subTest(payload_type=type(payload).__name__, payload=payload):
                self.post.reset_mock()
                response = provider_response()
                response.json.return_value = payload
                self.post.return_value = response
                self.assert_delivery_failure(lambda: get_connection().send_messages([self.message()]))
                self.post.assert_called_once()

    def test_missing_credentials_fail_before_any_network_request(self):
        for missing in ({"BREVO_API_KEY": ""}, {"DEFAULT_FROM_EMAIL": ""}):
            with self.subTest(missing=next(iter(missing))), override_settings(**missing):
                self.assert_delivery_failure(lambda: get_connection().send_messages([self.message()]))
                self.post.assert_not_called()

    def test_fail_silently_returns_zero_for_unaccepted_or_failed_delivery(self):
        invalid_json = provider_response()
        invalid_json.json.side_effect = ValueError(UNSAFE_DETAIL)
        for failure in (provider_response(403), Timeout(UNSAFE_DETAIL), RequestsConnectionError(UNSAFE_DETAIL), invalid_json):
            with self.subTest(failure_type=type(failure).__name__):
                self.post.reset_mock()
                self.clear_logs()
                self.post.side_effect = [failure]
                self.assertEqual(get_connection(fail_silently=True).send_messages([self.message()]), 0)
                self.post.assert_called_once()
                self.assert_safe_failure_logs()

        self.post.reset_mock()
        self.clear_logs()
        with override_settings(BREVO_API_KEY=""):
            self.assertEqual(get_connection(fail_silently=True).send_messages([self.message()]), 0)
        self.post.assert_not_called()
        self.assert_safe_failure_logs()

    def test_fail_silently_counts_only_accepted_messages_in_a_batch(self):
        self.post.side_effect = [provider_response(), provider_response(403), provider_response()]

        self.assertEqual(get_connection(fail_silently=True).send_messages([self.message()] * 3), 2)
        self.assertEqual(self.post.call_count, 3)
        self.assert_no_sensitive_output(self.log_output.getvalue())


class ProductionEmailSettingsTests(SimpleTestCase):
    """Evaluate configuration without loading private .env or opening a database."""

    def load_settings(self, **overrides):
        environment = {
            "DJANGO_LOAD_DOTENV": "False",
            "DJANGO_DEBUG": "False",
            "DJANGO_SECRET_KEY": "test-only-settings-key",
            "DJANGO_ALLOWED_HOSTS": "dsaquest.onrender.com",
            "DATABASE_URL": "postgresql://test:test@localhost/test_only_not_connected",
            "EMAIL_BACKEND": "accounts.email_backends.BrevoEmailBackend",
            "DEFAULT_FROM_EMAIL": "sender@example.com",
            "BREVO_API_KEY": API_KEY,
            **overrides,
        }
        with patch.dict(os.environ, {key: value for key, value in environment.items() if value is not None}, clear=True):
            return runpy.run_path(str(Path(__file__).resolve().parents[1] / "config" / "settings.py"))

    def test_production_brevo_needs_no_smtp_credentials(self):
        configured = self.load_settings()
        self.assertEqual(configured["EMAIL_BACKEND"], "accounts.email_backends.BrevoEmailBackend")
        self.assertEqual(configured["EMAIL_HOST_PASSWORD"], "")
        self.assertEqual(configured["EMAIL_TIMEOUT"], 20)

    def test_brevo_is_default_in_production(self):
        self.assertEqual(self.load_settings(EMAIL_BACKEND=None)["EMAIL_BACKEND"], "accounts.email_backends.BrevoEmailBackend")

    def test_production_missing_key_or_sender_fails_safely(self):
        for missing in ("BREVO_API_KEY", "DEFAULT_FROM_EMAIL"):
            with self.subTest(missing=missing), self.assertRaises(ImproperlyConfigured) as caught:
                self.load_settings(**{missing: ""})
            self.assertNotIn(API_KEY, str(caught.exception))

    def test_smtp_still_validates_credentials_and_tls_conflict(self):
        smtp = {"EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend"}
        with self.assertRaises(ImproperlyConfigured):
            self.load_settings(**smtp)
        with self.assertRaises(ImproperlyConfigured):
            self.load_settings(**smtp, EMAIL_USE_TLS="True", EMAIL_USE_SSL="True")

    def test_timeout_rejects_invalid_values_without_echoing_them(self):
        for value in ("0", "-1", UNSAFE_DETAIL):
            with self.subTest(value_is_sensitive=value == UNSAFE_DETAIL), self.assertRaises(ImproperlyConfigured) as caught:
                self.load_settings(EMAIL_TIMEOUT=value)
            self.assertNotIn(UNSAFE_DETAIL, str(caught.exception))


@override_settings(**BREVO_SETTINGS, PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class BrevoAccountDeliveryTests(BrevoTestSupport, TestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def register(self, email):
        return self.client.post(
            "/api/auth/register/",
            {
                "email": email, "password": PASSWORD, "confirm_password": PASSWORD,
                "display_name": "Email Player", "timezone": "UTC", "challenge_mode": "balanced",
            },
            format="json",
        )

    def assert_generic_response(self, response, detail):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"detail": detail})
        self.assert_no_sensitive_output(response.content.decode())

    def assert_emitted_link(self, path, email):
        call = self.post.call_args
        self.assertEqual(call.args, (BREVO_URL,))
        payload = call.kwargs["json"]
        self.assertEqual(payload["to"], [{"email": email}])
        links = [line for line in payload["textContent"].splitlines() if f"/{path}?" in line]
        self.assertEqual(len(links), 1)
        parsed = urlparse(links[0])
        self.assertEqual((parsed.scheme, parsed.netloc, parsed.path), ("https", "frontend.example.test", f"/{path}"))
        query = parse_qs(parsed.query)
        self.assertEqual(set(query), {"uid", "token"})
        self.assertTrue(all(len(value) == 1 and value[0] for value in query.values()))
        self.assert_no_sensitive_output(self.log_output.getvalue(), links[0], query["token"][0])
        return {key: value[0] for key, value in query.items()}

    def test_registration_emitted_link_verifies_once_and_allows_login(self):
        email = "register-brevo@example.com"
        response = self.register(email)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {"verification_required": True, "email": email})
        self.post.assert_called_once()
        user = User.objects.get(email=email)
        self.assertFalse(user.email_verified)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertFalse(Token.objects.filter(user=user).exists())
        query = self.assert_emitted_link("verify-email", email)

        pending_login = self.client.post("/api/auth/login/", {"email": email, "password": PASSWORD}, format="json")
        self.assertEqual(pending_login.status_code, 200)
        self.assertFalse(pending_login.data["user"]["email_verified"])
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {pending_login.data['token']}")
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)
        self.client.force_authenticate(user=None)
        verification = self.client.post("/api/auth/email/verify/", query, format="json")
        self.assertEqual(verification.status_code, 200)
        self.assertEqual(verification.data, {"detail": "Email verified successfully."})
        user.refresh_from_db()
        self.assertTrue(user.email_verified)
        self.assertEqual(self.client.post("/api/auth/email/verify/", query, format="json").status_code, 400)

        login = self.client.post("/api/auth/login/", {"email": email, "password": PASSWORD}, format="json")
        self.assertEqual(login.status_code, 200)
        self.assertEqual(Token.objects.get(user=user).key, login.data["token"])
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {login.data['token']}")
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)
        self.post.assert_called_once()

    def assert_registration_rollback_and_retry(self, failure, email):
        self.post.side_effect = [failure, provider_response()]
        response = self.register(email)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data, {"detail": REGISTRATION_FAILURE})
        self.assert_no_sensitive_output(response.content.decode())
        self.assertFalse(User.objects.filter(email=email).exists())
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Token.objects.count(), 0)
        self.post.assert_called_once()
        self.assert_safe_failure_logs()
        self.assert_emitted_link("verify-email", email)

        self.clear_logs()
        retry = self.register(email)
        self.assertEqual(retry.status_code, 201)
        self.assertEqual(retry.data, {"verification_required": True, "email": email})
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get(email=email)
        self.assertFalse(user.email_verified)
        self.assertEqual(Token.objects.count(), 0)
        self.assertEqual(self.post.call_count, 2)
        query = self.assert_emitted_link("verify-email", email)
        self.assertTrue(email_verification_token_generator.check_token(user, query["token"]))

    def test_registration_provider_403_rolls_back_then_retry_creates_one_pending_user(self):
        self.assert_registration_rollback_and_retry(provider_response(403), "retry-403@example.com")

    def test_registration_timeout_rolls_back_then_retry_creates_one_pending_user(self):
        self.assert_registration_rollback_and_retry(Timeout(UNSAFE_DETAIL), "retry-timeout@example.com")

    def test_duplicate_registration_does_not_send_a_second_email(self):
        email = "duplicate-brevo@example.com"
        self.assertEqual(self.register(email).status_code, 201)
        original = User.objects.get(email=email)
        original_password = original.password

        self.assertEqual(self.register(email).status_code, 400)
        self.post.assert_called_once()
        self.assertEqual(User.objects.filter(email=email).count(), 1)
        original.refresh_from_db()
        self.assertEqual(original.password, original_password)
        self.assertFalse(original.email_verified)

    def test_resend_acceptance_is_generic_and_preserves_unverified_state(self):
        user = User.objects.create_user(email="resend-brevo@example.com", password=PASSWORD)
        original_password = user.password
        response = self.client.post("/api/auth/email/resend/", {"email": user.email}, format="json")

        self.assert_generic_response(response, RESEND_DETAIL)
        self.post.assert_called_once()
        query = self.assert_emitted_link("verify-email", user.email)
        user.refresh_from_db()
        self.assertIsNone(user.email_verified_at)
        self.assertEqual(user.password, original_password)
        self.assertTrue(email_verification_token_generator.check_token(user, query["token"]))
        self.assertFalse(Token.objects.filter(user=user).exists())
        unknown = self.client.post("/api/auth/email/resend/", {"email": "unknown@example.com"}, format="json")
        self.assert_generic_response(unknown, RESEND_DETAIL)
        self.assertEqual(unknown.data, response.data)
        self.post.assert_called_once()

    def test_resend_rejection_and_timeout_are_generic_and_keep_user_unverified(self):
        user = User.objects.create_user(email="resend-failure-brevo@example.com", password=PASSWORD)
        original_password = user.password
        unknown = self.client.post("/api/auth/email/resend/", {"email": "unknown@example.com"}, format="json")
        self.assert_generic_response(unknown, RESEND_DETAIL)
        self.post.assert_not_called()

        for failure in (provider_response(403), Timeout(UNSAFE_DETAIL)):
            with self.subTest(failure_type=type(failure).__name__):
                self.post.reset_mock()
                self.post.side_effect = [failure]
                self.clear_logs()
                response = self.client.post("/api/auth/email/resend/", {"email": user.email}, format="json")
                self.assert_generic_response(response, RESEND_DETAIL)
                self.assertEqual(response.data, unknown.data)
                self.post.assert_called_once()
                self.assert_safe_failure_logs()
                self.assert_emitted_link("verify-email", user.email)
                user.refresh_from_db()
                self.assertIsNone(user.email_verified_at)
                self.assertEqual(user.password, original_password)
                self.assertFalse(Token.objects.filter(user=user).exists())

    def test_password_reset_emitted_link_changes_password_and_is_one_time(self):
        user = User.objects.create_user(
            email="reset-brevo@example.com", password=PASSWORD, email_verified_at=timezone.now()
        )
        original_password = user.password
        Token.objects.create(user=user)
        response = self.client.post("/api/auth/password-reset/request/", {"email": user.email}, format="json")

        self.assert_generic_response(response, RESET_DETAIL)
        self.post.assert_called_once()
        user.refresh_from_db()
        self.assertEqual(user.password, original_password)
        query = self.assert_emitted_link("reset-password", user.email)
        reset_payload = {**query, "new_password": "new-strong-password-456", "confirm_password": "new-strong-password-456"}
        reset = self.client.post("/api/auth/password-reset/confirm/", reset_payload, format="json")

        self.assertEqual(reset.status_code, 200)
        self.assertEqual(reset.data, {"detail": "Your password has been reset successfully."})
        user.refresh_from_db()
        self.assertNotEqual(user.password, original_password)
        self.assertFalse(user.check_password(PASSWORD))
        self.assertTrue(user.check_password(reset_payload["new_password"]))
        self.assertTrue(user.email_verified)
        self.assertFalse(Token.objects.filter(user=user).exists())
        changed_password = user.password
        reused = self.client.post(
            "/api/auth/password-reset/confirm/",
            {**query, "new_password": "another-strong-password-789", "confirm_password": "another-strong-password-789"},
            format="json",
        )
        self.assertEqual(reused.status_code, 400)
        user.refresh_from_db()
        self.assertEqual(user.password, changed_password)
        self.assertEqual(
            self.client.post("/api/auth/login/", {"email": user.email, "password": PASSWORD}, format="json").status_code,
            400,
        )
        login = self.client.post(
            "/api/auth/login/", {"email": user.email, "password": reset_payload["new_password"]}, format="json"
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(Token.objects.get(user=user).key, login.data["token"])
        self.post.assert_called_once()

    def test_password_reset_rejection_and_timeout_are_generic_without_state_changes(self):
        user = User.objects.create_user(
            email="reset-failure-brevo@example.com", password=PASSWORD, email_verified_at=timezone.now()
        )
        original_password, verified_at = user.password, user.email_verified_at
        original_token = Token.objects.create(user=user)
        unknown = self.client.post("/api/auth/password-reset/request/", {"email": "unknown@example.com"}, format="json")
        self.assert_generic_response(unknown, RESET_DETAIL)
        self.post.assert_not_called()

        for failure in (provider_response(403), Timeout(UNSAFE_DETAIL)):
            with self.subTest(failure_type=type(failure).__name__):
                self.post.reset_mock()
                self.post.side_effect = [failure]
                self.clear_logs()
                response = self.client.post("/api/auth/password-reset/request/", {"email": user.email}, format="json")
                self.assert_generic_response(response, RESET_DETAIL)
                self.assertEqual(response.data, unknown.data)
                self.post.assert_called_once()
                self.assert_safe_failure_logs()
                self.assert_emitted_link("reset-password", user.email)
                user.refresh_from_db()
                self.assertEqual(user.password, original_password)
                self.assertTrue(user.check_password(PASSWORD))
                self.assertEqual(user.email_verified_at, verified_at)
                self.assertEqual(Token.objects.get(user=user).key, original_token.key)
