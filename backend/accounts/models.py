from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone as django_timezone

from .managers import UserManager


def validate_timezone(value):
    try:
        ZoneInfo(value)
    except (TypeError, ZoneInfoNotFoundError):
        raise ValidationError("Use a valid IANA timezone, such as Asia/Kolkata or UTC.")


class User(AbstractBaseUser, PermissionsMixin):
    class ChallengeMode(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        BALANCED = "balanced", "Balanced"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"
        ADAPTIVE = "adaptive", "Adaptive"

    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=80, blank=True)
    challenge_mode = models.CharField(
        max_length=20, choices=ChallengeMode.choices, default=ChallengeMode.BALANCED
    )
    timezone = models.CharField(max_length=64, default="UTC", validators=[validate_timezone])
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=django_timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.display_name or self.email

    def clean(self):
        super().clean()
        self.email = type(self).objects.normalize_email(self.email)
        validate_timezone(self.timezone)
