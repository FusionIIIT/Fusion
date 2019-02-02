from django.shortcuts import render
from notifications.signals import notify

# Create your views here.

def leave_module_notif(request):
    user=request.user
    url='leave:leave'
    module='Leave Module'
    notify.send(sender=user, recipient=user, url=url, module=module, verb='testing...')


