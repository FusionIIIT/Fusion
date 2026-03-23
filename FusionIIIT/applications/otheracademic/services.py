"""
Services layer for otheracademic module.
Contains all business logic and write operations.
Views should call these services instead of containing business logic directly.
"""
from datetime import date
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from applications.otheracademic.models import (
    LeaveFormTable,
    LeavePG,
    BonafideFormTableUpdated,
    AssistantshipClaimFormStatusUpd,
    NoDues,
    LeaveStatusChoices,
    LeaveTypeChoices,
)
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from applications.filetracking.sdk.methods import create_file
from notification.views import otheracademic_notif

from . import selectors


class LeaveServiceError(Exception):
    """Custom exception for leave-related service errors."""
    pass


class BonafideServiceError(Exception):
    """Custom exception for bonafide-related service errors."""
    pass


class AssistantshipServiceError(Exception):
    """Custom exception for assistantship-related service errors."""
    pass


# ==================== LEAVE SERVICES ====================

def submit_ug_leave(
    user,
    date_from,
    date_to,
    leave_type,
    address,
    purpose,
    hod_credential,
    semester,
    mobile_number=None,
    parents_mobile=None,
    mobile_during_leave=None,
    upload_file=None,
):
    """
    Submit a UG leave application.
    Creates leave record, file tracking, and sends notification to HOD.
    """
    # Validate HOD exists
    hod_user = selectors.get_user_by_username(hod_credential)
    if not hod_user:
        raise LeaveServiceError(f"HOD with username '{hod_credential}' not found.")

    # Create leave record
    leave = LeaveFormTable.objects.create(
        student_name=f"{user.first_name}{user.last_name}",
        roll_no=user.extrainfo,
        date_from=date_from,
        date_to=date_to,
        leave_type=leave_type,
        upload_file=upload_file,
        address=address,
        purpose=purpose,
        date_of_application=date.today(),
        stud_mobile_no=mobile_number,
        parent_mobile_no=parents_mobile,
        leave_mobile_no=mobile_during_leave,
        curr_sem=int(semester) if semester else None,
        hod=hod_credential,
    )

    # Get uploader designation for file tracking
    uploader_designation = selectors.get_first_designation_for_user(user)

    # Create file tracking record
    create_file(
        uploader=user.username,
        uploader_designation=uploader_designation,
        receiver=hod_user,
        receiver_designation="student",
        src_module="otheracademic",
        src_object_id=leave.id,
        file_extra_JSON={"value": 2},
        attached_file=None,
        subject='ug_leave'
    )

    # Send notification to HOD
    otheracademic_notif(user, hod_user, 'ug_leave_hod', leave.id, 'student', "A new leave application")

    return leave


def submit_pg_leave(
    user,
    date_from,
    date_to,
    leave_type,
    address,
    purpose,
    hod_credential,
    ta_supervisor_credential,
    thesis_supervisor_credential,
    semester,
    mobile_number=None,
    parents_mobile=None,
    mobile_during_leave=None,
    upload_file=None,
):
    """
    Submit a PG leave application.
    Creates leave record, file tracking, and sends notification to TA supervisor.
    """
    # Validate all supervisors exist
    ta_user = selectors.get_user_by_username(ta_supervisor_credential)
    if not ta_user:
        raise LeaveServiceError(f"TA Supervisor with username '{ta_supervisor_credential}' not found.")

    thesis_user = selectors.get_user_by_username(thesis_supervisor_credential)
    if not thesis_user:
        raise LeaveServiceError(f"Thesis Supervisor with username '{thesis_supervisor_credential}' not found.")

    hod_user = selectors.get_user_by_username(hod_credential)
    if not hod_user:
        raise LeaveServiceError(f"HOD with username '{hod_credential}' not found.")

    # Create leave record
    leave = LeavePG.objects.create(
        student_name=f"{user.first_name}{user.last_name}",
        roll_no=user.extrainfo,
        date_from=date_from,
        date_to=date_to,
        leave_type=leave_type,
        upload_file=upload_file,
        address=address,
        purpose=purpose,
        date_of_application=date.today(),
        stud_mobile_no=mobile_number,
        parent_mobile_no=parents_mobile,
        leave_mobile_no=mobile_during_leave,
        curr_sem=int(semester) if semester else None,
        hod=hod_credential,
        ta_supervisor=ta_supervisor_credential,
        thesis_supervisor=thesis_supervisor_credential,
    )

    # Get uploader designation for file tracking
    uploader_designation = selectors.get_first_designation_for_user(user)

    # Create file tracking record
    create_file(
        uploader=user.username,
        uploader_designation=uploader_designation,
        receiver=hod_user,
        receiver_designation="student",
        src_module="otheracademic",
        src_object_id=leave.id,
        file_extra_JSON={"value": 2},
        attached_file=None,
        subject='pg_leave'
    )

    # Send notification to TA supervisor
    otheracademic_notif(user, ta_user, 'pg_leave_at', leave.id, 'student', "A new leave application")

    return leave


