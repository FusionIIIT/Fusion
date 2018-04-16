import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import HttpResponse, get_object_or_404, render

from .helpers import seen_or_x, type_sort_notifs
from .models import Notification

login_url = getattr(settings, "LOGIN_URL", "/")


@login_required(login_url=login_url)
def notifications(request):
    context = {"notifications": request.user.notifications.all().order_by("-timestamp")}
    return render(request, "notification_channels/notify.html", context)


@login_required(login_url=login_url)
def read_all(request, notif_type):
    if notif_type == "all":
        request.user.notifications.seen()
        request.user.notifications.read()
    else:
        request.user.notifications.seen(notif_type=notif_type)
        request.user.notifications.read(notif_type=notif_type)
    context = {"success": True}
    return HttpResponse(json.dumps(context), content_type='application/json')


@login_required(login_url=login_url)
def seen_all(request, notif_type):
    if notif_type == "all":
        request.user.notifications.seen()
    else:
        request.user.notifications.seen(notif_type=notif_type)
    context = {"success": True}
    return HttpResponse(json.dumps(context), content_type='application/json')


@login_required(login_url=login_url)
def mark_seen(request, id):
    notif = get_object_or_404(Notification, id=id)
    context = {}
    if request.user == notif.recipient:
        notif.mark_seen()
        context['success'] = True
        context['text'] = "Successfully marked as seen"
        return HttpResponse(json.dumps(context), content_type='application/json')
    context['success'] = False
    context['text'] = "Unauthorised to make these changes"
    return HttpResponse(json.dumps(context), content_type='application/json')


@login_required(login_url=login_url)
def mark_read(request, id):
    notif = get_object_or_404(Notification, id=id)
    context = {}
    if request.user == notif.recipient:
        notif.mark_read()
        notif.mark_seen()
        context['success'] = True
        context['text'] = "Successfully marked as read"
        return HttpResponse(json.dumps(context), content_type='application/json')
    context['success'] = False
    context['text'] = "Unauthorised to make these changes"
    return HttpResponse(json.dumps(context), content_type='application/json')


@login_required(login_url=login_url)
def get_notifications(request):
    notifs = seen_or_x(Notification.objects.all())
    context = {"notifications": notifs}
    return render(request, "notification_channels/notify.html", context)


@login_required(login_url=login_url)
def get_type_sorted_notifs(request):
    context = type_sort_notifs(request.user.notifications)
    return render(request, "notification_channels/type_sorted_notifs.html", context)


@login_required(login_url=login_url)
def get_unseen_count(request):
    context = {
        "count": request.user.notifications.filter(seen=False).count(),
    }
    return HttpResponse(json.dumps(context), content_type="application/json")
