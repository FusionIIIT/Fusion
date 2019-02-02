from django.shortcuts import render
from notifications.signals import notify

# Create your views here.

def leave_module_notif(request):
    print("it works")
    user=request.user
    target_url='leave'
    notify.send(sender=user, recipient=user, target_url=target_url, verb='testing...')


