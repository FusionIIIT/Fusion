from functools import wraps

from rest_framework import status
from rest_framework.response import Response

from applications.globals.models import HoldsDesignation


def role_required(allowed_roles):
    """
    Decorator factory that accepts a list of allowed role names.
    Accepts multiple HoldsDesignation records per user.
    """
    allowed_lower = {role.lower() for role in allowed_roles}

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Fetch all designations for this user
            user_roles = (
                HoldsDesignation.objects
                .select_related('designation')
                .filter(user=request.user)
                .values_list('designation__name', flat=True)  # or whichever field holds the string
            )

            # Normalize to lowercase for comparison
            user_roles_lower = {r.lower() for r in user_roles}

            # Check intersection
            if not (user_roles_lower & allowed_lower):
                return Response(
                    {"error": "Permission denied: one of %s required" % allowed_roles},
                    status=status.HTTP_403_FORBIDDEN
                )

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