def update_ug_leave_status(approved_ids, rejected_ids):
    """Update status of UG leave requests (by HOD)."""
    if approved_ids:
        LeaveFormTable.objects.filter(id__in=approved_ids).update(status=LeaveStatusChoices.APPROVED)
    if rejected_ids:
        LeaveFormTable.objects.filter(id__in=rejected_ids).update(status=LeaveStatusChoices.REJECTED)


def update_pg_leave_status_hod(approved_ids, rejected_ids):
    """Update status of PG leave requests (by HOD - final approval)."""
    if approved_ids:
        LeavePG.objects.filter(id__in=approved_ids).update(status=LeaveStatusChoices.APPROVED)
    if rejected_ids:
        LeavePG.objects.filter(id__in=rejected_ids).update(status=LeaveStatusChoices.REJECTED)


def update_pg_leave_status_ta(approved_ids, rejected_ids):
    """Update status of PG leave requests (by TA supervisor)."""
    from django.db.models import F
    if approved_ids:
        LeavePG.objects.filter(id__in=approved_ids).update(status=F('ta_supervisor'))
    if rejected_ids:
        LeavePG.objects.filter(id__in=rejected_ids).update(status=LeaveStatusChoices.REJECTED)


def update_pg_leave_status_thesis(approved_ids, rejected_ids):
    """Update status of PG leave requests (by Thesis supervisor)."""
    from django.db.models import F
    if approved_ids:
        LeavePG.objects.filter(id__in=approved_ids).update(status=F('thesis_supervisor'))
    if rejected_ids:
        LeavePG.objects.filter(id__in=rejected_ids).update(status=LeaveStatusChoices.REJECTED)


# ==================== BONAFIDE SERVICES ====================

def submit_bonafide(user, branch, semester, purpose, download_file=None):
    """
    Submit a bonafide application.
    Creates bonafide record and sends notification to academic admin.
    """
    bonafide_form = BonafideFormTableUpdated.objects.create(
        student_names=f"{user.first_name} {user.last_name}",
        roll_nos=user.extrainfo,
        branch_types=branch,
        semester_types=semester,
        purposes=purpose,
        date_of_applications=date.today(),
        download_file=download_file.name if download_file else "unavailable",
        approve=False,
        reject=False,
    )

    # Notify academic admin
    acad_admin_user = selectors.get_first_user_for_designation("acadadmin")
    if acad_admin_user:
        otheracademic_notif(
            user,
            acad_admin_user,
            'bonafide',
            bonafide_form.id,
            'student',
            "A new Bonafide application has been submitted."
        )

    return bonafide_form


def update_bonafide_status(approved_ids, rejected_ids, actor_user):
    """
    Update bonafide status and send notifications to students.
    """
    # Process approvals
    if approved_ids:
        BonafideFormTableUpdated.objects.filter(id__in=approved_ids).update(approve=True, reject=False)
        for bonafide_id in approved_ids:
            bonafide = selectors.get_bonafide_by_id(bonafide_id)
            if bonafide:
                student = selectors.get_user_by_extrainfo_id(bonafide.roll_nos_id)
                if student:
                    otheracademic_notif(
                        actor_user,
                        student,
                        'bonafide_accept',
                        bonafide.id,
                        'admin',
                        "Your Bonafide application has been approved. Please check the status."
                    )

    # Process rejections
    if rejected_ids:
        BonafideFormTableUpdated.objects.filter(id__in=rejected_ids).update(approve=False, reject=True)
        for bonafide_id in rejected_ids:
            bonafide = selectors.get_bonafide_by_id(bonafide_id)
            if bonafide:
                student = selectors.get_user_by_extrainfo(bonafide.roll_nos)
                if student:
                    otheracademic_notif(
                        actor_user,
                        student,
                        'bonafide_accept',
                        bonafide.id,
                        'admin',
                        "Your Bonafide application has been rejected. Please check the status for further details."
                    )


# ==================== ASSISTANTSHIP SERVICES ====================

def submit_assistantship(
    user,
    discipline,
    date_from,
    date_to,
    date_applied,
    bank_account,
    signature_file,
    ta_supervisor,
    thesis_supervisor,
    hod,
    applicability,
):
    """
    Submit an assistantship claim form.
    Validates supervisors, creates record, and sends notifications.
    """
    # Check for duplicate submission
    if selectors.assistantship_exists_for_period(user.extrainfo, date_from, date_to):
        raise AssistantshipServiceError("Form for this period already exists.")

    # Validate TA supervisor
    ta_supervisor_user = selectors.get_user_by_username(ta_supervisor)
    if not ta_supervisor_user:
        raise AssistantshipServiceError("TA Supervisor username not found.")

    # Validate Thesis supervisor
    thesis_supervisor_user = selectors.get_user_by_username(thesis_supervisor)
    if not thesis_supervisor_user:
        raise AssistantshipServiceError("Thesis Supervisor username not found.")

    # Create assistantship form
    assistantship_form = AssistantshipClaimFormStatusUpd.objects.create(
        roll_no=user.extrainfo,
        student_name=f"{user.first_name} {user.last_name}",
        discipline=discipline,
        dateFrom=date_from,
        dateTo=date_to,
        bank_account=bank_account,
        student_signature=signature_file,
        dateApplied=date_applied,
        ta_supervisor=ta_supervisor,
        thesis_supervisor=thesis_supervisor,
        hod=hod,
        applicability=applicability,
        TA_approved=False,
        TA_rejected=False,
        Ths_approved=False,
        Ths_rejected=False,
        HOD_approved=False,
        HOD_rejected=False,
        Dean_approved=False,
        Dean_rejected=False,
        Director_approved=False,
        Director_rejected=False,
        AcadAdmin_approved=False,
        AcadAdmin_rejected=False,
    )

    # Send notifications
    otheracademic_notif(
        user, ta_supervisor_user, "assistantship_form", assistantship_form.id,
        "student", "Assistantship form needs your (TA Supervisor) approval."
    )
    otheracademic_notif(
        user, thesis_supervisor_user, "assistantship_form", assistantship_form.id,
        "student", "Assistantship form needs your (Thesis Supervisor) approval."
    )

    return assistantship_form


