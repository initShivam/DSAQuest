from django.urls import path

from .views import GenerateChallengeView, TodayChallengeView


urlpatterns = [
    path("challenges/today/", TodayChallengeView.as_view(), name="today-challenge"),
    path("challenges/generate/", GenerateChallengeView.as_view(), name="generate-challenge"),
]
