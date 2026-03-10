from rest_framework import serializers
from .models import Attorney, Document

class AttorneySerializer(serializers.ModelSerializer):
    class Meta:
        model = Attorney
        fields = ['id', 'name', 'email', 'phone', 'firm_name']
        read_only_fields = ['id']

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'title', 'link', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at'] 