from rest_framework import serializers
from applications.complaint_system.models import (
    Caretaker,
    ComplaintEvent,
    ComplaintPriority,
    ComplaintStatus,
    StudentComplain,
    VerificationStatus,
    Supervisor,
    Workers,
)
from applications.globals.models import ExtraInfo, User


COMPLAINT_SLA_HOURS = {
    ComplaintPriority.URGENT: 24,
    ComplaintPriority.STANDARD: 72,
    ComplaintPriority.LOW: 168,
}

ALLOWED_ATTACHMENT_TYPES = {
    'image/jpeg',
    'image/png',
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}

MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024

class StudentComplainSerializers(serializers.ModelSerializer):
    assigned_to_name = serializers.SerializerMethodField()
    status_label = serializers.SerializerMethodField()
    verification_status_label = serializers.SerializerMethodField()
    reopen_allowed_until = serializers.SerializerMethodField()
    reopen_window_open = serializers.SerializerMethodField()

    class Meta:
        model = StudentComplain
        fields = '__all__'
        read_only_fields = (
            'complainer',
            'complaint_date',
            'complaint_ref',
            'submitted_at',
            'sla_deadline',
            'assigned_to',
            'assigned_team',
            'resolved_at',
            'closed_at',
            'verification_status',
            'verification_source',
            'verification_notes',
            'reopen_requested_at',
            'reopened_at',
            'updated_at',
            'progress_notes',
            'progress_attachment',
            'estimated_resolution_time',
        )

    def validate(self, attrs):
        from datetime import timedelta
        from django.utils import timezone

        draft_mode = bool(
            self.context.get('draft_mode')
            or attrs.get('is_draft')
            or (self.instance is not None and getattr(self.instance, 'is_draft', False))
        )

        def _is_empty(value):
            return value is None or (isinstance(value, str) and not value.strip())

        # Keep default server-side values predictable even when frontend sends partial payloads.
        if self.instance is None:
            required_fields = {
                'complaint_type': 'Category is required',
                'location': 'Location is required',
                'details': 'Description is required',
            }
            if not draft_mode:
                for field, message in required_fields.items():
                    if _is_empty(attrs.get(field)):
                        raise serializers.ValidationError({field: message})

            priority = attrs.get('priority', ComplaintPriority.STANDARD)
            if priority not in dict(ComplaintPriority.CHOICES):
                raise serializers.ValidationError({'priority': 'Invalid priority'})

            attrs.setdefault('complaint_type', 'internet')  # Use valid complaint type, not priority
            attrs.setdefault('status', ComplaintStatus.PENDING)
            attrs.setdefault('remarks', 'Pending')
            attrs.setdefault('reason', 'None')
            attrs.setdefault('comment', 'None')
            attrs.setdefault('priority', ComplaintPriority.STANDARD)
            attrs.setdefault('is_draft', draft_mode)
            # In draft mode, allow empty details
            if draft_mode and 'details' not in attrs:
                attrs['details'] = ''
            priority = attrs['priority']
            if not draft_mode:
                attrs['sla_deadline'] = timezone.now() + timedelta(hours=COMPLAINT_SLA_HOURS.get(priority, 72))
                attrs.setdefault('submitted_at', timezone.now())
            else:
                attrs['sla_deadline'] = None
                attrs['complaint_finish'] = None
        else:
            for field, message in {
                'complaint_type': 'Category cannot be empty',
                'location': 'Location cannot be empty',
                'details': 'Description cannot be empty',
            }.items():
                if not draft_mode and field in attrs and _is_empty(attrs.get(field)):
                    raise serializers.ValidationError({field: message})

        if 'priority' in attrs:
            if attrs.get('priority') not in dict(ComplaintPriority.CHOICES):
                raise serializers.ValidationError({'priority': 'Invalid priority'})

        if self.instance is not None and 'priority' in attrs and 'sla_deadline' not in attrs and not draft_mode:
            priority = attrs.get('priority', getattr(self.instance, 'priority', ComplaintPriority.STANDARD))
            attrs['sla_deadline'] = timezone.now() + timedelta(hours=COMPLAINT_SLA_HOURS.get(priority, 72))

        if not attrs.get('complaint_finish') and attrs.get('sla_deadline'):
            attrs['complaint_finish'] = attrs['sla_deadline'].date()

        return attrs

    def _validate_attachment(self, file_obj, field_label):
        if file_obj is None:
            return file_obj

        content_type = getattr(file_obj, 'content_type', None)
        if content_type not in ALLOWED_ATTACHMENT_TYPES:
            raise serializers.ValidationError(
                f'{field_label} must be JPG, PNG, PDF, or DOCX'
            )

        file_size = getattr(file_obj, 'size', 0) or 0
        if file_size > MAX_ATTACHMENT_SIZE:
            raise serializers.ValidationError(
                f'{field_label} must be 5 MB or smaller'
            )

        return file_obj

    def validate_upload_complaint(self, value):
        return self._validate_attachment(value, 'upload_complaint')

    def validate_progress_attachment(self, value):
        return self._validate_attachment(value, 'progress_attachment')

    def get_assigned_to_name(self, obj):
        if obj.assigned_to_id and obj.assigned_to:
            return obj.assigned_to.name
        if obj.worker_id_id and obj.worker_id:
            return obj.worker_id.name
        return ''

    def get_status_label(self, obj):
        return dict(ComplaintStatus.CHOICES).get(obj.status, 'Unknown')

    def get_verification_status_label(self, obj):
        return dict(VerificationStatus.CHOICES).get(obj.verification_status, obj.verification_status)

    def get_reopen_allowed_until(self, obj):
        from datetime import timedelta
        from django.utils import timezone

        reference_time = obj.closed_at or obj.resolved_at or obj.updated_at or obj.complaint_date
        if not reference_time:
            return None
        return (reference_time + timedelta(days=7)).isoformat() if reference_time else None

    def get_reopen_window_open(self, obj):
        from datetime import timedelta
        from django.utils import timezone

        reference_time = obj.closed_at or obj.resolved_at or obj.updated_at or obj.complaint_date
        if not reference_time:
            return False
        return timezone.now() <= (reference_time + timedelta(days=7))


class WorkersSerializers(serializers.ModelSerializer):
    class Meta:
        model = Workers
        fields = '__all__'


class CaretakerSerializers(serializers.ModelSerializer):
    class Meta:
        model = Caretaker
        fields = '__all__'


class SupervisorSerializers(serializers.ModelSerializer):
    class Meta:
        model = Supervisor
        fields = '__all__'


class ExtraInfoSerializers(serializers.ModelSerializer):
    class Meta:
        model = ExtraInfo
        fields = ('id', 'user', 'user_type', 'department')


class UserSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'is_superuser')


class ComplaintEventSerializer(serializers.ModelSerializer):
    actor = ExtraInfoSerializers(read_only=True)
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = ComplaintEvent
        fields = '__all__'

    def get_actor_name(self, obj):
        if obj.actor and obj.actor.user:
            return obj.actor.user.username
        return 'System'