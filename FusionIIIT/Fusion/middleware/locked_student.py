"""A locked student's account (alumni, withdrawn, ...) is read-only.

Any request of theirs other than a read (GET, HEAD, OPTIONS, TRACE) is
refused with 403, except the few views that only sign in or out, reset a
password, switch the selected role, handle notifications, or fetch results
(the result page asks with POST). Reading is never refused here.
"""
from django.http import JsonResponse
from django.urls import Resolver404, resolve
from rest_framework.authtoken.models import Token

from applications.academic_information.student_status import is_locked_status, status_label

SAFE_METHODS = frozenset({'GET', 'HEAD', 'OPTIONS', 'TRACE'})

# (module, view name) of every view a locked student may still POST to.
ALLOWED_VIEWS = frozenset({
    ('applications.globals.api.views', name) for name in (
        'login', 'logout', 'auth_view',
        'password_reset_send_otp', 'password_reset_verify_otp', 'password_reset_reset',
        'update_last_selected_role',
        'unread_notification_count', 'notification', 'NotificationRead',
        'delete_notification', 'clear_notifications', 'NotificationUnread',
    )
} | {
    ('applications.examination.api.views', 'CheckResultView'),
    ('applications.examination.api.views', 'GenerateStudentResultPDFAPI'),
})


def _view_key(func):
    """(module, name) of a resolved view; DRF views carry their class."""
    view = getattr(func, 'view_class', None) or getattr(func, 'cls', None) or func
    return view.__module__, view.__name__


def _request_users(request):
    """Every user the request could act as: the token's and the session's.
    A view may authenticate by either, so both are checked."""
    users = []
    parts = request.META.get('HTTP_AUTHORIZATION', '').split()
    if len(parts) == 2 and parts[0].lower() == 'token':
        token = Token.objects.select_related('user__extrainfo').filter(key=parts[1]).first()
        if token is not None:
            users.append(token.user)
    session_user = getattr(request, 'user', None)
    if session_user is not None and session_user.is_authenticated:
        users.append(session_user)
    return users


def _locked_extra(user):
    extra = getattr(user, 'extrainfo', None)
    if extra is not None and extra.user_type == 'student' and is_locked_status(extra.user_status):
        return extra
    return None


class LockedStudentMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        refusal = self.refusal(request)
        return refusal if refusal is not None else self.get_response(request)

    @staticmethod
    def refusal(request):
        if request.method in SAFE_METHODS:
            return None
        locked = [e for e in map(_locked_extra, _request_users(request)) if e is not None]
        if not locked:
            return None
        extra = locked[0]
        try:
            match = resolve(request.path_info)
        except Resolver404:
            return None
        if _view_key(match.func) in ALLOWED_VIEWS:
            return None
        return JsonResponse(
            {'detail': 'Your account is read-only because you are %s.'
                       % status_label(extra.user_status)},
            status=403)
