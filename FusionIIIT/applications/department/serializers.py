from rest_framework import serializers
from .models import *

class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model=Announcements
        fields="__all__"
    
class SpecialRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model=SpecialRequest
        fields="__all__"