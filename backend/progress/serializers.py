from rest_framework import serializers

from catalog.serializers import QuestionSerializer

from .models import Achievement, DailyActivity, UserAchievement, UserQuestionProgress, XPTransaction


class UserQuestionProgressSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)
    xp_earned = serializers.SerializerMethodField()

    class Meta:
        model = UserQuestionProgress
        fields = [
            "id",
            "question",
            "status",
            "first_attempt_at",
            "solved_at",
            "solve_count",
            "personal_notes",
            "xp_earned",
        ]

    def get_xp_earned(self, obj):
        from django.db.models import Sum

        user = self.context.get("request").user if self.context.get("request") else obj.user
        return (
            XPTransaction.objects.filter(
                user=user,
                event_type="question_completed",
                reference_type="question",
                reference_id=obj.question_id,
            ).aggregate(total=Sum("xp_amount"))["total"]
            or 0
        )


class XPTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = XPTransaction
        fields = [
            "id",
            "event_type",
            "reference_type",
            "reference_id",
            "xp_amount",
            "idempotency_key",
            "created_at",
        ]


class DailyActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyActivity
        fields = [
            "activity_date",
            "questions_completed",
            "goal_completed",
            "xp_earned",
            "streak_qualified",
        ]


class AchievementSerializer(serializers.ModelSerializer):
    unlocked = serializers.SerializerMethodField()
    unlocked_at = serializers.SerializerMethodField()
    current_progress = serializers.SerializerMethodField()

    class Meta:
        model = Achievement
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "criteria_type",
            "criteria_value",
            "difficulty",
            "unlocked",
            "unlocked_at",
            "current_progress",
        ]

    def _unlock(self, obj):
        user = self.context["request"].user
        return UserAchievement.objects.filter(user=user, achievement=obj).first()

    def get_unlocked(self, obj):
        return bool(self._unlock(obj))

    def get_unlocked_at(self, obj):
        unlock = self._unlock(obj)
        return unlock.unlocked_at if unlock else None

    def get_current_progress(self, obj):
        from .services import user_metrics

        metrics = user_metrics(self.context["request"].user)
        if obj.criteria_type == Achievement.CriteriaType.DIFFICULTY:
            return metrics.get(obj.difficulty, 0)
        return metrics.get(obj.criteria_type, 0)
