from rest_framework import serializers
from ..models import (
    AppealRequest,
    Attorney,
    AuditLog,
    BudgetApproval,
    CommunicationLog,
    ConflictDeclaration,
    Document,
    DocumentVersion,
    ExternalFilingRecord,
    InventorConsent,
    LegalAdviceMemo,
    LegalAssessment,
    LicensingRequest,
    MaintenanceSchedule,
    NotificationEvent,
    OfficeAction,
    OfficeActionResponse,
    PriorArtReference,
)

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


class CommunicationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunicationLog
        fields = '__all__'
        read_only_fields = ['id', 'application', 'logged_by', 'created_at', 'updated_at']


class ConflictDeclarationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConflictDeclaration
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class LegalAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalAssessment
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class NotificationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationEvent
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class BudgetApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetApproval
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'decided_at']


class ExternalFilingRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalFilingRecord
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class MaintenanceScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceSchedule
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'reminder_sent_at', 'paid_at']


class DocumentVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentVersion
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class InventorConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventorConsent
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class OfficeActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfficeAction
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class OfficeActionResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfficeActionResponse
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class LicensingRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LicensingRequest
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class AppealRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppealRequest
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class PriorArtReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriorArtReference
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class LegalAdviceMemoSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalAdviceMemo
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at']