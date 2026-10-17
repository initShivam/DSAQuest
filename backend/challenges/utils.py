from datetime import date, datetime, timezone as datetime_timezone
from zoneinfo import ZoneInfo

from django.utils import timezone


def user_timezone(user):
    return ZoneInfo(user.timezone)


def local_date_for_user(user, value=None):
    value = value or timezone.now()
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if timezone.is_naive(value):
        value = timezone.make_aware(value, datetime_timezone.utc)
    return timezone.localtime(value, user_timezone(user)).date()
