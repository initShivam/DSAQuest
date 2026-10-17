from datetime import timedelta

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from challenges.models import DailyChallenge, DailyChallengeQuestion
from challenges.services import generate_daily_challenge
from challenges.utils import local_date_for_user

from .models import (
    Achievement,
    DailyActivity,
    UserAchievement,
    UserPatternProgress,
    UserQuestionProgress,
    XPTransaction,
)


XP_BY_DIFFICULTY = {"easy": 10, "medium": 25, "hard": 50}
DAILY_GOAL = 2
DAILY_GOAL_BONUS = 20


def xp_for_question(question):
    return XP_BY_DIFFICULTY.get(question.difficulty, 0)


def _qualified_dates(user):
    return set(
        DailyActivity.objects.filter(user=user, goal_completed=True).values_list("activity_date", flat=True)
    )


def current_streak(user, as_of=None):
    as_of = as_of or local_date_for_user(user)
    qualified = _qualified_dates(user)
    cursor = as_of
    if cursor not in qualified:
        cursor -= timedelta(days=1)
    streak = 0
    while cursor in qualified:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def longest_streak(user):
    dates = sorted(_qualified_dates(user))
    longest = running = 0
    previous = None
    for activity_date in dates:
        if previous and activity_date == previous + timedelta(days=1):
            running += 1
        else:
            running = 1
        longest = max(longest, running)
        previous = activity_date
    return longest


def user_metrics(user):
    completed = UserQuestionProgress.objects.filter(user=user, status=UserQuestionProgress.Status.COMPLETED)
    total_questions = completed.count()
    difficulty_counts = {
        difficulty: completed.filter(question__difficulty=difficulty).count()
        for difficulty in ("easy", "medium", "hard")
    }
    distinct_patterns = UserPatternProgress.objects.filter(user=user, completed_count__gt=0).count()
    revisions = DailyChallengeQuestion.objects.filter(
        challenge__user=user, is_revision=True, status=DailyChallengeQuestion.Status.COMPLETED
    ).count()
    return {
        "questions": total_questions,
        "patterns": distinct_patterns,
        "streak": longest_streak(user),
        "easy": difficulty_counts["easy"],
        "medium": difficulty_counts["medium"],
        "hard": difficulty_counts["hard"],
        "revisions": revisions,
    }


def evaluate_achievements(user):
    metrics = user_metrics(user)
    unlocked = []
    for achievement in Achievement.objects.filter(is_active=True):
        metric = metrics.get(achievement.criteria_type)
        if achievement.criteria_type == Achievement.CriteriaType.DIFFICULTY:
            metric = metrics.get(achievement.difficulty, 0)
        if metric is None or metric < achievement.criteria_value:
            continue
        user_achievement, created = UserAchievement.objects.get_or_create(
            user=user, achievement=achievement
        )
        if created:
            unlocked.append(user_achievement)
    return unlocked


def _update_patterns(user, question, completed_at):
    for pattern in question.patterns.filter(is_active=True):
        progress, _ = UserPatternProgress.objects.select_for_update().get_or_create(
            user=user, pattern=pattern, defaults={"completed_count": 0}
        )
        progress.completed_count += 1
        progress.last_practiced_at = completed_at
        progress.save(update_fields=["completed_count", "last_practiced_at"])


def complete_assigned_question(user, question, completed_at=None, personal_notes=""):
    completed_at = completed_at or timezone.now()
    challenge_date = local_date_for_user(user, completed_at)
    challenge = generate_daily_challenge(user, challenge_date)

    with transaction.atomic():
        challenge = DailyChallenge.objects.select_for_update().get(pk=challenge.pk)
        assignment = DailyChallengeQuestion.objects.select_for_update().filter(
            challenge=challenge, question=question
        ).first()
        if assignment is None:
            raise ValueError("This question is not assigned in today's challenge.")

        progress, _ = UserQuestionProgress.objects.select_for_update().get_or_create(
            user=user, question=question
        )
        if progress.status == UserQuestionProgress.Status.COMPLETED:
            if assignment.status != DailyChallengeQuestion.Status.COMPLETED:
                assignment.status = DailyChallengeQuestion.Status.COMPLETED
                assignment.completed_at = progress.solved_at or completed_at
                assignment.save(update_fields=["status", "completed_at"])
            return {
                "duplicate": True,
                "xp_awarded": 0,
                "bonus_xp": 0,
                "daily_goal_completed": DailyActivity.objects.filter(
                    user=user, activity_date=challenge_date, goal_completed=True
                ).exists(),
                "new_achievements": [],
                "question_progress": progress,
                "assignment": assignment,
                "challenge": challenge,
            }

        progress.status = UserQuestionProgress.Status.COMPLETED
        progress.first_attempt_at = progress.first_attempt_at or completed_at
        progress.solved_at = completed_at
        progress.solve_count += 1
        if personal_notes:
            progress.personal_notes = personal_notes
        progress.save()

        assignment.status = DailyChallengeQuestion.Status.COMPLETED
        assignment.completed_at = completed_at
        assignment.save(update_fields=["status", "completed_at"])

        activity, _ = DailyActivity.objects.select_for_update().get_or_create(
            user=user, activity_date=challenge_date
        )
        question_xp = xp_for_question(question)
        XPTransaction.objects.create(
            user=user,
            event_type="question_completed",
            reference_type="question",
            reference_id=question.id,
            xp_amount=question_xp,
            idempotency_key=f"question-completion:{user.id}:{question.id}",
        )
        activity.questions_completed += 1
        activity.xp_earned += question_xp

        bonus_xp = 0
        mandatory_completed = DailyChallengeQuestion.objects.filter(
            challenge=challenge,
            is_bonus=False,
            status=DailyChallengeQuestion.Status.COMPLETED,
        ).count()
        if mandatory_completed >= DAILY_GOAL and not activity.goal_completed:
            activity.goal_completed = True
            activity.streak_qualified = True
            bonus_xp = DAILY_GOAL_BONUS
            XPTransaction.objects.create(
                user=user,
                event_type="daily_goal_completed",
                reference_type="activity",
                reference_id=activity.id,
                xp_amount=bonus_xp,
                idempotency_key=f"daily-goal:{user.id}:{challenge_date.isoformat()}",
            )
            activity.xp_earned += bonus_xp
        activity.save()

        if activity.goal_completed:
            challenge.status = DailyChallenge.Status.COMPLETED
            challenge.save(update_fields=["status", "updated_at"])
        _update_patterns(user, question, completed_at)
        new_achievements = evaluate_achievements(user)
        return {
            "duplicate": False,
            "xp_awarded": question_xp,
            "bonus_xp": bonus_xp,
            "daily_goal_completed": activity.goal_completed,
            "new_achievements": new_achievements,
            "question_progress": progress,
            "assignment": assignment,
            "challenge": challenge,
        }


def total_xp(user):
    return XPTransaction.objects.filter(user=user).aggregate(total=Sum("xp_amount"))["total"] or 0


def level_for_xp(xp):
    levels = [
        (0, 1, "Beginner"),
        (100, 2, "Apprentice"),
        (250, 3, "Problem Solver"),
        (500, 4, "Pattern Hunter"),
        (1000, 5, "Code Warrior"),
        (2000, 6, "DSA Master"),
    ]
    current = levels[0]
    for level in levels:
        if xp >= level[0]:
            current = level
    return {"level": current[1], "title": current[2], "current_xp": xp, "next_level_xp": next((item[0] for item in levels if item[0] > xp), None)}
