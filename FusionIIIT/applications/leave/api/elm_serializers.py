from django.contrib.auth.models import User
from rest_framework import serializers


class ELMApplicationSerializer(serializers.Serializer):
    CATEGORIES = (('CL', 'Casual Leave'), ('RH', 'Restricted Holiday'),
                 ('SCL', 'Special Casual Leave'), ('EL', 'Earned Leave'),
                 ('COL', 'Commuted Leave'), ('VL', 'Vacation Leave'))
    category = serializers.ChoiceField(choices=CATEGORIES)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    purpose = serializers.CharField(max_length=500)
    start_half = serializers.BooleanField(required=False, default=False)
    end_half = serializers.BooleanField(required=False, default=False)
    substitute = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(extrainfo__user_type__in=('faculty', 'staff'), is_active=True),
        required=False, allow_null=True)
    station_leave = serializers.BooleanField(required=False, default=False)
    station_details = serializers.CharField(max_length=500, required=False, allow_blank=True)
    medical_evidence = serializers.FileField(required=False, allow_null=True)

    def validate(self, attrs):
        if attrs['start_date'] > attrs['end_date']:
            raise serializers.ValidationError({'end_date': 'End date must not precede start date.'})
        if attrs.get('station_leave') and not attrs.get('station_details'):
            raise serializers.ValidationError({'station_details': 'Enter details when Station Leave is selected.'})
        return attrs


class ELMTaskDecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=(
        ('accept', 'Accept'), ('decline', 'Decline'), ('recommend', 'Recommend'),
        ('not_recommend', 'Not recommended'), ('forward', 'Forward'),
        ('approve', 'Approve'), ('reject', 'Reject'), ('verify', 'Verify')))
    remark = serializers.CharField(required=False, allow_blank=True, max_length=500)
