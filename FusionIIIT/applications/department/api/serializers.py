from rest_framework import serializers
from applications.department.models import Announcements


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcements
        fields = ('__all__')

    # def to_representation(self, instance):
    #     response = super().to_representation(instance)
    #     return response
