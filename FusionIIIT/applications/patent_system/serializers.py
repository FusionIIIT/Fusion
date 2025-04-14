from rest_framework import serializers
from .models import Attorney

class AttorneySerializer(serializers.ModelSerializer):
    class Meta:
        model = Attorney
        fields = ['id', 'name', 'email', 'phone', 'firm_name']
        read_only_fields = ['id'] 