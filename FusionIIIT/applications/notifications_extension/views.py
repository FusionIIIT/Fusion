from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from notifications.utils import id2slug, slug2id
from django.shortcuts import get_object_or_404, redirect
from notifications.models import Notification

def mark_as_read_and_redirect(request, slug=None):
    notification_id = slug2id(slug)

    notification = get_object_or_404(
        Notification, recipient=request.user, id=notification_id)
    notification.mark_as_read()

    return HttpResponseRedirect(reverse(notification.data['url']))
