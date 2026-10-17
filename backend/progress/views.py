from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Question
from challenges.serializers import DailyChallengeSerializer
from challenges.utils import local_date_for_user

from .models import Achievement, DailyActivity, UserQuestionProgress, XPTransaction
from .serializers import (
    AchievementSerializer,
    DailyActivitySerializer,
    UserQuestionProgressSerializer,
    XPTransactionSerializer,
)
from .services import complete_assigned_question, current_streak, level_for_xp, longest_streak, total_xp
from challenges.services import generate_daily_challenge


class CompleteQuestionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        question = get_object_or_404(Question, pk=pk, is_active=True)
        personal_notes = request.data.get("personal_notes", "")
        if not isinstance(personal_notes, str) or len(personal_notes) > 5000:
            return Response({"detail": "personal_notes must be a string up to 5000 characters."}, status=400)
        try:
            result = complete_assigned_question(request.user, question, personal_notes=personal_notes)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                "duplicate": result["duplicate"],
                "xp_awarded": result["xp_awarded"],
                "bonus_xp": result["bonus_xp"],
                "daily_goal_completed": result["daily_goal_completed"],
                "current_streak": current_streak(request.user),
                "question_progress": UserQuestionProgressSerializer(
                    result["question_progress"], context={"request": request}
                ).data,
                "challenge": DailyChallengeSerializer(
                    result["challenge"], context={"request": request}
                ).data,
                "new_achievements": AchievementSerializer(
                    [item.achievement for item in result["new_achievements"]],
                    many=True,
                    context={"request": request},
                ).data,
            },
            status=status.HTTP_200_OK,
        )


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        challenge = generate_daily_challenge(request.user)
        xp = total_xp(request.user)
        completed = UserQuestionProgress.objects.filter(
            user=request.user, status=UserQuestionProgress.Status.COMPLETED
        ).count()
        patterns = request.user.pattern_progress.filter(completed_count__gt=0).count()
        return Response(
            {
                "user": {"id": request.user.id, "display_name": request.user.display_name, "email": request.user.email},
                "level": level_for_xp(xp),
                "completed_questions": completed,
                "patterns_practiced": patterns,
                "current_streak": current_streak(request.user),
                "today": DailyChallengeSerializer(challenge, context={"request": request}).data,
            }
        )


class ProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        completed = UserQuestionProgress.objects.filter(
            user=request.user, status=UserQuestionProgress.Status.COMPLETED
        )
        xp = total_xp(request.user)
        return Response(
            {
                "questions_completed": completed.count(),
                "total_xp": xp,
                "level": level_for_xp(xp),
                "current_streak": current_streak(request.user),
                "longest_streak": longest_streak(request.user),
                "difficulty": {
                    difficulty: completed.filter(question__difficulty=difficulty).count()
                    for difficulty in ("easy", "medium", "hard")
                },
                "patterns_practiced": request.user.pattern_progress.filter(completed_count__gt=0).count(),
            }
        )


class ProgressHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            days = min(max(int(request.query_params.get("days", 30)), 1), 366)
        except ValueError:
            return Response({"detail": "days must be an integer."}, status=400)
        activity = DailyActivity.objects.filter(user=request.user).order_by("-activity_date")[:days]
        questions = UserQuestionProgress.objects.filter(
            user=request.user, status=UserQuestionProgress.Status.COMPLETED
        ).select_related("question").prefetch_related("question__patterns")
        return Response(
            {
                "activity": DailyActivitySerializer(activity, many=True).data,
                "questions": UserQuestionProgressSerializer(
                    questions, many=True, context={"request": request}
                ).data,
            }
        )


class AchievementListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        achievements = Achievement.objects.filter(is_active=True)
        return Response(AchievementSerializer(achievements, many=True, context={"request": request}).data)


class StreakView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = local_date_for_user(request.user)
        activity = DailyActivity.objects.filter(user=request.user, activity_date=today).first()
        return Response(
            {
                "today": today,
                "today_goal_completed": bool(activity and activity.goal_completed),
                "today_questions_completed": activity.questions_completed if activity else 0,
                "current_streak": current_streak(request.user, today),
                "longest_streak": longest_streak(request.user),
            }
        )


class XPHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        transactions = XPTransaction.objects.filter(user=request.user)
        return Response(
            {
                "total_xp": total_xp(request.user),
                "transactions": XPTransactionSerializer(transactions, many=True).data,
            }
        )
