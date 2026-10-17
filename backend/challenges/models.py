from django.conf import settings
from django.db import models

from catalog.models import Question


class DailyChallenge(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        COMPLETED = "completed", "Completed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="daily_challenges")
    challenge_date = models.DateField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-challenge_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "challenge_date"], name="unique_user_challenge_date"),
        ]

    def __str__(self):
        return f"{self.user} / {self.challenge_date}"


class DailyChallengeQuestion(models.Model):
    class Status(models.TextChoices):
        ASSIGNED = "assigned", "Assigned"
        COMPLETED = "completed", "Completed"

    challenge = models.ForeignKey(DailyChallenge, on_delete=models.CASCADE, related_name="assignments")
    question = models.ForeignKey(Question, on_delete=models.PROTECT, related_name="challenge_assignments")
    position = models.PositiveSmallIntegerField()
    is_bonus = models.BooleanField(default=False)
    is_revision = models.BooleanField(default=False)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ASSIGNED)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["challenge", "question"], name="unique_question_per_challenge"),
            models.UniqueConstraint(fields=["challenge", "position"], name="unique_position_per_challenge"),
        ]

    def __str__(self):
        return f"{self.challenge} / {self.question}"
