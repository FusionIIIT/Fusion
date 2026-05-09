"""
Patent Management System — DRF Serializers + field-level validation.
"""

from rest_framework import serializers
from ..models import (
    Application, ApplicationSectionI, ApplicationSectionII,
    ApplicationSectionIII, Applicant, Inventor,
    CommunicationLog, Budget, AuditLog, Document,
    AttorneyAssignment, PatentabilityAssessment, FilingRecord,
    PatentNotification, ApplicationDocument,
)


# ---------------------------------------------------------------------------
# Applicant
# ---------------------------------------------------------------------------

class ApplicantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Applicant
        fields = ["id", "name", "email", "mobile", "address"]
        read_only_fields = ["id"]


# ---------------------------------------------------------------------------
# Inventor
# ---------------------------------------------------------------------------

class InventorSerializer(serializers.ModelSerializer):
    applicant_name = serializers.CharField(source="applicant.name", read_only=True)
    applicant_email = serializers.CharField(source="applicant.email", read_only=True)

    class Meta:
        model = Inventor
        fields = ["id", "applicant", "applicant_name", "applicant_email", "percentage_share"]
        read_only_fields = ["id"]


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

class SectionISerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationSectionI
        fields = [
            "id", "type_of_ip", "area", "problem", "objective",
            "novelty", "advantages", "is_tested", "poc_details", "applications",
        ]
        read_only_fields = ["id"]


class SectionIISerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationSectionII
        fields = [
            "id", "funding_details", "funding_source", "source_agreement",
            "publication_details", "mou_details", "mou_file", "research_details",
        ]
        read_only_fields = ["id"]


class SectionIIISerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationSectionIII
        fields = [
            "id", "company_name", "contact_person", "contact_no",
            "development_stage", "form_iii",
        ]
        read_only_fields = ["id"]


# ---------------------------------------------------------------------------
# Application (list + detail)
# ---------------------------------------------------------------------------

class ApplicationListSerializer(serializers.ModelSerializer):
    primary_applicant_name = serializers.CharField(source="primary_applicant.name", read_only=True)

    class Meta:
        model = Application
        fields = [
            "id", "title", "status", "decision_status", "token_no",
            "submitted_date", "primary_applicant_name",
        ]


class ApplicationDetailSerializer(serializers.ModelSerializer):
    section_i = SectionISerializer(source="section_i", read_only=True)
    section_ii = SectionIISerializer(source="section_ii", read_only=True)
    section_iii = SectionIIISerializer(source="section_iii", many=True, read_only=True)
    inventors = InventorSerializer(many=True, read_only=True)
    primary_applicant_name = serializers.CharField(source="primary_applicant.name", read_only=True)

    class Meta:
        model = Application
        fields = [
            "id", "title", "status", "decision_status", "token_no",
            "comments", "director_feedback",
            "submitted_date", "reviewed_by_pcc_date",
            "forwarded_to_director_date", "director_approval_date",
            "patentability_check_start_date", "patentability_check_completed_date",
            "search_report_generated_date", "patent_filed_date",
            "patent_published_date", "decision_date",
            "withdrawn_date", "resubmission_deadline",
            "last_updated_at", "created_at",
            "primary_applicant_name",
            "section_i", "section_ii", "section_iii", "inventors",
        ]


# ---------------------------------------------------------------------------
# Communication Log  (replaces Attorney)
# ---------------------------------------------------------------------------

class CommunicationLogSerializer(serializers.ModelSerializer):
    logged_by_name = serializers.CharField(source="logged_by.get_full_name", read_only=True)

    class Meta:
        model = CommunicationLog
        fields = [
            "id", "application", "logged_by", "logged_by_name",
            "direction", "subject", "body",
            "external_party_name", "external_party_email",
            "attachment", "confidentiality_level", "created_at",
        ]
        read_only_fields = ["id", "logged_by", "logged_by_name", "created_at"]

    def validate_subject(self, value):
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError("Subject must be at least 3 characters.")
        return value

    def validate_direction(self, value):
        if value not in ("Incoming", "Outgoing"):
            raise serializers.ValidationError("Direction must be 'Incoming' or 'Outgoing'.")
        return value


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------

