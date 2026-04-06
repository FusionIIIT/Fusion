from rest_framework import serializers
from applications.complaint_system.models import Caretaker, StudentComplain, Supervisor, Workers
from applications.globals.models import ExtraInfo, User


COMPLAINT_FINISH_DAYS = {
    'Electricity': 2,
    'carpenter': 2,
    'plumber': 2,
    'garbage': 1,
    'dustbin': 1,
    'internet': 4,
    'other': 3,
}

class StudentComplainSerializers(serializers.ModelSerializer):

    class Meta:
        model = StudentComplain
        fields = '__all__'
        read_only_fields = ('complainer', 'complaint_date')

    def validate(self, attrs):
        # Keep default server-side values predictable even when frontend sends partial payloads.
        if self.instance is None:
            attrs.setdefault('status', 0)
            attrs.setdefault('remarks', 'Pending')
            attrs.setdefault('reason', 'None')
            attrs.setdefault('comment', 'None')

        complaint_type = attrs.get(
            'complaint_type',
            getattr(self.instance, 'complaint_type', 'other') if self.instance else 'other',
        )
        if not attrs.get('complaint_finish'):
            from datetime import timedelta
            from django.utils import timezone

            attrs['complaint_finish'] = timezone.now().date() + timedelta(
                days=COMPLAINT_FINISH_DAYS.get(complaint_type, 3)
            )

        return attrs


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