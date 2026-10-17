from django.conf import settings
from django.db import models

from catalog.models import Pattern, Question


class UserQuestionProgress(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not started"
        COMPLETED = "completed", "Completed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="question_progress")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="user_progress")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_STARTED)
    first_attempt_at = models.DateTimeField(null=True, blank=True)
    solved_at = models.DateTimeField(null=True, blank=True)
    solve_count = models.PositiveIntegerField(default=0)
    personal_notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "question"], name="unique_user_question_progress"),
        ]
        ordering = ["-solved_at", "-updated_at"]


class DailyActivity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="daily_activity")
    activity_date = models.DateField()
    questions_completed = models.PositiveIntegerField(default=0)
    goal_completed = models.BooleanField(default=False)
    xp_earned = models.PositiveIntegerField(default=0)
    streak_qualified = models.BooleanField(default=False)

    class Meta:
        ordering = ["-activity_date"]
        constraints = [
            models.UniqueConstraint(fields=["user", "activity_date"], name="unique_user_activity_date"),
        ]


class XPTransaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="xp_transactions")
    event_type = models.CharField(max_length=50)
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.PositiveBigIntegerField(null=True, blank=True)
    xp_amount = models.PositiveIntegerField()
    idempotency_key = models.CharField(max_length=180, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class Achievement(models.Model):
    class CriteriaType(models.TextChoices):
        QUESTIONS = "questions", "Questions completed"
        STREAK = "streak", "Consecutive goal days"
        PATTERNS = "patterns", "Patterns practiced"
        DIFFICULTY = "difficulty", "Difficulty completions"
        REVISIONS = "revisions", "Revision tasks"

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField()
    criteria_type = models.CharField(max_length=20, choices=CriteriaType.choices)
    criteria_value = models.PositiveIntegerField()
    difficulty = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["criteria_value", "name"]


class UserAchievement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="achievements")
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name="user_unlocks")
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-unlocked_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "achievement"], name="unique_user_achievement"),
        ]


class UserPatternProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pattern_progress")
    pattern = models.ForeignKey(Pattern, on_delete=models.CASCADE, related_name="user_progress")
    completed_count = models.PositiveIntegerField(default=0)
    last_practiced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "pattern"], name="unique_user_pattern_progress"),
        ]
