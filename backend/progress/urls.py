from django.urls import path

from .views import (
    AchievementListView,
    CompleteQuestionView,
    DashboardView,
    ProgressHistoryView,
    ProgressView,
    StreakView,
    XPHistoryView,
)


urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("questions/<int:pk>/complete/", CompleteQuestionView.as_view(), name="complete-question"),
    path("progress/", ProgressView.as_view(), name="progress"),
    path("progress/history/", ProgressHistoryView.as_view(), name="progress-history"),
    path("achievements/", AchievementListView.as_view(), name="achievements"),
    path("streak/", StreakView.as_view(), name="streak"),
    path("xp/history/", XPHistoryView.as_view(), name="xp-history"),
]
