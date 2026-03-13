"""Write-oriented business logic for iwdModuleV2."""

from decimal import Decimal
from decimal import InvalidOperation

from .models import Budget
from .models import Requests
from .selectors import get_latest_bill_for_request
from .selectors import get_request_by_id


class ServiceError(Exception):
    """Base exception for service-level errors."""


class NotFoundError(ServiceError):
    """Raised when a requested entity is missing."""


class ValidationError(ServiceError):
    """Raised for invalid function inputs."""


class WorkflowError(ServiceError):
    """Raised when workflow preconditions are not satisfied."""


def _to_non_negative_decimal(value, field_name):
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(f"{field_name} must be a valid decimal value")
    if parsed < 0:
        raise ValidationError(f"{field_name} must be non-negative")
    return parsed


def mark_work_completed(request_id):
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        raise NotFoundError("Request not found")

    request_obj.workCompleted = 1
    request_obj.status = "Work Completed"
    request_obj.save(update_fields=["workCompleted", "status"])
    return request_obj


def mark_bill_audited(request_id):
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        raise NotFoundError("Request not found")

    latest_bill = get_latest_bill_for_request(request_id)
    if not latest_bill:
        raise WorkflowError("No bill found for request")

    latest_bill.audit = True
    latest_bill.save(update_fields=["audit"])

    request_obj.status = "Bill Audited"
    request_obj.save(update_fields=["status"])
    return request_obj


def settle_bill(request_id):
    request_obj = get_request_by_id(request_id)
    if not request_obj:
        raise NotFoundError("Request not found")

    latest_bill = get_latest_bill_for_request(request_id)
    if not latest_bill:
        raise WorkflowError("No bill found for request")
    if not latest_bill.audit or request_obj.status != "Bill Audited":
        raise WorkflowError("Bill must be audited before settlement")

    latest_bill.settle = True
    latest_bill.save(update_fields=["settle"])

    request_obj.billSettled = 1
    request_obj.status = "Final Bill Settled"
    request_obj.save(update_fields=["billSettled", "status"])
    return request_obj


def create_budget(name, amount):
    if not name or not str(name).strip():
        raise ValidationError("name is required")
    validated_amount = _to_non_negative_decimal(amount, "budget")
    return Budget.objects.create(name=str(name).strip(), budgetIssued=validated_amount)


def update_budget(budget_id, name, amount):
    budget_obj = Budget.objects.filter(id=budget_id).first()
    if not budget_obj:
        raise NotFoundError("Budget not found")
    if not name or not str(name).strip():
        raise ValidationError("name is required")

    validated_amount = _to_non_negative_decimal(amount, "budget")
    budget_obj.name = str(name).strip()
    budget_obj.budgetIssued = validated_amount
    budget_obj.save(update_fields=["name", "budgetIssued"])
    return budget_obj
