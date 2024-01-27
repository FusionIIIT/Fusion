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

    def validate_upload_file(self, value):
        print('wow')
        if not value:
            # handles empty file paths
            value = None
        else:
            if isinstance(value, str):
                with open(value, 'rb') as file:
                    value = DjangoFile(file)

            max_file_size = 10 * 1024 * 1024  # 10 MB
            if value.size > max_file_size:
                raise serializers.ValidationError(
                    "File size exceeds the limit (10 MB).")
        return value


class FileHeaderSerializer(serializers.ModelSerializer):
    '''
    This serializes everything except the attachments of a file and whether it is read or not
    '''
    class Meta:
        model = File
        fields = [
            'uploader',
            'designation',
            'subject',
            'description',
            'upload_date']
