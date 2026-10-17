from django.db.models import Count, OuterRef, Q, Subquery
from rest_framework import filters, generics
from rest_framework.permissions import IsAuthenticated

from .models import Pattern, Question
from .serializers import PatternSerializer, QuestionSerializer


class QuestionListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = QuestionSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["title", "difficulty", "estimated_minutes"]
    ordering = ["difficulty", "title"]

    def get_queryset(self):
        queryset = Question.objects.filter(is_active=True).prefetch_related("patterns")
        difficulty = self.request.query_params.get("difficulty")
        pattern = self.request.query_params.get("pattern")
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        if pattern:
            queryset = queryset.filter(Q(patterns__slug=pattern) | Q(patterns__pk=pattern))
        return queryset.distinct()


class QuestionDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = QuestionSerializer

    def get_queryset(self):
        return Question.objects.filter(is_active=True).prefetch_related("patterns")


class PatternListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PatternSerializer

    def get_queryset(self):
        from progress.models import UserPatternProgress

        last_practiced = UserPatternProgress.objects.filter(
            user=self.request.user, pattern=OuterRef("pk")
        ).values("last_practiced_at")[:1]
        return Pattern.objects.filter(is_active=True).annotate(
            available_count=Count("questions", filter=Q(questions__is_active=True), distinct=True),
            completed_count=Count(
                "questions__user_progress",
                filter=Q(questions__user_progress__user=self.request.user, questions__user_progress__status="completed"),
                distinct=True,
            ),
            last_practiced_at=Subquery(last_practiced),
        ).order_by("display_order", "name")


class PatternDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PatternSerializer

    def get_queryset(self):
        from progress.models import UserPatternProgress

        last_practiced = UserPatternProgress.objects.filter(
            user=self.request.user, pattern=OuterRef("pk")
        ).values("last_practiced_at")[:1]
        return Pattern.objects.filter(is_active=True).annotate(
            available_count=Count("questions", filter=Q(questions__is_active=True), distinct=True),
            completed_count=Count(
                "questions__user_progress",
                filter=Q(questions__user_progress__user=self.request.user, questions__user_progress__status="completed"),
                distinct=True,
            ),
            last_practiced_at=Subquery(last_practiced),
        ).order_by("display_order", "name").prefetch_related("questions")
