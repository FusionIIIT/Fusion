from django.utils import timezone


def critical_section(critical_view):

    def wrapper(request, *args, **kwargs):
        now = timezone.now()
        timeout = 600
        session_life = now - request.user.last_login

        if session_life <= timeout:
            return critical_view(request, *args, **kwargs)

        # TODO: Add redirect to critical_section authentication
        # page, to reauthenticate the user.

    return wrapper
