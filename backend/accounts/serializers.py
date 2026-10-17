from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "display_name", "challenge_mode", "timezone", "date_joined"]
        read_only_fields = ["id", "email", "date_joined"]

    def validate_timezone(self, value):
        try:
            ZoneInfo(value)
        except (TypeError, ZoneInfoNotFoundError):
            raise serializers.ValidationError("Use a valid IANA timezone.")
        return value


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "password", "display_name", "challenge_mode", "timezone"]

    def validate_timezone(self, value):
        try:
            ZoneInfo(value)
        except (TypeError, ZoneInfoNotFoundError):
            raise serializers.ValidationError("Use a valid IANA timezone.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(email=attrs["email"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account is inactive.")
        attrs["user"] = user
        return attrs
