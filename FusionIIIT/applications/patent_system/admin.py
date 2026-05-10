from django.contrib import admin, messages
from django.db import transaction

# Ensure globals admin registrations are loaded before we attach actions.
import applications.globals.admin  # noqa: F401
from applications.globals.models import Designation, ExtraInfo, HoldsDesignation

from .models import (
    Applicant,
    Application,
    ApplicationSectionI,
    ApplicationSectionII,
    ApplicationSectionIII,
    AssociatedWith,
    Attorney,
    BudgetApproval,
    CommunicationLog,
    ConflictDeclaration,
    Document,
    DocumentVersion,
    ExternalFilingRecord,
    InventorConsent,
    LegalAssessment,
    MaintenanceSchedule,
    NotificationEvent,
    OfficeAction,
    OfficeActionResponse,
)


def _get_or_create_designation(name, full_name, designation_type):
    designation = Designation.objects.filter(name__iexact=name).first()
    if designation:
        updated = False
        if not designation.full_name:
            designation.full_name = full_name
            updated = True
        if not designation.type:
            designation.type = designation_type
            updated = True
        if updated:
            designation.save(update_fields=["full_name", "type"])
        return designation

    return Designation.objects.create(
        name=name,
        full_name=full_name,
        type=designation_type,
    )


def _assign_designation_to_user(user, designation):
    # Keep working=user so middleware and role switching stay consistent.
    _, created = HoldsDesignation.objects.get_or_create(
        user=user,
        designation=designation,
        defaults={"working": user},
    )
    return created


def assign_patent_director_and_pcc_admin(modeladmin, request, queryset):
    """Assign Director + PCC Admin role(s) to selected user(s)"""
    director_designation = _get_or_create_designation(
        name="Director",
        full_name="Director",
        designation_type="administrative",
    )
    pcc_admin_designation = _get_or_create_designation(
        name="PCC Admin",
        full_name="PCC Admin",
        designation_type="administrative",
    )

    users = [obj.user for obj in queryset.select_related("user")]
    if not users:
        modeladmin.message_user(request, "No users selected.", level=messages.WARNING)
        return

    director_created_count = 0
    pcc_created_count = 0

    with transaction.atomic():
        for user in users:
            if _assign_designation_to_user(user, director_designation):
                director_created_count += 1
            if _assign_designation_to_user(user, pcc_admin_designation):
                pcc_created_count += 1

    modeladmin.message_user(
        request,
        (
            f"Processed {len(users)} user(s). "
            f"New Director assignments: {director_created_count}. "
            f"New PCC Admin assignments: {pcc_created_count}."
        ),
        level=messages.SUCCESS,
    )


assign_patent_director_and_pcc_admin.short_description = "Patent: assign Director + PCC Admin role(s)"


# Attach role-assignment action to already-registered ExtraInfo admin safely.
extra_info_admin = admin.site._registry.get(ExtraInfo)
if extra_info_admin:
    existing_actions = list(getattr(extra_info_admin, "actions", []) or [])
    if assign_patent_director_and_pcc_admin not in existing_actions:
        existing_actions.append(assign_patent_director_and_pcc_admin)
        extra_info_admin.actions = existing_actions


# Register patent-system models for admin visibility.
PATENT_MODELS = [
    Applicant,
    Attorney,
    Application,
    ApplicationSectionI,
    ApplicationSectionII,
    ApplicationSectionIII,
    AssociatedWith,
    Document,
    CommunicationLog,
    ConflictDeclaration,
    LegalAssessment,
    NotificationEvent,
    BudgetApproval,
    ExternalFilingRecord,
    MaintenanceSchedule,
    DocumentVersion,
    InventorConsent,
    OfficeAction,
    OfficeActionResponse,
]

for model in PATENT_MODELS:
    if model not in admin.site._registry:
        admin.site.register(model)
