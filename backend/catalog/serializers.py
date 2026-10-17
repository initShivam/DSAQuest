from rest_framework import serializers

from .models import Pattern, Question


class PatternSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Pattern
        fields = ["id", "name", "slug"]


class QuestionSerializer(serializers.ModelSerializer):
    patterns = PatternSummarySerializer(many=True, read_only=True)
    completed = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id",
            "title",
            "slug",
            "leetcode_url",
            "difficulty",
            "estimated_minutes",
            "patterns",
            "completed",
        ]

    def get_completed(self, obj):
        user = self.context.get("request").user if self.context.get("request") else None
        if not user or not user.is_authenticated:
            return False
        progress_model = self.context.get("progress_model")
        if progress_model is None:
            from progress.models import UserQuestionProgress

            progress_model = UserQuestionProgress
        return progress_model.objects.filter(user=user, question=obj, status="completed").exists()


class PatternSerializer(serializers.ModelSerializer):
    completed_count = serializers.IntegerField(read_only=True)
    available_count = serializers.IntegerField(read_only=True)
    last_practiced_at = serializers.DateTimeField(read_only=True, allow_null=True)

    class Meta:
        model = Pattern
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "display_order",
            "completed_count",
            "available_count",
            "last_practiced_at",
        ]
