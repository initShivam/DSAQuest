from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import DailyChallengeSerializer
from .services import generate_daily_challenge
from .utils import local_date_for_user


class TodayChallengeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        challenge = generate_daily_challenge(request.user)
        return Response(DailyChallengeSerializer(challenge, context={"request": request}).data)


class GenerateChallengeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        challenge = generate_daily_challenge(request.user)
        return Response(DailyChallengeSerializer(challenge, context={"request": request}).data, status=status.HTTP_200_OK)
