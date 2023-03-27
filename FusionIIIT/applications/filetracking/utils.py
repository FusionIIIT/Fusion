from .models import File, Tracking
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from django.contrib.auth.models import User

def get_designation(userid):
    user_designation=HoldsDesignation.objects.select_related('user','working','designation').filter(user=userid)
    return user_designation

def get_all_designation():
     user_designation=HoldsDesignation.objects.select_related('user','working','designation').all()
     return user_designation
