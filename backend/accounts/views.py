from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .emailing import send_password_reset_email, send_verification_email
from .serializers import (
    EmailAddressSerializer,
    EmailVerificationSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    RegisterSerializer,
    UserSerializer,
)
from .tokens import email_verification_token_generator


User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_register"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                user = serializer.save()
                send_verification_email(user)
        except Exception:
            return Response(
                {"detail": "We couldn't send the verification email. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(
            {"verification_required": True, "email": user.email},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        with transaction.atomic():
            locked_user = User.objects.select_for_update().get(pk=user.pk)
            Token.objects.filter(user=locked_user).delete()
            token = Token.objects.create(user=locked_user)
        return Response({"token": token.key, "user": UserSerializer(locked_user).data})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if hasattr(request.user, "auth_token"):
            request.user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        with transaction.atomic():
            locked_user = User.objects.select_for_update().get(pk=user.pk)
            if locked_user.email_verified or not email_verification_token_generator.check_token(locked_user, serializer.validated_data["token"]):
                return Response({"detail": "This verification link is invalid or has already been used."}, status=status.HTTP_400_BAD_REQUEST)
            locked_user.email_verified_at = timezone.now()
            locked_user.save(update_fields=["email_verified_at"])
            Token.objects.filter(user=locked_user).delete()
        return Response({"detail": "Email verified successfully."})


class ResendVerificationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_verification"

    def post(self, request):
        try:
            serializer = EmailAddressSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = User.objects.filter(email__iexact=serializer.validated_data["email"], is_active=True).first()
            if user and not user.email_verified:
                try:
                    send_verification_email(user)
                except Exception:
                    logger.exception(f"Failed to send verification email to {user.email}")
        except Exception as e:
            logger.exception(f"Unexpected error in ResendVerificationView: {e}")

        return Response({"detail": "If an account needs verification, a new email will arrive shortly."})


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_password_reset"

    def post(self, request):
        try:
            serializer = EmailAddressSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = User.objects.filter(email__iexact=serializer.validated_data["email"], is_active=True).first()
            if user:
                try:
                    send_password_reset_email(user)
                except Exception:
                    logger.exception(f"Failed to send password reset email to {user.email}")
        except Exception as e:
            logger.exception(f"Unexpected error in PasswordResetRequestView: {e}")

        return Response({"detail": "If an account exists for that email, a reset link will arrive shortly."})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        with transaction.atomic():
            locked_user = User.objects.select_for_update().get(pk=user.pk)
            if not default_token_generator.check_token(locked_user, serializer.validated_data["token"]):
                return Response({"detail": "This password reset link is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)
            locked_user.set_password(serializer.validated_data["new_password"])
            locked_user.save(update_fields=["password"])
            Token.objects.filter(user=locked_user).delete()
        return Response({"detail": "Your password has been reset successfully."})
