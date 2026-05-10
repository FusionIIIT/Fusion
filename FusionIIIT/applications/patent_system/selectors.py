from django.db.models import Count, Q

from .models import (
	Application,
	AuditLog,
	BudgetApproval,
	CommunicationLog,
	Document,
	DocumentVersion,
	ExternalFilingRecord,
	InventorConsent,
	LicensingRequest,
	MaintenanceSchedule,
	NotificationEvent,
	OfficeAction,
	PriorArtReference,
	AppealRequest,
	LegalAdviceMemo,
	LegalAssessment,
	Attorney,
)


def applicant_applications(applicant):
	return (
		Application.objects.filter(Q(primary_applicant=applicant) | Q(associatedwith__applicant=applicant))
		.select_related("attorney")
		.distinct()
		.order_by("-last_updated_at")
	)


def applications_by_status(statuses):
	return Application.objects.filter(status__in=statuses).select_related("primary_applicant")


def applications_by_decision_status(statuses):
	return Application.objects.filter(decision_status__in=statuses).select_related("primary_applicant")


def get_communication_logs(application):
	return application.communication_logs.select_related("logged_by").all()


def get_budget_approvals(application):
	return application.budget_approvals.all()


def get_office_actions(application):
	return application.office_actions.all()


def get_prior_art_references(application):
	return application.prior_art_references.all()


def get_legal_assessments(application):
	return application.legal_assessments.all()


def get_legal_advice_memos(application):
	return application.legal_memos.all()


def get_licensing_requests(application):
	return application.licensing_requests.all()


def get_inventor_consents(application):
	return application.inventor_consents.all()


def get_maintenance_schedules(application):
	return application.maintenance_schedules.all()


def get_appeal_requests(application):
	return application.appeals.all()


def get_external_filing_records(application):
	return application.external_filings.all()


def get_conflict_declarations(application):
	return application.conflict_declarations.all()


def get_documents(application):
	return application.documents.all()


def get_document_versions(document):
	return document.versions.all()


def get_attorney_applications(attorney):
	return Application.objects.filter(attorney=attorney).values("id", "title", "status")


def get_pcc_admin_queue():
	return Application.objects.filter(status__in=["Submitted", "Needs Revision"]).select_related("primary_applicant", "assigned_pcc_admin")


def get_director_queue():
	return Application.objects.filter(
		status__in=["Forwarded for Director's Review", "Returned to Director"]
	).select_related("primary_applicant", "assigned_pcc_admin", "attorney")


def count_by_status(statuses):
	return Application.objects.filter(status__in=statuses).values("status").annotate(count=Count("id"))


def count_by_decision_status(statuses):
	return Application.objects.filter(decision_status__in=statuses).values("decision_status").annotate(count=Count("id"))
