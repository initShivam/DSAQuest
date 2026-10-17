from datetime import date, datetime, timedelta, timezone as datetime_timezone
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.http.request import validate_host
from django.urls import Resolver404, resolve
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.views import LoginView, RegisterView
from accounts.models import User
from catalog.models import Pattern, Question, QuestionPattern
from challenges.models import DailyChallenge, DailyChallengeQuestion
from challenges.services import generate_daily_challenge
from challenges.utils import local_date_for_user
from progress.models import DailyActivity, UserQuestionProgress, XPTransaction
from progress.services import complete_assigned_question, current_streak
from accounts.tokens import email_verification_token_generator


class DeploymentConfigurationTests(SimpleTestCase):
    def test_render_hostname_is_allowed(self):
        self.assertIn(settings.DEPLOYMENT_HOST, settings.ALLOWED_HOSTS)
        self.assertTrue(validate_host(settings.DEPLOYMENT_HOST, settings.ALLOWED_HOSTS))

    def test_login_route_is_prefixed_with_api(self):
        self.assertIs(resolve("/api/auth/login/").func.view_class, LoginView)
        with self.assertRaises(Resolver404):
            resolve("/auth/login/")

    def test_frontend_preflight_is_allowed_for_api_route(self):
        response = self.client.options(
            "/api/auth/login/",
            HTTP_HOST=settings.DEPLOYMENT_HOST,
            HTTP_ORIGIN=settings.FRONTEND_ORIGIN,
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Access-Control-Allow-Origin"], settings.FRONTEND_ORIGIN)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class BackendFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pattern = Pattern.objects.create(name="Arrays and Strings", slug="arrays-strings")
        cls.hashing = Pattern.objects.create(name="Hashing", slug="hashing")
        cls.questions = []
        for index in range(1, 4):
            question = Question.objects.create(
                title=f"Easy Question {index}",
                slug=f"easy-question-{index}",
                leetcode_url=f"https://leetcode.com/problems/easy-question-{index}/",
                difficulty="easy",
                estimated_minutes=20,
            )
            QuestionPattern.objects.create(question=question, pattern=cls.pattern, is_primary=True)
            cls.questions.append(question)
        for index in range(1, 4):
            question = Question.objects.create(
                title=f"Medium Question {index}",
                slug=f"medium-question-{index}",
                leetcode_url=f"https://leetcode.com/problems/medium-question-{index}/",
                difficulty="medium",
                estimated_minutes=30,
            )
            QuestionPattern.objects.create(question=question, pattern=cls.hashing, is_primary=True)
            cls.questions.append(question)

    def setUp(self):
        self.user = User.objects.create_user(
            email="player@example.com", password="strong-password-123", timezone="UTC", email_verified_at=timezone.now()
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_challenge_generation_is_idempotent(self):
        first = generate_daily_challenge(self.user, date(2026, 1, 5))
        second = generate_daily_challenge(self.user, date(2026, 1, 5))

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(DailyChallenge.objects.filter(user=self.user, challenge_date=date(2026, 1, 5)).count(), 1)
        self.assertEqual(first.assignments.filter(is_bonus=False).count(), 2)
        self.assertEqual(first.assignments.values("question_id").distinct().count(), first.assignments.count())

    def test_challenge_mode_and_safe_fallback(self):
        self.user.challenge_mode = User.ChallengeMode.BEGINNER
        self.user.save(update_fields=["challenge_mode"])
        beginner = generate_daily_challenge(self.user, date(2026, 1, 6))
        self.assertEqual(set(beginner.assignments.values_list("question__difficulty", flat=True)), {"easy"})

        sparse_user = User.objects.create_user(email="sparse@example.com", password="strong-password-123")
        Question.objects.filter(difficulty="easy").update(is_active=False)
        fallback = generate_daily_challenge(sparse_user, date(2026, 1, 6))
        self.assertGreaterEqual(fallback.assignments.count(), 2)

    def test_duplicate_completion_awards_xp_once(self):
        challenge = generate_daily_challenge(self.user, date(2026, 1, 7))
        question = challenge.assignments.order_by("position").first().question

        first = self.client.post(f"/api/questions/{question.pk}/complete/", {}, format="json")
        second = self.client.post(f"/api/questions/{question.pk}/complete/", {}, format="json")

        self.assertEqual(first.status_code, 200)
        self.assertFalse(first.data["duplicate"])
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.data["duplicate"])
        self.assertEqual(XPTransaction.objects.filter(user=self.user).count(), 1)
        self.assertEqual(XPTransaction.objects.get(user=self.user).xp_amount, 10)
        self.assertEqual(UserQuestionProgress.objects.get(user=self.user, question=question).solve_count, 1)

    def test_daily_goal_adds_bonus_and_qualifies_streak(self):
        challenge = generate_daily_challenge(self.user, date(2026, 1, 8))
        assignments = list(challenge.assignments.order_by("position"))
        first = complete_assigned_question(self.user, assignments[0].question, datetime(2026, 1, 8, 12, tzinfo=datetime_timezone.utc))
        second = complete_assigned_question(self.user, assignments[1].question, datetime(2026, 1, 8, 13, tzinfo=datetime_timezone.utc))

        self.assertFalse(first["daily_goal_completed"])
        self.assertTrue(second["daily_goal_completed"])
        activity = DailyActivity.objects.get(user=self.user, activity_date=date(2026, 1, 8))
        self.assertEqual(activity.questions_completed, 2)
        self.assertEqual(activity.xp_earned, 55)
        self.assertEqual(XPTransaction.objects.filter(user=self.user).count(), 3)
        self.assertEqual(current_streak(self.user, date(2026, 1, 8)), 1)

    def test_bonus_question_does_not_complete_daily_goal(self):
        challenge = generate_daily_challenge(self.user, date(2026, 1, 10))
        bonus = challenge.assignments.get(is_bonus=True)
        mandatory = list(challenge.assignments.filter(is_bonus=False).order_by("position"))

        complete_assigned_question(self.user, bonus.question, datetime(2026, 1, 10, 10, tzinfo=datetime_timezone.utc))
        first_mandatory = complete_assigned_question(
            self.user, mandatory[0].question, datetime(2026, 1, 10, 11, tzinfo=datetime_timezone.utc)
        )

        self.assertFalse(first_mandatory["daily_goal_completed"])
        activity = DailyActivity.objects.get(user=self.user, activity_date=date(2026, 1, 10))
        self.assertEqual(activity.questions_completed, 2)

        second_mandatory = complete_assigned_question(
            self.user, mandatory[1].question, datetime(2026, 1, 10, 12, tzinfo=datetime_timezone.utc)
        )
        self.assertTrue(second_mandatory["daily_goal_completed"])

    def test_profile_update_rejects_invalid_timezone(self):
        response = self.client.patch("/api/auth/me/", {"timezone": "Not/A_Timezone"}, format="json")

        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.timezone, "UTC")

    def test_streak_continues_and_resets_after_a_missed_day(self):
        DailyActivity.objects.create(user=self.user, activity_date=date(2026, 1, 1), goal_completed=True, streak_qualified=True)
        DailyActivity.objects.create(user=self.user, activity_date=date(2026, 1, 2), goal_completed=True, streak_qualified=True)
        DailyActivity.objects.create(user=self.user, activity_date=date(2026, 1, 4), goal_completed=True, streak_qualified=True)

        self.assertEqual(current_streak(self.user, date(2026, 1, 2)), 2)
        self.assertEqual(current_streak(self.user, date(2026, 1, 4)), 1)

    def test_user_cannot_complete_another_users_assignment(self):
        own_challenge = generate_daily_challenge(self.user, date(2026, 1, 9))
        other = User.objects.create_user(email="other@example.com", password="strong-password-123")
        other_challenge = generate_daily_challenge(other, date(2026, 1, 9))
        own_question_ids = set(own_challenge.assignments.values_list("question_id", flat=True))
        question = Question.objects.filter(is_active=True).exclude(pk__in=own_question_ids).exclude(
            challenge_assignments__challenge=other_challenge
        ).first()
        DailyChallengeQuestion.objects.create(
            challenge=other_challenge,
            question=question,
            position=4,
            is_bonus=True,
        )

        response = self.client.post(f"/api/questions/{question.pk}/complete/", {}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(XPTransaction.objects.filter(user=self.user).count(), 0)

    def test_timezone_boundary_uses_user_local_date(self):
        self.user.timezone = "Asia/Kolkata"
        self.user.save(update_fields=["timezone"])
        instant = datetime(2026, 2, 1, 18, 45, tzinfo=datetime_timezone.utc)

        local_day = local_date_for_user(self.user, instant)
        challenge = generate_daily_challenge(self.user, local_day)
        result = complete_assigned_question(self.user, challenge.assignments.first().question, instant)

        self.assertEqual(local_day, date(2026, 2, 2))
        self.assertEqual(result["question_progress"].solved_at, instant)
        self.assertTrue(DailyActivity.objects.filter(user=self.user, activity_date=date(2026, 2, 2)).exists())
        self.assertFalse(DailyActivity.objects.filter(user=self.user, activity_date=date(2026, 2, 1)).exists())

    def test_authentication_and_authorization(self):
        anonymous = APIClient().get("/api/dashboard/")
        self.assertEqual(anonymous.status_code, 401)

        login = APIClient().post(
            "/api/auth/login/", {"email": self.user.email, "password": "strong-password-123"}, format="json"
        )
        self.assertEqual(login.status_code, 200)
        self.assertIn("token", login.data)

        register = APIClient().post(
            "/api/auth/register/",
            {"email": "new@example.com", "password": "strong-password-123", "confirm_password": "strong-password-123", "timezone": "America/New_York"},
            format="json",
        )
        self.assertEqual(register.status_code, 201)
        self.assertTrue(register.data["verification_required"])
        self.assertNotIn("token", register.data)

    def test_unverified_user_cannot_login_and_can_verify_once(self):
        pending = User.objects.create_user(email="pending@example.com", password="strong-password-123")
        login = APIClient().post(
            "/api/auth/login/", {"email": pending.email, "password": "strong-password-123"}, format="json"
        )
        self.assertEqual(login.status_code, 400)
        self.assertEqual(str(login.data["code"][0]), "email_not_verified")

        from rest_framework.authtoken.models import Token

        protected = APIClient()
        protected.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=pending).key}")
        self.assertEqual(protected.get("/api/auth/me/").status_code, 401)

        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        verification = APIClient().post(
            "/api/auth/email/verify/",
            {"uid": urlsafe_base64_encode(force_bytes(pending.pk)), "token": email_verification_token_generator.make_token(pending)},
            format="json",
        )
        self.assertEqual(verification.status_code, 200)
        self.assertTrue(User.objects.get(pk=pending.pk).email_verified)
        self.assertEqual(
            APIClient().post(
                "/api/auth/email/verify/",
                {"uid": urlsafe_base64_encode(force_bytes(pending.pk)), "token": email_verification_token_generator.make_token(pending)},
                format="json",
            ).status_code,
            400,
        )

    def test_registration_creates_pending_user_and_sends_verification_email(self):
        response = APIClient().post(
            "/api/auth/register/",
            {"email": "verify@example.com", "password": "strong-password-123", "confirm_password": "strong-password-123", "display_name": "Verify Me", "timezone": "UTC", "challenge_mode": "balanced"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="verify@example.com")
        self.assertFalse(user.email_verified)
        from django.core import mail

        self.assertTrue(mail.outbox[-1].to)
        self.assertIn("verify-email", mail.outbox[-1].body)

    @patch.object(RegisterView, "throttle_classes", new=[])
    @patch("accounts.views.send_verification_email", side_effect=RuntimeError("mail backend unavailable"))
    def test_registration_rolls_back_when_verification_email_fails(self, _send_email):
        response = APIClient().post(
            "/api/auth/register/",
            {"email": "rollback@example.com", "password": "strong-password-123", "confirm_password": "strong-password-123", "display_name": "Rollback", "timezone": "UTC", "challenge_mode": "balanced"},
            format="json",
        )
        self.assertEqual(response.status_code, 503)
        self.assertFalse(User.objects.filter(email="rollback@example.com").exists())

    def test_registration_rejects_password_mismatch(self):
        response = APIClient().post(
            "/api/auth/register/",
            {"email": "mismatch@example.com", "password": "strong-password-123", "confirm_password": "different-password-123", "display_name": "Mismatch", "timezone": "UTC", "challenge_mode": "balanced"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(email="mismatch@example.com").exists())

    @patch.object(RegisterView, "throttle_classes", new=[])
    def test_registration_rejects_duplicate_email(self):
        response = APIClient().post(
            "/api/auth/register/",
            {"email": self.user.email, "password": "strong-password-123", "confirm_password": "strong-password-123", "display_name": "Duplicate", "timezone": "UTC", "challenge_mode": "balanced"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_public_recovery_endpoint_ignores_stale_authorization_header(self):
        response = APIClient().post(
            "/api/auth/password-reset/request/",
            {"email": "nobody@example.com"},
            format="json",
            HTTP_AUTHORIZATION="Token stale-or-invalid",
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_verification_token_is_rejected(self):
        pending = User.objects.create_user(email="invalid@example.com", password="strong-password-123")
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        response = APIClient().post(
            "/api/auth/email/verify/",
            {"uid": urlsafe_base64_encode(force_bytes(pending.pk)), "token": "not-a-valid-token"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    @override_settings(PASSWORD_RESET_TIMEOUT=-1)
    def test_expired_verification_token_is_rejected(self):
        pending = User.objects.create_user(email="expired@example.com", password="strong-password-123")
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        response = APIClient().post(
            "/api/auth/email/verify/",
            {"uid": urlsafe_base64_encode(force_bytes(pending.pk)), "token": email_verification_token_generator.make_token(pending)},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_password_reset_is_generic_and_one_time(self):
        response = APIClient().post(
            "/api/auth/password-reset/request/", {"email": self.user.email}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("If an account exists", response.data["detail"])

        from django.core import mail
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        self.assertEqual(len(mail.outbox), 1)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        mismatch = APIClient().post(
            "/api/auth/password-reset/confirm/",
            {"uid": uid, "token": token, "new_password": "new-strong-password-123", "confirm_password": "different-strong-password-123"},
            format="json",
        )
        self.assertEqual(mismatch.status_code, 400)
        reset = APIClient().post(
            "/api/auth/password-reset/confirm/",
            {"uid": uid, "token": token, "new_password": "new-strong-password-123", "confirm_password": "new-strong-password-123"},
            format="json",
        )
        self.assertEqual(reset.status_code, 200)
        self.assertEqual(
            APIClient().post(
                "/api/auth/password-reset/confirm/",
                {"uid": uid, "token": token, "new_password": "another-strong-password-123", "confirm_password": "another-strong-password-123"},
                format="json",
            ).status_code,
            400,
        )

    @override_settings(PASSWORD_RESET_TIMEOUT=-1)
    def test_expired_password_reset_token_is_rejected(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        response = APIClient().post(
            "/api/auth/password-reset/confirm/",
            {"uid": uid, "token": default_token_generator.make_token(self.user), "new_password": "new-strong-password-123", "confirm_password": "new-strong-password-123"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_logout_revokes_token(self):
        login = APIClient().post(
            "/api/auth/login/", {"email": self.user.email, "password": "strong-password-123"}, format="json"
        )
        token_client = APIClient()
        token_client.credentials(HTTP_AUTHORIZATION=f"Token {login.data['token']}")

        logout = token_client.post("/api/auth/logout/")

        self.assertEqual(logout.status_code, 204)
        self.assertEqual(token_client.get("/api/auth/me/").status_code, 401)

    def test_login_rotates_existing_token(self):
        first_login = APIClient().post(
            "/api/auth/login/", {"email": self.user.email, "password": "strong-password-123"}, format="json"
        )
        second_login = APIClient().post(
            "/api/auth/login/", {"email": self.user.email, "password": "strong-password-123"}, format="json"
        )

        old_token_client = APIClient()
        old_token_client.credentials(HTTP_AUTHORIZATION=f"Token {first_login.data['token']}")
        new_token_client = APIClient()
        new_token_client.credentials(HTTP_AUTHORIZATION=f"Token {second_login.data['token']}")

        self.assertEqual(old_token_client.get("/api/auth/me/").status_code, 401)
        self.assertEqual(new_token_client.get("/api/auth/me/").status_code, 200)

    def test_catalog_and_progress_read_endpoints(self):
        challenge = self.client.get("/api/challenges/today/")
        self.assertEqual(challenge.status_code, 200)
        self.assertEqual(challenge.data["mandatory_total"], 2)

        for path in (
            "/api/dashboard/",
            "/api/questions/",
            f"/api/questions/{self.questions[0].pk}/",
            "/api/patterns/",
            f"/api/patterns/{self.pattern.pk}/",
            "/api/progress/",
            "/api/progress/history/",
            "/api/achievements/",
            "/api/streak/",
            "/api/xp/history/",
        ):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)


class SeedCommandTests(TestCase):
    def test_seed_command_is_safe_to_repeat(self):
        call_command("seed_data")
        call_command("seed_data")
        self.assertGreaterEqual(Question.objects.count(), 10)
        self.assertEqual(Question.objects.filter(slug="two-sum").count(), 1)
