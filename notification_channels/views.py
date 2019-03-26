import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import HttpResponse, get_object_or_404, render

from .models import Notification

login_url = getattr(settings, "LOGIN_URL", "/")


@login_required(login_url=login_url)
def notifications(request):
    context = {"notifications": request.user.notifications.all()}
    return render(request, "notification_channels/notify.html", context)


@login_required(login_url=login_url)
def read_all(request):
    request.user.notifications.all().seen()
    request.user.notifications.all().read()
    context = {"success": True}
    return HttpResponse(json.dumps(context), content_type='application/json')


@login_required(login_url=login_url)
def seen_all(request):
    request.user.notifications.all().seen()
    context = {"success": True}
    return HttpResponse(json.dumps(context), content_type='application/json')


@login_required(login_url=login_url)
def mark_seen(request, id):
    notif = get_object_or_404(Notification, id=id)
    context = {}
    if request.user == notif.recipient:
        notif.mark_seen()
        context['success'] = True
        context['text'] = "Successfully marked as read"
        return HttpResponse(json.dumps(context), content_type='application/json')
    context['success'] = False
    context['text'] = "Unauthorised to make these changes"
    return HttpResponse(json.dumps(context), content_type='application/json')


@login_required(login_url=login_url)
def get_notifications(request):
    pass
