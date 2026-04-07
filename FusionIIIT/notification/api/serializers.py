"""
Notification API Serializers
=============================

Serializers for API views to validate and serialize notification data.
"""

from rest_framework import serializers
from notifications.models import Notification
from ..models import Announcements, AnnouncementRecipients
from applications.globals.models import ExtraInfo


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model"""
    
    sender_username = serializers.CharField(source='actor.username', read_only=True)
    sender_name = serializers.CharField(source='actor.get_full_name', read_only=True)
    module = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'sender_username',
            'sender_name',
            'verb',
            'description',
            'timestamp',
            'unread',
            'module',
            'data',
        ]
        read_only_fields = fields
    
    def get_module(self, obj):
        """Extract module from notification data"""
        return obj.data.get('module', 'Unknown')


class AnnouncementSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating announcements"""
    
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    recipient_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Announcements
        fields = [
            'id',
            'message',
            'module',
            'target_group',
            'department',
            'batch',
            'is_published',
            'is_active',
            'created_by_username',
            'created_at',
            'updated_at',
            'published_at',
            'recipient_count',
        ]
        read_only_fields = [
            'id',
            'created_by_username',
            'created_at',
            'updated_at',
            'published_at',
            'recipient_count',
        ]
    
    def get_recipient_count(self, obj):
        """Get count of specific recipients"""
        if obj.target_group == 'specific_users':
            return obj.recipients.count()
        return 0
    
    def validate(self, data):
        """Validate announcement data"""
        target_group = data.get('target_group')
        
        # Department announcements require department
        if target_group == 'department' and not data.get('department'):
            raise serializers.ValidationError(
                "Department is required for department-wide announcements."
            )
        
        # Batch announcements require batch
        if target_group == 'batch' and not data.get('batch'):
            raise serializers.ValidationError(
                "Batch is required for batch-specific announcements."
            )
        
        return data


class AnnouncementListSerializer(serializers.ModelSerializer):
    """Serializer for listing announcements"""
    
    created_by = serializers.CharField(source='created_by.get_full_name', read_only=True)
    target_group_display = serializers.CharField(source='get_target_group_display', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True, allow_null=True)
    recipient_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Announcements
        fields = [
            'id',
            'message',
            'module',
            'target_group',
            'target_group_display',
            'department_name',
            'batch',
            'is_published',
            'is_active',
            'created_by',
            'created_at',
            'published_at',
            'recipient_count',
        ]
        read_only_fields = fields
    
    def get_recipient_count(self, obj):
        """Get recipient count"""
        if obj.target_group == 'specific_users':
            return obj.recipients.count()
        return 0


class AnnouncementDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single announcement"""
    
    created_by = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_info = serializers.SerializerMethodField()
    recipients = serializers.SerializerMethodField()
    read_statistics = serializers.SerializerMethodField()
    
    class Meta:
        model = Announcements
        fields = [
            'id',
            'message',
            'module',
            'target_group',
            'department',
            'batch',
            'is_published',
            'is_active',
            'created_by',
            'created_at',
            'updated_at',
            'published_at',
            'recipients',
            'read_statistics',
            'updated_by_info',
        ]
        read_only_fields = fields
    
    def get_recipients(self, obj):
        """Get specific recipients if applicable"""
        if obj.target_group == 'specific_users':
            recipients = obj.recipients.all()
            return AnnouncementRecipientSerializer(recipients, many=True).data
        return []
    
    def get_read_statistics(self, obj):
        """Get read statistics"""
        if obj.target_group == 'specific_users':
            total = obj.recipients.count()
            read = obj.recipients.filter(is_read=True).count()
            unread = total - read
            
            return {
                'total': total,
                'read': read,
                'unread': unread,
                'read_percentage': (read / total * 100) if total > 0 else 0,
            }
        return None
    
    def get_updated_by_info(self, obj):
        """Get updated by information"""
        return f"Last updated at {obj.updated_at.strftime('%Y-%m-%d %H:%M')}"


class AnnouncementRecipientSerializer(serializers.ModelSerializer):
    """Serializer for announcement recipients"""
    
    user_name = serializers.CharField(source='user.user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.user.email', read_only=True)
    user_username = serializers.CharField(source='user.user.username', read_only=True)
    
    class Meta:
        model = AnnouncementRecipients
        fields = [
            'id',
            'user_name',
            'user_email',
            'user_username',
            'is_read',
            'read_at',
            'created_at',
        ]
        read_only_fields = fields


class CreateAnnouncementWithRecipientsSerializer(serializers.ModelSerializer):
    """Serializer for creating announcement with specific recipients"""
    
    specific_user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of ExtraInfo IDs for specific_users target group"
    )
    
    class Meta:
        model = Announcements
        fields = [
            'message',
            'module',
            'target_group',
            'department',
            'batch',
            'specific_user_ids',
        ]
    
    def validate(self, data):
        """Validate that required fields are present"""
        target_group = data.get('target_group')
        
        if target_group == 'department' and not data.get('department'):
            raise serializers.ValidationError(
                {"department": "Department is required for department-wide announcements."}
            )
        
        if target_group == 'batch' and not data.get('batch'):
            raise serializers.ValidationError(
                {"batch": "Batch is required for batch-specific announcements."}
            )
        
        if target_group == 'specific_users' and not data.get('specific_user_ids'):
            raise serializers.ValidationError(
                {"specific_user_ids": "At least one user ID is required for specific_users target group."}
            )
        
        return data
    
    def create(self, validated_data):
        """Create announcement and add specific recipients"""
        specific_user_ids = validated_data.pop('specific_user_ids', [])
        
        announcement = Announcements.objects.create(**validated_data)
        
        # Add specific recipients
        if announcement.target_group == 'specific_users' and specific_user_ids:
            for user_id in specific_user_ids:
                try:
                    extra_info = ExtraInfo.objects.get(id=user_id)
                    AnnouncementRecipients.objects.create(
                        announcement=announcement,
                        user=extra_info
                    )
                except ExtraInfo.DoesNotExist:
                    pass  # Skip if user doesn't exist
        
        return announcement


class NotificationModuleStatsSerializer(serializers.Serializer):
    """Serializer for notification statistics by module"""
    
    module = serializers.CharField()
    count = serializers.IntegerField()
    unread_count = serializers.IntegerField()
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
