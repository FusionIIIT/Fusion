from applications.filetracking.models import File, Tracking
from django.core.files import File as DjangoFile
from rest_framework import serializers


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = '__all__'


class TrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tracking
        fields = '__all__'


class FileHeaderSerializer(serializers.ModelSerializer):
    '''
    This serializes everything except the attachments of a file and whether it is read or not
    '''
    class Meta:
        model = File
        exclude = ['upload_file', 'is_read']
