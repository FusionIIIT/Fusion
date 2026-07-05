from datetime import timedelta

from django.utils import timezone
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication


TOKEN_MAX_AGE_SECONDS = 8 * 60 * 60


def apply_token_expiry_patch():
    if getattr(TokenAuthentication, "_fusion_expiry_patch_applied", False):
        return

    original_authenticate_credentials = TokenAuthentication.authenticate_credentials

    def authenticate_credentials_with_expiry(self, key):
        user_auth_tuple = original_authenticate_credentials(self, key)
        user, token = user_auth_tuple

        token_age = timezone.now() - token.created
        if token_age > timedelta(seconds=TOKEN_MAX_AGE_SECONDS):
            token.delete()
            raise exceptions.AuthenticationFailed("Token expired. Please login again.")

        return user, token

    TokenAuthentication.authenticate_credentials = authenticate_credentials_with_expiry
    TokenAuthentication._fusion_expiry_patch_applied = True
