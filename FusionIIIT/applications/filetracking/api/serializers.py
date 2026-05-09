from rest_framework import serializers

from applications.filetracking.models import (
    DraftFile,
    File,
    FileAttachment,
    FileMovement,
    FileType,
)


class FileTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileType
        fields = ['id', 'name', 'category', 'description', 'is_active']


class FileAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.CharField(source='uploaded_by.user.username', read_only=True)

    class Meta:
        model = FileAttachment
        fields = ['id', 'name', 'document', 'uploaded_by', 'uploaded_at', 'description']


class FileMovementSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source='sender.user.username', read_only=True)
    receiver = serializers.SerializerMethodField()
    sender_designation = serializers.CharField(source='sender_designation.name', read_only=True)
    receiver_designation = serializers.SerializerMethodField()

    class Meta:
        model = FileMovement
        fields = [
            'id',
            'action',
            'sender',
            'receiver',
            'sender_designation',
            'receiver_designation',
            'remarks',
            'timestamp',
        ]

    def get_receiver(self, obj):
        return obj.receiver.user.username if obj.receiver and obj.receiver.user else ''

    def get_receiver_designation(self, obj):
        return obj.receiver_designation.name if obj.receiver_designation else ''


class FileSerializer(serializers.ModelSerializer):
    file_type = FileTypeSerializer(read_only=True)
    created_by = serializers.CharField(source='created_by.user.username', read_only=True)
    current_holder = serializers.CharField(source='current_holder.user.username', read_only=True)
    current_designation = serializers.CharField(source='current_designation.name', read_only=True)
    current_department = serializers.CharField(source='current_department.name', read_only=True)
    source_department = serializers.CharField(source='source_department.name', read_only=True)
    attachments = FileAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = File
        fields = [
            'id',
            'file_number',
            'file_type',
            'subject',
            'description',
            'status',
            'priority',
            'created_at',
            'created_by',
            'source_department',
            'current_holder',
            'current_designation',
            'current_department',
            'attachments',
        ]


class DraftFileSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source='created_by.user.username', read_only=True)
    file_type = FileTypeSerializer(read_only=True)

    class Meta:
        model = DraftFile
        fields = [
            'id',
            'created_by',
            'file_type',
            'subject',
            'description',
            'created_at',
            'updated_at',
            'draft_data',
        ]
