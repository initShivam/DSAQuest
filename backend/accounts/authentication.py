from rest_framework.authentication import TokenAuthentication


class EmailVerifiedTokenAuthentication(TokenAuthentication):
    """Preserve the configured authentication path while allowing unverified users."""
