from django.contrib import admin
from .models import (
    Applicant, Application, ApplicationSectionI, ApplicationSectionII,
    ApplicationSectionIII, Inventor, CommunicationLog, Budget, AuditLog, Document,
    AttorneyAssignment, PatentabilityAssessment, FilingRecord,
)


class InventorInline(admin.TabularInline):
    model = Inventor
    extra = 0


class SectionIInline(admin.StackedInline):
    model = ApplicationSectionI
    extra = 0


class SectionIIInline(admin.StackedInline):
    model = ApplicationSectionII
    extra = 0


class SectionIIIInline(admin.TabularInline):
    model = ApplicationSectionIII
    extra = 0


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "decision_status", "primary_applicant", "submitted_date")
    list_filter = ("status", "decision_status")
    search_fields = ("title", "token_no")
    inlines = [InventorInline, SectionIInline, SectionIIInline, SectionIIIInline]


@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "user")
    search_fields = ("name", "email")


@admin.register(CommunicationLog)
class CommunicationLogAdmin(admin.ModelAdmin):
    list_display = ("id", "application", "direction", "subject", "logged_by", "created_at")
    list_filter = ("direction",)


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("id", "application", "total_cost", "decision")
    list_filter = ("decision",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "application", "action", "user", "timestamp")
    list_filter = ("action",)
    readonly_fields = ("application", "user", "action", "previous_state", "new_state", "details", "timestamp")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "link", "created_at")


@admin.register(AttorneyAssignment)
class AttorneyAssignmentAdmin(admin.ModelAdmin):
    list_display = ("id", "application", "attorney_name", "attorney_firm", "assigned_by", "assignment_date", "is_active")
    list_filter = ("is_active",)
    search_fields = ("attorney_name", "attorney_firm", "attorney_email")


@admin.register(PatentabilityAssessment)
class PatentabilityAssessmentAdmin(admin.ModelAdmin):
    list_display = ("id", "application", "assessed_by_attorney", "recommendation", "assessment_date")
    list_filter = ("recommendation",)
    search_fields = ("assessed_by_attorney", "opinion_summary")


@admin.register(FilingRecord)
class FilingRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "application", "filing_office", "jurisdiction", "external_filing_id", "filing_date")
    list_filter = ("filing_office", "jurisdiction")
    search_fields = ("external_filing_id",)
