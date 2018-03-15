from functools import wraps
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from applications.globals.models import Designation

def get_object_or_none(model, **kwargs):
    try:
        obj = model.objects.get(**kwargs)
    except:
        obj = None
    return obj

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
