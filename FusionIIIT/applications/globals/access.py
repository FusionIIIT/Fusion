










"""Server-side role / designation checks.
Authorization must be derived from the authenticated user's real designation
"""

from django.db.models import Q


def user_holds_role(user, role):
    """True if ``user`` actually holds the designation named ``role``."""
    if not role or not getattr(user, "is_authenticated", False):
        return False
    from applications.globals.models import HoldsDesignation

    return HoldsDesignation.objects.filter(
        Q(working=user) | Q(user=user),
        designation__name=role,
    ).exists()


def user_holds_any_role(user, roles):
    """True if ``user`` holds any designation in ``roles``."""
    if not getattr(user, "is_authenticated", False):
        return False
    names = [r for r in roles if r]
    if not names:
        return False
    from applications.globals.models import HoldsDesignation

    return HoldsDesignation.objects.filter(
        Q(working=user) | Q(user=user),
        designation__name__in=names,
    ).exists()


# --- Reusable DRF permission classes (declarative, fail-closed) -------------
# Prefer these on admin views: `permission_classes = [IsAcadAdminOrDean]` or
# `permission_classes = [has_any_role("acadadmin", "Dean Academic")]`. They
# authorize from the real designation and deny by default.
from rest_framework.permissions import BasePermission  # noqa: E402


class HasDesignation(BasePermission):
    """Allow only users who hold one of ``allowed_roles`` (designation names)."""

    allowed_roles = ()
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        return user_holds_any_role(request.user, self.allowed_roles)


def has_any_role(*roles):
    """Factory: return a permission class allowing any of ``roles``."""

    class _HasAnyRole(HasDesignation):
        allowed_roles = roles

    return _HasAnyRole


class IsAcadAdmin(HasDesignation):
    allowed_roles = ("acadadmin",)


class IsDeanAcademic(HasDesignation):
    allowed_roles = ("Dean Academic",)


class IsAcadAdminOrDean(HasDesignation):
    allowed_roles = ("acadadmin", "Dean Academic")


# --- Decorator for PLAIN Django views (non-DRF) -----------------------------
# Plain function views (e.g. those using @require_http_methods) bypass DRF, so
# DRF auth/permission don't apply and the token header is ignored. This
# decorator authenticates the token itself and enforces the designation, so
# such views are no longer effectively open. Apply it as the OUTERMOST decorator.
from functools import wraps  # noqa: E402

from django.http import JsonResponse  # noqa: E402


def _user_from_request(request):
    """Resolve the user from a DRF-authenticated request or a Token header."""
    existing = getattr(request, "user", None)
    if getattr(existing, "is_authenticated", False):
        return existing
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth.startswith("Token "):
        return None
    key = auth.split(" ", 1)[1].strip()
    from rest_framework.authtoken.models import Token

    try:
        return Token.objects.select_related("user").get(key=key).user
    except Token.DoesNotExist:
        return None


def require_designation(*roles):
    """Gate a plain Django view to users holding one of ``roles`` (server-side)."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = _user_from_request(request)
            if user is None or not user_holds_any_role(user, roles):
                return JsonResponse(
                    {"error": "You do not have permission to perform this action."},
                    status=403,
                )
            request.user = user
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
