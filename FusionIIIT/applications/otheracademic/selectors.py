"""
Selectors layer for otheracademic module.
Contains all database read operations (queries).
Views and services should call these selectors instead of querying directly.
"""
from django.db.models import F
from django.contrib.auth.models import User

from applications.otheracademic.models import (
    LeaveFormTable,
    LeavePG,
    BonafideFormTableUpdated,
    AssistantshipClaimFormStatusUpd,
    NoDues,
    LeaveStatusChoices,
)
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation


# ==================== USER/DESIGNATION SELECTORS ====================

def get_user_by_username(username):
    """Get a user by username, returns None if not found."""
    try:
        return User.objects.get(username__iexact=username)
    except User.DoesNotExist:
        return None


def get_user_by_extrainfo_id(extrainfo_id):
    """Get a user by their extrainfo ID."""
    try:
        return User.objects.get(extrainfo=extrainfo_id)
    except User.DoesNotExist:
        return None


def get_user_by_extrainfo(extrainfo):
    """Get a user by their extrainfo object."""
    try:
        return User.objects.get(extrainfo=extrainfo)
    except User.DoesNotExist:
        return None


def get_first_designation_for_user(user):
    """Get the first designation for a user."""
    designations = HoldsDesignation.objects.filter(user=user)
    if designations.exists():
        return designations.first().designation
    return None


def get_first_user_for_designation(designation_name):
    """
    Get the first user who holds a specific designation.
    Used for routing notifications to admin roles.
    """
    try:
        designation = Designation.objects.get(name=designation_name)
        user_ids = HoldsDesignation.objects.filter(
            designation_id=designation.id
        ).values_list('user_id', flat=True)

        if user_ids.exists():
            return User.objects.get(id=user_ids[0])
    except (Designation.DoesNotExist, User.DoesNotExist):
        pass
    return None


# ==================== LEAVE SELECTORS ====================

def get_pending_ug_leaves():
    """Get all pending UG leave requests."""
    return LeaveFormTable.objects.filter(approved=False, rejected=False)


def get_pending_ug_leaves_for_hod(hod_username):
    """Get pending UG leave requests assigned to a specific HOD."""
    return LeaveFormTable.objects.filter(
        approved=False,
        rejected=False,
        hod__iexact=hod_username,
    )


def get_pending_pg_leaves_for_ta():
    """Get all pending PG leave requests (for TA approval)."""
    return LeavePG.objects.filter(ta_approved=False, ta_rejected=False)


def get_pending_pg_leaves_for_ta_user(ta_username):
    """Get pending PG leave requests assigned to a specific TA supervisor."""
    return LeavePG.objects.filter(
        ta_approved=False,
        ta_rejected=False,
        ta_supervisor__iexact=ta_username,
    )


def get_pending_pg_leaves_for_thesis():
    """Get PG leave requests pending thesis supervisor approval."""
    return LeavePG.objects.filter(
        ta_approved=True,
        ta_rejected=False,
        thesis_approved=False,
        thesis_rejected=False,
    )


def get_pending_pg_leaves_for_thesis_user(thesis_username):
    """Get PG leave requests pending review for a specific thesis supervisor."""
    return LeavePG.objects.filter(
        ta_approved=True,
        ta_rejected=False,
        thesis_approved=False,
        thesis_rejected=False,
        thesis_supervisor__iexact=thesis_username,
    )


def get_pending_pg_leaves_for_hod():
    """Get PG leave requests pending HOD approval."""
    return LeavePG.objects.filter(
        thesis_approved=True,
        thesis_rejected=False,
        hod_approved=False,
        hod_rejected=False,
    )


def get_pending_pg_leaves_for_hod_user(hod_username):
    """Get PG leave requests pending approval for a specific HOD."""
    return LeavePG.objects.filter(
        thesis_approved=True,
        thesis_rejected=False,
        hod_approved=False,
        hod_rejected=False,
        hod__iexact=hod_username,
    )


def get_ug_leaves_by_roll_no(roll_no_id):
    """Get all UG leave requests for a specific roll number."""
    return LeaveFormTable.objects.filter(roll_no=roll_no_id)


