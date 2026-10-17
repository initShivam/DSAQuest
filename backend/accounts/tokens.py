from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """Invalidate a verification link when the account becomes verified."""

    def _make_hash_value(self, user, timestamp):
        return "".join(
            [
                str(user.pk),
                str(user.password),
                str(user.email_verified_at),
                str(timestamp),
                str(user.email),
            ]
        )


email_verification_token_generator = EmailVerificationTokenGenerator()
