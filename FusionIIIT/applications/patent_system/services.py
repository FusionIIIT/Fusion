import logging
from decimal import Decimal
from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from django.utils.timezone import now
from django.contrib.auth.models import User

from applications.globals.models import HoldsDesignation

from .models import (
	Applicant,
	Application,
	AuditLog,
	Attorney,
	BudgetApproval,
	NotificationEvent,
)

logger = logging.getLogger(__name__)


def role_names_for_user(user):
	names = set(
		HoldsDesignation.objects.filter(user=user).values_list("designation__name", flat=True)
	)
	return {name.lower() for name in names if name}


def is_pcc_admin_user(user):
	role_names = role_names_for_user(user)
	return any("pcc" in role and "admin" in role for role in role_names)


def is_director_user(user):
	role_names = role_names_for_user(user)
	return any("director" in role for role in role_names)


def get_director_users():
	return User.objects.filter(
		holds_designations__designation__name__icontains="director",
		is_active=True,
	).distinct()


def is_authorized_applicant_user(user):
	role_names = role_names_for_user(user)
	allowed_roles = {
		"student",
		"alumini",
		"professor",
		"associate professor",
		"assistant professor",
		"research engineer",
		"faculty",
	}
	return bool(role_names & allowed_roles) or Applicant.objects.filter(user=user).exists()


def get_attorney_for_user(user):
	if not user or not user.email:
		return None
	attorney = Attorney.objects.filter(email__iexact=user.email).first()
	if attorney:
		return attorney
	full_name = user.get_full_name().strip()
	if full_name:
		attorney = Attorney.objects.filter(name__iexact=full_name).first()
	return attorney


def is_attorney_user(user):
	role_names = role_names_for_user(user)
	if any("attorney" in role for role in role_names):
		return True
	return get_attorney_for_user(user) is not None


def require_comments(payload, key="comments"):
	comments = (payload.get(key) or "").strip()
	if not comments:
		raise ValueError("Comments are required.")
	if len(comments) > 1000:
		raise ValueError("Comments too long. Max 1000 characters allowed.")
	return comments


def create_audit(action, actor, application=None, details=""):
	AuditLog.objects.create(action=action, actor=actor, application=application, details=details)


def notify(application, message, recipient=None, recipient_role=None, event_type="General", due_date=None):
	NotificationEvent.objects.create(
		application=application,
		recipient=recipient,
		recipient_role=recipient_role,
		event_type=event_type,
		message=message,
		due_date=due_date,
	)


def reviewer_workload(user):
	return Application.objects.filter(
		assigned_pcc_admin=user,
		status__in=["Submitted", "Reviewed by PCC Admin", "Needs Revision"],
	).count()


def move_application_to_revision(application, comments, actor):
	application.status = "Needs Revision"
	application.revision_requested_at = now()
	application.revision_due_date = (now() + timedelta(days=60)).date()
	application.is_revision_locked = False
	application.comments = comments
	application.assigned_pcc_admin = actor
	application.save()
	return application


def record_budget_request(application, requested_by, amount, threshold, comments=""):
	serializer_data = {
		"application": application.id,
		"requested_by": requested_by.id,
		"amount": Decimal(str(amount)),
		"threshold": Decimal(str(threshold)),
		"status": "Pending",
		"comments": comments,
	}
	budget = BudgetApproval.objects.create(**serializer_data)
	application.budget_status = "Pending Approval"
	application.budget_estimate = serializer_data["amount"]
	application.save(update_fields=["budget_status", "budget_estimate", "last_updated_at"])
	return budget