def get_pg_leaves_by_roll_no(roll_no_id):
    """Get all PG leave requests for a specific roll number."""
    return LeavePG.objects.filter(roll_no=roll_no_id)


def get_leave_by_id(leave_id, is_pg=False):
    """Get a leave request by ID."""
    model = LeavePG if is_pg else LeaveFormTable
    try:
        return model.objects.get(id=leave_id)
    except model.DoesNotExist:
        return None


def serialize_ug_leave(leave):
    """Serialize a UG leave request to dictionary format."""
    return {
        "id": leave.id,
        "rollNo": leave.roll_no.id,
        "name": leave.student_name,
        "form": leave.upload_file.url if leave.upload_file else None,
        "details": {
            "dateFrom": leave.date_from,
            "dateTo": leave.date_to,
            "leaveType": leave.leave_type,
            "address": leave.address,
            "purpose": leave.purpose,
            "hodCredential": leave.hod,
            "mobileNumber": None,
            "parentsMobile": None,
            "mobileDuringLeave": None,
            "semester": None,
            "academicYear": leave.date_of_application.year,
            "dateOfApplication": leave.date_of_application,
        },
    }


def serialize_pg_leave(leave):
    """Serialize a PG leave request to dictionary format."""
    return {
        "id": leave.id,
        "rollNo": leave.roll_no.id,
        "name": leave.student_name,
        "form": leave.upload_file.url if leave.upload_file else None,
        "details": {
            "dateFrom": leave.date_from,
            "dateTo": leave.date_to,
            "leaveType": leave.leave_type,
            "address": leave.address,
            "purpose": leave.purpose,
            "hodCredential": leave.hod,
            "mobileNumber": leave.mobile_no,
            "parentsMobile": leave.parent_mobile_no,
            "mobileDuringLeave": leave.alt_mobile_no,
            "semester": leave.Semester,
            "academicYear": leave.date_of_application.year,
            "dateOfApplication": leave.date_of_application,
        },
    }


def serialize_leave_status(leave, roll_no_id):
    """Serialize leave status for student view."""
    if hasattr(leave, 'approved'):
        status_text = (
            LeaveStatusChoices.APPROVED
            if leave.approved
            else LeaveStatusChoices.REJECTED
            if leave.rejected
            else LeaveStatusChoices.PENDING
        )
        is_final = leave.approved or leave.rejected
    else:
        is_rejected = any([
            leave.ta_rejected,
            leave.thesis_rejected,
            leave.hod_rejected,
        ])
        status_text = (
            LeaveStatusChoices.APPROVED
            if leave.hod_approved
            else LeaveStatusChoices.REJECTED
            if is_rejected
            else LeaveStatusChoices.PENDING
        )
        is_final = leave.hod_approved or leave.hod_rejected

    return {
        "id": leave.id,
        "rollNo": roll_no_id,
        "name": leave.student_name,
        "dateApplied": leave.date_of_application.strftime("%Y-%m-%d") if leave.date_of_application else None,
        "dateFrom": leave.date_from,
        "dateTo": leave.date_to,
        "leaveType": leave.leave_type,
        "attachment": leave.upload_file.url if leave.upload_file else None,
        "purpose": leave.purpose,
        "address": leave.address,
        "action": status_text,
        "canWithdraw": not is_final,
    }


# ==================== BONAFIDE SELECTORS ====================

def get_pending_bonafides():
    """Get all pending bonafide requests."""
    return BonafideFormTableUpdated.objects.filter(approve=False, reject=False)


def get_bonafide_by_id(bonafide_id):
    """Get a bonafide request by ID."""
    try:
        return BonafideFormTableUpdated.objects.get(id=bonafide_id)
    except BonafideFormTableUpdated.DoesNotExist:
        return None


def get_bonafides_by_roll_no(roll_no_id):
    """Get all bonafide requests for a specific roll number."""
    return BonafideFormTableUpdated.objects.filter(roll_nos_id=roll_no_id)


def serialize_pending_bonafide(bonafide):
    """Serialize a pending bonafide request."""
    return {
        "id": bonafide.id,
        "rollNo": bonafide.roll_nos_id,
        "name": bonafide.student_names,
        "details": {
            "purpose": bonafide.purposes,
            "dateOfApplication": bonafide.date_of_applications,
            "semester": bonafide.semester_types,
        },
    }


