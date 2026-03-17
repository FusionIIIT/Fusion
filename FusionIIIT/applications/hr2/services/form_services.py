"""Service layer for HR form persistence and lookup.

The goal is to keep database access logic out of views and provide a stable,
reusable interface for fetching and updating form instances.
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


User = get_user_model()

_FORM_TYPE_TO_MODEL = {
    FormType.LTC: LTCform,
    FormType.CPDA_ADVANCE: CPDAAdvanceform,
    FormType.CPDA_REIMBURSEMENT: CPDAReimbursementform,
    FormType.LEAVE: LeaveForm,
    FormType.APPRAISAL: Appraisalform,
}


def get_model_for_form_type(form_type: str):
    """Return the Django model class for a given form type."""

    return _FORM_TYPE_TO_MODEL.get(form_type)


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