class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = [
            "id", "application", "filing_cost", "attorney_fees",
            "administrative_cost", "total_cost", "decision",
            "decision_by", "decision_date", "remarks",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "total_cost", "decision_by", "decision_date", "created_at", "updated_at"]


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------

class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id", "application", "user", "user_name",
            "action", "previous_state", "new_state",
            "details", "timestamp",
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "title", "link", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_title(self, value):
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Title is required.")
        return value

    def validate_link(self, value):
        if not value:
            raise serializers.ValidationError("Link is required.")
        return value


# ---------------------------------------------------------------------------
# Attorney Assignment  (UC-006, BR-PMS-007)
# ---------------------------------------------------------------------------

class AttorneyAssignmentSerializer(serializers.ModelSerializer):
    assigned_by_name = serializers.CharField(source="assigned_by.get_full_name", read_only=True)

    class Meta:
        model = AttorneyAssignment
        fields = [
            "id", "application", "attorney_name", "attorney_email",
            "attorney_phone", "attorney_firm", "specialization",
            "assigned_by", "assigned_by_name", "assignment_date",
            "engagement_proof", "remarks", "is_active",
        ]
        read_only_fields = ["id", "assigned_by", "assigned_by_name", "assignment_date"]

    def validate_attorney_name(self, value):
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Attorney name must be at least 2 characters.")
        return value


# ---------------------------------------------------------------------------
# Patentability Assessment  (UC-007, BR-PMS-014)
# ---------------------------------------------------------------------------

class PatentabilityAssessmentSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.CharField(source="recorded_by.get_full_name", read_only=True)

    class Meta:
        model = PatentabilityAssessment
        fields = [
            "id", "application", "assessed_by_attorney",
            "novelty_score", "non_obviousness_score",
            "utility_score", "search_completeness",
            "recommendation", "opinion_summary",
            "prior_art_references", "attorney_report",
            "recorded_by", "recorded_by_name",
            "assessment_date", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "recorded_by", "recorded_by_name",
            "created_at", "updated_at",
        ]

    def validate_opinion_summary(self, value):
        if not value or len(value.strip()) < 20:
            raise serializers.ValidationError(
                "Opinion summary must be at least 20 characters (BR-PMS-014)."
            )
        return value


# ---------------------------------------------------------------------------
# Filing Record  (UC-009, BR-PMS-017, WF-601)
# ---------------------------------------------------------------------------

class FilingRecordSerializer(serializers.ModelSerializer):
    filed_by_name = serializers.CharField(source="filed_by.get_full_name", read_only=True)

    class Meta:
        model = FilingRecord
        fields = [
            "id", "application", "filing_office", "jurisdiction",
            "external_filing_id", "filing_date",
            "confirmation_proof", "international_filing_justification",
            "filed_by", "filed_by_name", "remarks",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "filed_by", "filed_by_name",
            "created_at", "updated_at",
        ]


# ---------------------------------------------------------------------------
# Feature 2: Inventor with Consent
# ---------------------------------------------------------------------------

class InventorWithConsentSerializer(serializers.ModelSerializer):
    applicant_name = serializers.CharField(source="applicant.name", read_only=True)
    applicant_email = serializers.CharField(source="applicant.email", read_only=True)

    class Meta:
        model = Inventor
        fields = [
            "id", "applicant", "applicant_name", "applicant_email",
            "percentage_share", "has_consent", "consent_date",
        ]
        read_only_fields = ["id", "has_consent", "consent_date"]


# ---------------------------------------------------------------------------
# Feature 4: Patent Notification
# ---------------------------------------------------------------------------

class PatentNotificationSerializer(serializers.ModelSerializer):
    application_title = serializers.CharField(source="application.title", read_only=True)

    class Meta:
        model = PatentNotification
        fields = [
            "id", "recipient", "application", "application_title",
            "notification_type", "title", "message",
            "is_read", "deadline_date", "action_url", "created_at",
        ]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Feature 5: Application Document (Version Control)
# ---------------------------------------------------------------------------

class ApplicationDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source="uploaded_by.get_full_name", read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationDocument
        fields = [
            "id", "application", "document_type", "title",
            "file", "file_url", "version", "description",
            "uploaded_by", "uploaded_by_name", "is_current", "created_at",
        ]
        read_only_fields = ["id", "version", "is_current", "uploaded_by", "uploaded_by_name", "created_at"]

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None