def serialize_bonafide_status(bonafide):
    """Serialize bonafide status for student view."""
    status = "Approved" if bonafide.approve else "Rejected" if bonafide.reject else "Pending"
    download_url = None
    if bonafide.download_file:
        try:
            download_url = bonafide.download_file.url
        except ValueError:
            # File field can be empty or point to a non-resolved path.
            download_url = None

    return {
        "id": bonafide.id,
        "rollNo": bonafide.roll_nos_id,
        "name": bonafide.student_names,
        "branch": bonafide.branch_types,
        "semester": bonafide.semester_types,
        "purpose": bonafide.purposes,
        "dateApplied": bonafide.date_of_applications.strftime("%Y-%m-%d") if bonafide.date_of_applications else None,
        "status": status,
        "downloadUrl": download_url,
    }


# ==================== ASSISTANTSHIP SELECTORS ====================

def assistantship_exists_for_period(roll_no, date_from, date_to):
    """Check if an assistantship form already exists for the given period."""
    return AssistantshipClaimFormStatusUpd.objects.filter(
        roll_no=roll_no,
        dateFrom=date_from,
        dateTo=date_to
    ).exists()


def get_pending_assistantships_for_ta():
    """Get assistantship forms pending TA approval."""
    return AssistantshipClaimFormStatusUpd.objects.filter(
        TA_approved=False,
        TA_rejected=False
    )


def get_pending_assistantships_for_thesis():
    """Get assistantship forms pending Thesis supervisor approval."""
    return AssistantshipClaimFormStatusUpd.objects.filter(
        Ths_approved=False,
        Ths_rejected=False
    )


def get_pending_assistantships_for_hod():
    """Get assistantship forms pending HOD approval."""
    return AssistantshipClaimFormStatusUpd.objects.filter(
        TA_approved=True,
        Ths_approved=True,
        HOD_approved=False,
        HOD_rejected=False
    )


def get_pending_assistantships_for_acad_admin():
    """Get assistantship forms pending Academic Admin approval."""
    return AssistantshipClaimFormStatusUpd.objects.filter(
        TA_approved=True,
        Ths_approved=True,
        HOD_approved=True,
        AcadAdmin_approved=False,
        AcadAdmin_rejected=False
    )


def get_pending_assistantships_for_dean():
    """Get assistantship forms pending Dean Academic approval."""
    return AssistantshipClaimFormStatusUpd.objects.filter(
        TA_approved=True,
        Ths_approved=True,
        HOD_approved=True,
        AcadAdmin_approved=True,
        Dean_approved=False,
        Dean_rejected=False
    )


def get_pending_assistantships_for_director():
    """Get assistantship forms pending Director approval."""
    return AssistantshipClaimFormStatusUpd.objects.filter(
        TA_approved=True,
        Ths_approved=True,
        HOD_approved=True,
        AcadAdmin_approved=True,
        Dean_approved=True,
        Director_approved=False,
        Director_rejected=False
    )


def get_assistantships_by_roll_no(roll_no_id):
    """Get all assistantship forms for a specific roll number."""
    return AssistantshipClaimFormStatusUpd.objects.filter(roll_no_id=roll_no_id)


def serialize_assistantship_pending(form):
    """Serialize an assistantship form for pending requests view."""
    return {
        "id": form.id,
        "student_name": form.student_name,
        "roll_no": form.roll_no.id,
        "discipline": form.discipline,
        "dateFrom": form.dateFrom.strftime('%Y-%m-%d'),
        "dateTo": form.dateTo.strftime('%Y-%m-%d'),
        "applicability": form.applicability,
        "dateApplied": form.dateApplied.strftime('%Y-%m-%d'),
    }


# ==================== NO DUES SELECTORS ====================

def get_nodues_by_roll_no(roll_no):
    """Get no dues record for a specific roll number."""
    try:
        return NoDues.objects.get(roll_no=roll_no)
    except NoDues.DoesNotExist:
        return None


def get_all_nodues_requests():
    """Get all no dues requests."""
    return NoDues.objects.all()
