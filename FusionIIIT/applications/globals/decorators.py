from functools import wraps

from rest_framework import status
from rest_framework.response import Response

from applications.globals.models import HoldsDesignation

#: Held by definition rather than assigned, so they carry no HoldsDesignation row.
BASIC_ROLES = {'student', 'faculty', 'staff'}


def held_designations(user):
    """Every post this user may act in, lowercased.

    Keyed on `working`, not `user`: HoldsDesignation's own docstring says
    "Use 'working' to handle permissions in code", because `working` is whoever
    currently occupies the post and `user` is its substantive holder. Reading
    the wrong one authorises the person on leave and refuses their stand-in,
    and disagrees with the IAM, which projects on `working`.
    """
    names = (HoldsDesignation.objects
             .select_related('designation')
             .filter(working=user)
             .values_list('designation__name', flat=True))
    return {name.lower() for name in names if name}


def active_designation(user):
    """The post this user is currently acting in.

    Their own choice when they have made one and still hold it. Otherwise an
    office outranks the basic role, which is the rule the IAM applies too — so
    somebody who has never touched the role switcher is not locked out of the
    post they hold.
    """
    held = held_designations(user)
    chosen = getattr(getattr(user, 'extrainfo', None), 'last_selected_role', None)
    if chosen and chosen.lower() in held:
        return chosen.lower()
    return next(iter(sorted(held - BASIC_ROLES)), None)


def role_required(allowed_roles):
    """Allow the request only if the role being acted in is one of these.

    The set of posts somebody holds is not the same question. Checking the set
    means a student who also holds an office keeps that office's authority while
    acting as a student — so anything that reaches their session, an XSS above
    all, reaches the office's endpoints too.
    """
    allowed_lower = {role.lower() for role in allowed_roles}

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            acting = active_designation(request.user)

            if acting is None or acting not in allowed_lower:
                return Response(
                    {"error": "Permission denied: one of %s required" % allowed_roles},
                    status=status.HTTP_403_FORBIDDEN
                )

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
