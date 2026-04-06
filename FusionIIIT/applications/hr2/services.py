"""Consolidated service layer for HR2 module.

This module consolidates business logic from form management and file workflow,
providing a stable, reusable interface for both database operations and file tracking.
"""

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
# Form Persistence & Lookup (Form Services)
# ============================================================================

def get_forms_by_creator(form_model, username: str):
    """Return a queryset (or list) of forms created by the given username."""
    user = User.objects.get(username=username)
    return form_model.objects.filter(created_by=user)


def get_form_by_id(form_model, form_id):
    """Fetch a single form by its ID."""
    return form_model.objects.get(id=form_id)


def get_forms_for_user(form_type: str, username: str):
    """Fetch forms for a user by form type.

    Returns (forms, many) where `many` indicates whether the result is a queryset.
    """
    model = get_model_for_form_type(form_type)
    if model is None:
        return [], True

    queryset = get_forms_by_creator(model, username)

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
    attached_file=None
):
    """Create a file in filetracking for a form and return the created file id."""
    return create_file(
        uploader=uploader,
        uploader_designation=uploader_designation,
        receiver=receiver,
        receiver_designation=receiver_designation,
        src_module=src_module,
        src_object_id=src_object_id,
        file_extra_JSON={"type": form_type},
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
