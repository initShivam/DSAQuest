from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class EmailVerifiedTokenAuthentication(TokenAuthentication):
    """Do not allow tokens to reach protected views before email verification."""

    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)
        if not user.email_verified:
            raise AuthenticationFailed("Verify your email address before continuing.")
        return user, token
