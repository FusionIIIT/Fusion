from django.http import HttpResponseRedirect
from django.urls import reverse
from notifications.utils import id2slug, slug2id
from django.shortcuts import get_object_or_404, redirect
from notifications.models import Notification
from notifications.signals import notify
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User


        
def mark_as_read_and_redirect(request, slug=None):
    notification_id = slug2id(slug)
    notification = get_object_or_404(
        Notification, recipient=request.user, id=notification_id)
    notification.mark_as_read()

    # This conditional statement is True only in
    # case of complaint_module.

    if(notification.data['module'] == 'Complaint System'):
        complaint_id=notification.description
        return HttpResponseRedirect(reverse(notification.data['url'],kwargs={'detailcomp_id1':complaint_id}))
    else:
        return HttpResponseRedirect(reverse(notification.data['url']))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def placement_cell_notification(request):
    send_to = request.data.get('sendTo')
    recipient = request.data.get('recipient')
    description = request.data.get('description') or request.data.get('type') or 'Placement Cell notification'

    if send_to == 'All':
        recipients = User.objects.filter(extrainfo__user_type='student')
    else:
        target_user = get_object_or_404(User, username=recipient)
        recipients = [target_user]

    for target in recipients:
        notify.send(
            sender=request.user,
            recipient=target,
            verb=description,
            url='placement:placement',
            module='Placement Cell',
        )

    return Response({'message': 'Notification sent successfully.'}, status=status.HTTP_200_OK)
