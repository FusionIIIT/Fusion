from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework import serializers
from notifications.models import Notification
from applications.complaint_system.models import Caretaker, StudentComplain, Supervisor, Workers
from applications.globals.models import ExtraInfo,User

class StudentComplainSerializers(serializers.ModelSerializer):

    class Meta:
        model=StudentComplain
        fields=('__all__')

class WorkersSerializers(serializers.ModelSerializer):
    class Meta:
        model = Workers
        fields=('__all__')

class CaretakerSerializers(serializers.ModelSerializer):
    class Meta:
        model = Caretaker
        fields=('__all__')

class SupervisorSerializers(serializers.ModelSerializer):
    class Meta:
        model=Supervisor
        fields=('__all__')

class ExtraInfoSerializers(serializers.ModelSerializer):
    class Meta:
        model=ExtraInfo
        fields=('__all__')

class UserSerializers(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=('__all__')