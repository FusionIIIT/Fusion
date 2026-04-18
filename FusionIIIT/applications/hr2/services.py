"""Consolidated service layer for HR2 module.

This module consolidates business logic from form management and file workflow,
providing a stable, reusable interface for both database operations and file tracking.
"""

import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from applications.hr2.constants.form_types import FormType
from applications.hr2.models import (
    Appraisalform,
    CPDAAdvanceform,
    CPDAReimbursementform,
    LeaveForm,
    LTCform,
)
from applications.filetracking.sdk.methods import (
    archive_file,
    create_file,
    forward_file,
    view_archived,
    view_history,
    view_inbox,
    view_outbox,
)


User = get_user_model()

_FORM_TYPE_TO_MODEL = {
    FormType.LTC: LTCform,
    FormType.CPDA_ADVANCE: CPDAAdvanceform,
    FormType.CPDA_REIMBURSEMENT: CPDAReimbursementform,
    FormType.LEAVE: LeaveForm,
    FormType.APPRAISAL: Appraisalform,
}


# ============================================================================
# Form Model Mapping & Lookup
# ============================================================================

def get_model_for_form_type(form_type: str):
    """Return the Django model class for a given form type."""
    return _FORM_TYPE_TO_MODEL.get(form_type)


# ============================================================================
# Date Filtering Helpers
# ============================================================================

def _get_default_date_range():
    """Return (start_date, end_date) for the current calendar year (Jan 1 - Dec 31)."""
    today = datetime.date.today()
    start = datetime.date(today.year, 1, 1)
    end = datetime.date(today.year, 12, 31)
    return start, end


def _parse_and_validate_date_params(from_date_str, to_date_str):
    """Parse and validate ISO 8601 date strings (YYYY-MM-DD).
    
    Returns:
        (from_date: date, to_date: date) on success, or (None, None) on parse error.
        Validates that from_date <= to_date.
    """
    from_date = None
    to_date = None
    
    if from_date_str:
        try:
            from_date = datetime.datetime.strptime(from_date_str.strip(), "%Y-%m-%d").date()
        except (ValueError, AttributeError):
            return None, None
    
    if to_date_str:
        try:
            to_date = datetime.datetime.strptime(to_date_str.strip(), "%Y-%m-%d").date()
        except (ValueError, AttributeError):
            return None, None
    
    # Validate range if both dates provided
    if from_date and to_date and from_date > to_date:
        return None, None
    
    return from_date, to_date


# ============================================================================
# Form Persistence & Lookup (Form Services)
# ============================================================================

def get_forms_by_creator(form_model, username: str):
    """Return a queryset (or list) of forms created by the given username."""
    user = User.objects.get(username=username)
    return form_model.objects.filter(created_by=user)


def get_form_by_id(form_model, form_id):
    """Fetch a single form by its ID."""
    return form_model.objects.get(id=form_id)


def get_forms_for_user(form_type: str, username: str, from_date: str = None, to_date: str = None):
    """Fetch forms for a user by form type, optionally filtered by date range.
    
    Args:
        form_type: The type of form (e.g., FormType.LTC, FormType.LEAVE).
        username: The username of the form creator.
        from_date: Optional start date (ISO 8601 format YYYY-MM-DD). If not provided,
                   defaults to Jan 1 of current year.
        to_date: Optional end date (ISO 8601 format YYYY-MM-DD). If not provided,
                 defaults to Dec 31 of current year.
    
    Returns:
        (forms, many) where `many` indicates whether the result is a queryset.
        - Single object (many=False) if exactly 1 result
        - List (many=True) if 0 or multiple results
    """
    model = get_model_for_form_type(form_type)
    if model is None:
        return [], True

    queryset = get_forms_by_creator(model, username)
    
    # Parse and validate date parameters; use defaults if not provided or invalid
    parsed_from_date, parsed_to_date = _parse_and_validate_date_params(from_date, to_date)
    
    # If dates were provided but invalid, return empty list (failed validation)
    if (from_date or to_date) and (parsed_from_date is None and parsed_to_date is None):
        return [], True
    
    # If no valid dates provided, use default range (current calendar year)
    if parsed_from_date is None and parsed_to_date is None:
        parsed_from_date, parsed_to_date = _get_default_date_range()
    # Handle case where only from_date was provided
    elif parsed_from_date and not parsed_to_date:
        _, parsed_to_date = _get_default_date_range()
    # Handle case where only to_date was provided
    elif parsed_to_date and not parsed_from_date:
        parsed_from_date, _ = _get_default_date_range()
    
    # Apply date range filter on submissionDate field
    queryset = queryset.filter(submissionDate__range=[parsed_from_date, parsed_to_date])

    # Keep response shape consistent with prior behavior:
    # - a single object for 1 result
    # - a list for 0 or multiple
    count = queryset.count()
    if count == 1:
        return queryset.first(), False
    return list(queryset), True


def get_form_for_type_and_id(form_type: str, form_id: int):
    """Fetch a specific form instance for the given type and id."""
    model = get_model_for_form_type(form_type)
    if model is None:
        raise ObjectDoesNotExist(f"Unknown form type: {form_type}")

    return get_form_by_id(model, form_id)


# ============================================================================
# File Workflow Operations (File Workflow Services)
# ============================================================================

def create_form_file(
    *,
    uploader: str,
    uploader_designation: str,
    receiver: str,
    receiver_designation: str,
    src_object_id: str,
    form_type: str,
    src_module: str = "HR",
    attached_file=None,
    file_extra_JSON=None,
):
    """Create a file in filetracking for a form and return the created file id."""
    extra = {"type": form_type}
    if file_extra_JSON and isinstance(file_extra_JSON, dict):
        extra.update(file_extra_JSON)
    return create_file(
        uploader=uploader,
        uploader_designation=uploader_designation,
        receiver=receiver,
        receiver_designation=receiver_designation,
        src_module=src_module,
        src_object_id=src_object_id,
        file_extra_JSON=extra,
        attached_file=attached_file,
    )


def forward_form_file(
    *,
    file_id: str,
    receiver: str,
    receiver_designation: str,
    remarks: str,
    file_extra_JSON: dict
):
    """Forward an existing file in the filetracking workflow."""
    return forward_file(
        file_id=file_id,
        receiver=receiver,
        receiver_designation=receiver_designation,
        remarks=remarks,
        file_extra_JSON=file_extra_JSON,
    )


def archive_form_file(*, file_id: str) -> bool:
    """Archive a file (soft delete) in the filetracking workflow."""
    return archive_file(file_id=file_id)


def get_inbox(*, username: str, designation: str, src_module: str = "HR"):
    """Retrieve inbox for a user."""
    return view_inbox(username=username, designation=designation, src_module=src_module)


def get_archived(*, username: str, designation: str, src_module: str = "HR"):
    """Retrieve archived files for a user."""
    return view_archived(username=username, designation=designation, src_module=src_module)


def get_outbox(*, username: str, designation: str, src_module: str = "HR"):
    """Retrieve outbox for a user."""
    return view_outbox(username=username, designation=designation, src_module=src_module)


def get_file_history(*, file_id: str):
    """Retrieve file workflow history."""
    return view_history(file_id)
