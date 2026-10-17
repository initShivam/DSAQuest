from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import Q

from catalog.models import Question

from .models import DailyChallenge, DailyChallengeQuestion
from .utils import local_date_for_user


MODE_DIFFICULTIES = {
    "beginner": ["easy", "easy"],
    "balanced": ["easy", "medium"],
    "intermediate": ["medium", "medium"],
    "advanced": ["medium", "hard"],
    "adaptive": ["easy", "medium"],
}


def _candidate_questions(user, challenge_date, difficulty, used_ids):
    completed_ids = set(
        user.question_progress.filter(status="completed").values_list("question_id", flat=True)
    )
    recent_cutoff = challenge_date - timedelta(days=7)
    recently_assigned_ids = set(
        DailyChallengeQuestion.objects.filter(
            challenge__user=user,
            challenge__challenge_date__gte=recent_cutoff,
            challenge__challenge_date__lt=challenge_date,
        ).values_list("question_id", flat=True)
    )
    base = Question.objects.filter(is_active=True, difficulty=difficulty).exclude(id__in=used_ids)
    preferred = base.exclude(id__in=completed_ids | recently_assigned_ids).order_by("id")
    if preferred.exists():
        return preferred
    recent_ok = base.exclude(id__in=completed_ids).order_by("id")
    if recent_ok.exists():
        return recent_ok
    return base.order_by("id")


def _select_questions(user, challenge_date):
    selected = []
    used_ids = set()
    requested = MODE_DIFFICULTIES.get(user.challenge_mode, MODE_DIFFICULTIES["balanced"])
    for difficulty in requested:
        candidate = _candidate_questions(user, challenge_date, difficulty, used_ids).first()
        if candidate:
            selected.append(candidate)
            used_ids.add(candidate.id)

    # A small catalog should still produce a usable challenge. Fill missing slots from any active question.
    if len(selected) < 2:
        fallback = Question.objects.filter(is_active=True).exclude(id__in=used_ids).order_by("id")
        fallback_preferred = fallback.exclude(
            id__in=set(user.question_progress.filter(status="completed").values_list("question_id", flat=True))
        )
        for question in list(fallback_preferred) + list(fallback):
            if question.id not in used_ids:
                selected.append(question)
                used_ids.add(question.id)
            if len(selected) >= 2:
                break

    # Offer one optional bonus assignment when the catalog has another suitable item.
    if len(selected) >= 2:
        completed_ids = set(
            user.question_progress.filter(status="completed").values_list("question_id", flat=True)
        )
        recent_cutoff = challenge_date - timedelta(days=7)
        recently_assigned_ids = set(
            DailyChallengeQuestion.objects.filter(
                challenge__user=user,
                challenge__challenge_date__gte=recent_cutoff,
                challenge__challenge_date__lt=challenge_date,
            ).values_list("question_id", flat=True)
        )
        bonus = Question.objects.filter(is_active=True).exclude(id__in=used_ids).exclude(
            id__in=completed_ids | recently_assigned_ids
        ).order_by("id").first()
        if bonus is None:
            bonus = Question.objects.filter(is_active=True).exclude(id__in=used_ids).order_by("id").first()
        if bonus:
            selected.append(bonus)
    return selected[:3]


def generate_daily_challenge(user, challenge_date=None):
    challenge_date = challenge_date or local_date_for_user(user)
    try:
        with transaction.atomic():
            challenge, created = DailyChallenge.objects.get_or_create(
                user=user,
                challenge_date=challenge_date,
                defaults={"status": DailyChallenge.Status.OPEN},
            )
            if created:
                questions = _select_questions(user, challenge_date)
                for position, question in enumerate(questions, start=1):
                    DailyChallengeQuestion.objects.create(
                        challenge=challenge,
                        question=question,
                        position=position,
                        is_bonus=position > 2,
                    )
            return challenge
    except IntegrityError:
        # A concurrent request won the unique constraint race. Its committed row is the source of truth.
        return DailyChallenge.objects.get(user=user, challenge_date=challenge_date)
