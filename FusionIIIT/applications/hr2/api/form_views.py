"""Legacy entrypoint for HR2 API views.

This module exists for backward compatibility with existing URL configuration
and should not contain business logic.
"""

from .views.form_views import *  # noqa: F401,F403
