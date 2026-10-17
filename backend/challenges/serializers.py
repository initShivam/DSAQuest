from rest_framework import serializers

from catalog.serializers import QuestionSerializer

from .models import DailyChallenge, DailyChallengeQuestion


class ChallengeAssignmentSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)

    class Meta:
        model = DailyChallengeQuestion
        fields = [
            "id",
            "question",
            "position",
            "is_bonus",
            "is_revision",
            "status",
            "completed_at",
        ]


class DailyChallengeSerializer(serializers.ModelSerializer):
    assignments = ChallengeAssignmentSerializer(many=True, read_only=True)
    mandatory_total = serializers.SerializerMethodField()
    mandatory_completed = serializers.SerializerMethodField()
    goal_completed = serializers.SerializerMethodField()
    xp_earned = serializers.SerializerMethodField()

    class Meta:
        model = DailyChallenge
        fields = [
            "id",
            "challenge_date",
            "status",
            "assignments",
            "mandatory_total",
            "mandatory_completed",
            "goal_completed",
            "xp_earned",
            "created_at",
        ]

    def get_mandatory_total(self, obj):
        return obj.assignments.filter(is_bonus=False).count()

    def get_mandatory_completed(self, obj):
        return obj.assignments.filter(is_bonus=False, status=DailyChallengeQuestion.Status.COMPLETED).count()

    def get_goal_completed(self, obj):
        from progress.models import DailyActivity

        return DailyActivity.objects.filter(user=obj.user, activity_date=obj.challenge_date, goal_completed=True).exists()

    def get_xp_earned(self, obj):
        from progress.models import DailyActivity

        activity = DailyActivity.objects.filter(user=obj.user, activity_date=obj.challenge_date).first()
        return activity.xp_earned if activity else 0
