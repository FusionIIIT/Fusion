
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
        return User.objects.get(username=username)
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
    return LeaveFormTable.objects.filter(status=LeaveStatusChoices.PENDING)


def get_pending_pg_leaves_for_ta():
    """Get all pending PG leave requests (for TA approval)."""
    return LeavePG.objects.filter(status=LeaveStatusChoices.PENDING)


def get_pending_pg_leaves_for_thesis():
    """Get PG leave requests pending thesis supervisor approval."""
    return LeavePG.objects.filter(status=F('ta_supervisor'))


def get_pending_pg_leaves_for_hod():
    """Get PG leave requests pending HOD approval."""
    return LeavePG.objects.filter(status=F('thesis_supervisor'))


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
            "mobileNumber": leave.stud_mobile_no,
            "parentsMobile": leave.parent_mobile_no,
            "mobileDuringLeave": leave.leave_mobile_no,
            "semester": leave.curr_sem,
            "academicYear": leave.date_of_application.year,