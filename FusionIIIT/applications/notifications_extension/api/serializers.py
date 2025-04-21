from rest_framework import serializers
from notifications.models import Notification
from notification.models import Announcements, AnnouncementRecipients
from applications.globals.models import ExtraInfo, DepartmentInfo
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields =  '__all__'

class AnnouncementListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcements
        fields = '__all__'  # Specify the fields you need


class AnnouncementSerializer(serializers.ModelSerializer):
    specific_users = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )  # List of specific user IDs for specific_users target group

    class Meta:
        model = Announcements
        fields = ['message', 'target_group', 'department', 'batch', 'module', 'specific_users']

    def validate(self, data):
        target_group = data.get('target_group')
        
        # Validate 'faculty' target group: department must be provided
        if target_group == 'faculty' and not data.get('department'):
            raise serializers.ValidationError("Department is required for faculty announcements.")

        # Validate 'students' target group: department and batch must be provided
        if target_group == 'students':
            if not data.get('department'):
                raise serializers.ValidationError("Department is required for student announcements.")
            if not data.get('batch'):
                raise serializers.ValidationError("Batch is required for student announcements.")
        
        return data

    def create(self, validated_data):
        specific_users = validated_data.pop('specific_users', [])
        announcement = Announcements.objects.create(**validated_data)

        # Handle specific_users for AnnouncementRecipients
        if validated_data['target_group'] == 'specific_users':
            extra_info_users = ExtraInfo.objects.filter(id__in=specific_users)
            for extra_info in extra_info_users:
                AnnouncementRecipients.objects.create(announcement=announcement, user=extra_info)

        return announcement