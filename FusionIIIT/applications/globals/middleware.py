"""Record successful authenticated writes and completed file downloads."""

from django.utils.text import capfirst
from rest_framework.authentication import TokenAuthentication

from applications.globals.decorators import active_designation
from applications.globals.models import ExtraInfo, SystemAdminAccess, UserActivityLog


DOWNLOAD_ACTIONS = {
    'download_template': 'Downloaded grade submission template',
    'generate_student_result_pdf': 'Downloaded student grade sheet',
    'generate_pdf': 'Downloaded grade sheet PDF',
    'downloadGrades': 'Downloaded course grades',
    'download_excel': 'Downloaded grade spreadsheet',
}
WRITE_ACTIONS = {
    'upload_grades_prof': 'Submitted student grade sheet',
    'preview_grades': 'Previewed student grade sheet',
    'submit_phd_milestone_grades': 'Submitted PhD milestone grades',
    'supervisor-thesis-grades-all-upload': 'Uploaded thesis grades',
    'supervisor-thesis-grades-all-bulk-submit': 'Submitted thesis grades',
}
IGNORED_ACTIONS = {
    'update_last_selected_role',
    # This POST only fetches the available courses for the selected term.
    'submitGradesProf',
}
WRITE_VERBS = {
    'POST': 'Submitted',
    'PUT': 'Updated',
    'PATCH': 'Updated',
    'DELETE': 'Deleted',
}
FILE_CONTENT_TYPES = (
    'application/pdf',
    'application/zip',
    'text/csv',
    'application/vnd.openxmlformats-officedocument',
    'application/vnd.ms-excel',
)


class RoleActivityAuditMiddleware:
    """Persist meaningful successful actions without storing request data."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        actor = self._actor(request)
        role = self._role_at_request_start(actor)
        response = self.get_response(request)
        method = request.method.upper()
        successful_response = (
            200 <= response.status_code < 300
            or (method not in ('GET', 'HEAD', 'OPTIONS')
                and 300 <= response.status_code < 400)
        )
        if actor and successful_response and not getattr(
            request, '_role_activity_recorded', False
        ):
            self._record_if_action(request, response, actor, role)
        return response

    @staticmethod
    def _actor(request):
        try:
            authenticated = TokenAuthentication().authenticate(request)
            if authenticated:
                return authenticated[0]
        except Exception:
            # Invalid or expired tokens are not attributed to an account.
            return None

        session_user = getattr(request, 'user', None)
        if session_user is not None and session_user.is_authenticated:
            return session_user
        return None

    @staticmethod
    def _role_at_request_start(user):
        if user is None:
            return None
        try:
            if SystemAdminAccess.objects.filter(user=user).exists():
                return 'system admin'
            role = active_designation(user)
            if role:
                return role
            return ExtraInfo.objects.filter(user=user).values_list(
                'user_type', flat=True
            ).first()
        except Exception:
            return None

    @staticmethod
    def _record_if_action(request, response, user, role):
        method = request.method.upper()
        match = getattr(request, 'resolver_match', None)
        url_name = getattr(match, 'url_name', None)
        if url_name in IGNORED_ACTIONS:
            return

        if method in ('GET', 'HEAD', 'OPTIONS'):
            content_type = response.get('Content-Type', '').lower()
            is_download = (
                'attachment' in response.get('Content-Disposition', '').lower()
                or any(content_type.startswith(value) for value in FILE_CONTENT_TYPES)
            )
            if not is_download:
                return
        else:
            is_download = 'attachment' in response.get(
                'Content-Disposition', '').lower()

        resource = (getattr(match, 'url_name', None) or
                    getattr(match, 'route', '') or '')[:200]
        route_label = (resource.rsplit(':', 1)[-1].replace('_', ' ').strip()
                       if resource else 'Fusion action')

        if is_download:
            action = DOWNLOAD_ACTIONS.get(
                url_name,
                'Downloaded {}'.format(capfirst(route_label)),
            )
        else:
            action = WRITE_ACTIONS.get(url_name) or '{} {}'.format(
                WRITE_VERBS.get(method, method.title()),
                capfirst(route_label),
            )

        try:
            UserActivityLog.objects.create(
                user=user,
                role=(role or 'unassigned')[:100],
                action=action[:200],
                method=method,
                resource=resource,
            )
        except Exception:
            # Auditing must never turn a successful application request into a failure.
            return
