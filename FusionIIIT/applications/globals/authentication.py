"""API tokens that stop working.

DRF's own token never expires, so a copy taken once is a credential for good —
and this one is kept in the browser's localStorage, where any script running on
the origin can read it. An age limit turns a permanent compromise into a bounded
one, and re-authenticating is the only thing the holder has to do about it.

Switch it on with, in the REST_FRAMEWORK setting:

    'DEFAULT_AUTHENTICATION_CLASSES': (
        'applications.globals.authentication.ExpiringTokenAuthentication',
    )
"""
import os
from datetime import timedelta

from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

#: Long enough for a working day, short enough that a stolen token dies.
TOKEN_TTL_HOURS = int(os.environ.get("API_TOKEN_TTL_HOURS", "12"))


class ExpiringTokenAuthentication(TokenAuthentication):
    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)

        if TOKEN_TTL_HOURS and token.created < (
                timezone.now() - timedelta(hours=TOKEN_TTL_HOURS)):
            # Deleted, not just refused: the row is what makes it work, and
            # leaving it lets a later change quietly bring the token back.
            token.delete()
            raise AuthenticationFailed("Session expired. Please sign in again.")

        return user, token
