"""
Notification API Serializers
=============================

Serializers for API views to validate and serialize notification data.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from notifications.models import Notification
from ..models import Announcements, AnnouncementRecipients
from applications.globals.models import ExtraInfo


def build_announcement_message(title=None, content=None, fallback_message=None):
    """Build a persisted `message` string from title/content inputs."""
    title = (title or "").strip()
    content = (content or "").strip()
    fallback_message = (fallback_message or "").strip()

    if title and content:
        return f"{title}\n\n{content}"
    if content:
        return content
    if title:
        return title
    return fallback_message


def split_announcement_message(message):
    """Split persisted `message` into title/content for frontend convenience."""
    raw = (message or "").strip()
    if not raw:
        return {"title": "", "content": ""}

    if "\n\n" in raw:
        title, content = raw.split("\n\n", 1)
        return {"title": title.strip(), "content": content.strip()}

    return {"title": raw, "content": raw}


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
    title = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    
    class Meta:
        model = Announcements
        fields = [
            'id',
            'title',
            'content',
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

    def get_title(self, obj):
        return split_announcement_message(obj.message).get('title', '')

    def get_content(self, obj):
        return split_announcement_message(obj.message).get('content', '')
    
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
    title = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    
    class Meta:
        model = Announcements
        fields = [
            'id',
            'title',
            'content',
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

    def get_title(self, obj):
        return split_announcement_message(obj.message).get('title', '')

    def get_content(self, obj):
        return split_announcement_message(obj.message).get('content', '')


class AnnouncementDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single announcement"""
    
    created_by = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_info = serializers.SerializerMethodField()
    recipients = serializers.SerializerMethodField()
    read_statistics = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    
    class Meta:
        model = Announcements
        fields = [
            'id',
            'title',
            'content',
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

    def get_title(self, obj):
        return split_announcement_message(obj.message).get('title', '')

    def get_content(self, obj):
        return split_announcement_message(obj.message).get('content', '')


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
    
    title = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Announcement title"
    )

    content = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Announcement content"
    )

    message = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Legacy combined message field"
    )

    specific_user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of ExtraInfo IDs for specific_users target group"
    )

    specific_usernames = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
        help_text="List of usernames for specific_users target group"
    )
    
    class Meta:
        model = Announcements
        fields = [
            'title',
            'content',
            'message',
            'module',
            'target_group',
            'department',
            'batch',
            'specific_user_ids',
            'specific_usernames',
        ]
    
    def validate(self, data):
        """Validate that required fields are present"""
        target_group = data.get('target_group', getattr(self.instance, 'target_group', None))

        resolved_message = build_announcement_message(
            title=data.get('title'),
            content=data.get('content'),
            fallback_message=data.get('message'),
        )

        if not resolved_message:
            raise serializers.ValidationError(
                {"content": "Announcement title/content cannot be empty."}
            )

        data['message'] = resolved_message
        
        if target_group == 'department' and not data.get('department'):
            raise serializers.ValidationError(
                {"department": "Department is required for department-wide announcements."}
            )
        
        if target_group == 'batch' and not data.get('batch'):
            raise serializers.ValidationError(
                {"batch": "Batch is required for batch-specific announcements."}
            )
        
        has_ids = bool(data.get('specific_user_ids'))
        has_usernames = bool(data.get('specific_usernames'))

        existing_recipients_count = 0
        if self.instance and target_group == 'specific_users':
            existing_recipients_count = self.instance.recipients.count()

        if target_group == 'specific_users' and not (has_ids or has_usernames or existing_recipients_count > 0):
            raise serializers.ValidationError(
                {"specific_user_ids": "Provide at least one user ID or username for specific_users target group."}
            )
        
        return data

    @staticmethod
    def _resolve_specific_user_ids(specific_user_ids, specific_usernames):
        resolved_ids = set(specific_user_ids or [])

        if specific_usernames:
            for username in specific_usernames:
                try:
                    user = User.objects.get(username=username)
                    extra_info = ExtraInfo.objects.get(user=user)
                    resolved_ids.add(extra_info.id)
                except (User.DoesNotExist, ExtraInfo.DoesNotExist):
                    continue

        return resolved_ids

    @staticmethod
    def _sync_specific_recipients(announcement, resolved_ids):
        announcement.recipients.exclude(user_id__in=resolved_ids).delete()

        for user_id in resolved_ids:
            try:
                extra_info = ExtraInfo.objects.get(id=user_id)
                AnnouncementRecipients.objects.update_or_create(
                    announcement=announcement,
                    user=extra_info,
                    defaults={
                        'is_read': False,
                        'read_at': None,
                    }
                )
            except ExtraInfo.DoesNotExist:
                continue
    
    def create(self, validated_data):
        """Create announcement and add specific recipients"""
        validated_data.pop('title', None)
        validated_data.pop('content', None)
        specific_user_ids = validated_data.pop('specific_user_ids', [])
        specific_usernames = validated_data.pop('specific_usernames', [])
        
        announcement = Announcements.objects.create(**validated_data)
        
        # Add specific recipients
        if announcement.target_group == 'specific_users':
            resolved_ids = self._resolve_specific_user_ids(
                specific_user_ids=specific_user_ids,
                specific_usernames=specific_usernames,
            )
            self._sync_specific_recipients(announcement, resolved_ids)
        
        return announcement

    def update(self, instance, validated_data):
        """Update announcement and synchronize specific recipients if required."""
        validated_data.pop('title', None)
        validated_data.pop('content', None)

        specific_user_ids = validated_data.pop('specific_user_ids', None)
        specific_usernames = validated_data.pop('specific_usernames', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if instance.target_group == 'specific_users':
            should_sync = specific_user_ids is not None or specific_usernames is not None
            if should_sync:
                resolved_ids = self._resolve_specific_user_ids(
                    specific_user_ids=specific_user_ids or [],
                    specific_usernames=specific_usernames or [],
                )
                self._sync_specific_recipients(instance, resolved_ids)
        else:
            instance.recipients.all().delete()

        return instance


class NotificationModuleStatsSerializer(serializers.Serializer):
    """Serializer for notification statistics by module"""
    
    module = serializers.CharField()
    count = serializers.IntegerField()
    unread_count = serializers.IntegerField()
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
