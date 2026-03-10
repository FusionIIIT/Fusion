from rest_framework import serializers
from .models import StudentComplain, Caretaker, Warden, Complaint_Admin, Workers

class StudentComplainSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentComplain
        fields = "__all__"

class CaretakerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caretaker
        fields = '__all__'

class WardenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warden
        fields = '__all__'

class Complaint_AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint_Admin
        fields = '__all__'

class FeedbackSerializer(serializers.Serializer):
    feedback = serializers.CharField()
    rating = serializers.IntegerField()

class ResolvePendingSerializer(serializers.Serializer):
    yesorno = serializers.ChoiceField(choices=[('Yes', 'Yes'), ('No', 'No')])
    comment = serializers.CharField(required=False, allow_blank=True)
    upload_resolved = serializers.ImageField(required=False, allow_null=True)

class WorkersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workers
        fields = '__all__'
