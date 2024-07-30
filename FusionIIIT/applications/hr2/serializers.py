from rest_framework import serializers
from .models import LTCform, CPDAAdvanceform, CPDAReimbursementform, Leaveform, Appraisalform

class LTC_serializer(serializers.ModelSerializer):
    class Meta:
        model = LTCform
        fields = '__all__'

    def create(self, validated_data):
        return LTCform.objects.create(**validated_data)

class CPDAAdvance_serializer(serializers.ModelSerializer):
    class Meta:
        model = CPDAAdvanceform
        fields = '__all__'

    def create(self, validated_data):
        return CPDAAdvanceform.objects.create(**validated_data)

class Appraisal_serializer(serializers.ModelSerializer):
    class Meta:
        model = Appraisalform
        fields = '__all__'

    def create(self, validated_data):
        return Appraisalform.objects.create(**validated_data)

class CPDAReimbursement_serializer(serializers.ModelSerializer):
    class Meta:
        model = CPDAReimbursementform
        fields = '__all__'

    def create(self, validated_data):
        return CPDAReimbursementform.objects.create(**validated_data)

class Leave_serializer(serializers.ModelSerializer):
    class Meta:
        model = Leaveform
        fields = '__all__'

    def create(self, validated_data):
        return Leaveform.objects.create(**validated_data)