def update_assistantship_status_ta(approved_ids, rejected_ids):
    """Update assistantship status by TA supervisor."""
    if approved_ids:
        AssistantshipClaimFormStatusUpd.objects.filter(id__in=approved_ids).update(TA_approved=True)
    if rejected_ids:
        AssistantshipClaimFormStatusUpd.objects.filter(id__in=rejected_ids).update(TA_rejected=True)


def update_assistantship_status_thesis(approved_ids, rejected_ids):
    """Update assistantship status by Thesis supervisor."""
    if approved_ids:
        AssistantshipClaimFormStatusUpd.objects.filter(id__in=approved_ids).update(Ths_approved=True)
    if rejected_ids:
        AssistantshipClaimFormStatusUpd.objects.filter(id__in=rejected_ids).update(Ths_rejected=True)


def update_assistantship_status_hod(approved_ids, rejected_ids):
    """Update assistantship status by HOD."""
    if approved_ids:
        AssistantshipClaimFormStatusUpd.objects.filter(id__in=approved_ids).update(HOD_approved=True, HOD_rejected=False)
    if rejected_ids:
        AssistantshipClaimFormStatusUpd.objects.filter(id__in=rejected_ids).update(HOD_approved=False, HOD_rejected=True)


def update_assistantship_status_acad_admin(approved_ids, rejected_ids):
    """Update assistantship status by Academic Admin."""
    if approved_ids:
        AssistantshipClaimFormStatusUpd.objects.filter(id__in=approved_ids).update(AcadAdmin_approved=True, AcadAdmin_rejected=False)
    if rejected_ids:
        AssistantshipClaimFormStatusUpd.objects.filter(id__in=rejected_ids).update(AcadAdmin_approved=False, AcadAdmin_rejected=True)


def update_assistantship_status_dean(approved_ids, rejected_ids):
    """Update assistantship status by Dean Academic."""
    if approved_ids:
        AssistantshipClaimFormStatusUpd.objects.filter(id__in=approved_ids).update(Dean_approved=True, Dean_rejected=False)
    if rejected_ids:
        AssistantshipClaimFormStatusUpd.objects.filter(id__in=rejected_ids).update(Dean_approved=False, Dean_rejected=True)


def update_assistantship_status_director(approved_ids, rejected_ids):
    """Update assistantship status by Director."""
    if approved_ids:
        AssistantshipClaimFormStatusUpd.objects.filter(id__in=approved_ids).update(Director_approved=True, Director_rejected=False)
    if rejected_ids:
        AssistantshipClaimFormStatusUpd.objects.filter(id__in=rejected_ids).update(Director_approved=False, Director_rejected=True)


def get_assistantship_status_text(form):
    """
    Determine the overall status text for an assistantship form.
    Returns 'Rejected', 'Approved', or 'Pending'.
    """
    is_rejected = any([
        form.Director_rejected,
        form.Dean_rejected,
        form.AcadAdmin_rejected,
        form.HOD_rejected,
        form.TA_rejected,
        form.Ths_rejected
    ])

    if is_rejected:
        return "Rejected"
    elif form.Director_approved:
        return "Approved"
    else:
        return "Pending"


def get_assistantship_approval_stages(form):
    """Get approval status for each stage of the assistantship workflow."""
    stages = {
        "TA_Supervisor": ("TA_approved", "TA_rejected"),
        "Thesis_Supervisor": ("Ths_approved", "Ths_rejected"),
        "HOD": ("HOD_approved", "HOD_rejected"),
        "Academic_Admin": ("AcadAdmin_approved", "AcadAdmin_rejected"),
        "Dean_Academic": ("Dean_approved", "Dean_rejected"),
        "Director": ("Director_approved", "Director_rejected"),
    }

    result = {}
    for stage_name, (approved_field, rejected_field) in stages.items():
        if getattr(form, approved_field):
            result[stage_name] = "Approved"
        elif getattr(form, rejected_field):
            result[stage_name] = "Rejected"
        else:
            result[stage_name] = "Pending"

    return result
