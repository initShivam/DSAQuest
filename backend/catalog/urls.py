from django.urls import path

from .views import PatternDetailView, PatternListView, QuestionDetailView, QuestionListView


urlpatterns = [
    path("questions/", QuestionListView.as_view(), name="question-list"),
    path("questions/<int:pk>/", QuestionDetailView.as_view(), name="question-detail"),
    path("patterns/", PatternListView.as_view(), name="pattern-list"),
    path("patterns/<int:pk>/", PatternDetailView.as_view(), name="pattern-detail"),
]
