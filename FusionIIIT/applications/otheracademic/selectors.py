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
    GraduateSeminarFormTable,
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
            "mobileNumber": leave.stud_mobile_no,
            "parentsMobile": leave.parent_mobile_no,
            "mobileDuringLeave": leave.leave_mobile_no,
            "semester": leave.curr_sem,
            "academicYear": leave.date_of_application.year,
            "dateOfApplication": leave.date_of_application,
        },
    }


def serialize_leave_status(leave, roll_no_id):
    """Serialize leave status for student view."""
    return {
        "rollNo": roll_no_id,
        "name": leave.student_name,
        "dateFrom": leave.date_from,
        "dateTo": leave.date_to,
        "leaveType": leave.leave_type,
        "attachment": leave.upload_file.url if leave.upload_file else None,
        "purpose": leave.purpose,
        "address": leave.address,
        "action": leave.status,
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
    return {
        "rollNo": bonafide.roll_nos_id,
        "name": bonafide.student_names,
        "branch": bonafide.branch_types,
        "semester": bonafide.semester_types,
        "purpose": bonafide.purposes,
        "dateApplied": bonafide.date_of_applications.strftime("%Y-%m-%d") if bonafide.date_of_applications else None,
        "status": status,
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


# ==================== GRADUATE SEMINAR SELECTORS ====================

def get_pending_graduate_seminar_forms():
    """Get all pending graduate seminar forms."""
    return GraduateSeminarFormTable.objects.filter(status='Pending')


def get_graduate_seminar_forms_by_roll_no(roll_no_id):
    """Get all graduate seminar forms for a specific roll number."""
    return GraduateSeminarFormTable.objects.filter(roll_no=roll_no_id)


def serialize_graduate_seminar_form(form):
    """Serialize a graduate seminar form for API response."""
    student_name = ""
    if form.roll_no and form.roll_no.user:
        student_name = form.roll_no.user.get_full_name()
    
    return {
        "id": form.id,
        "roll_no": form.roll_no.roll_no if form.roll_no else "",
        "student_name": student_name,
        "semester": form.semester,
        "date_of_seminar": form.date_of_seminar.strftime('%Y-%m-%d'),
        "theme_of_work": form.theme_of_work,
        "place": form.place,
        "time": form.time.strftime('%H:%M') if form.time else "",
        "work_done_till_previous_sem": form.work_done_till_previous_sem,
        "specific_contri_in_cur_sem": form.specific_contri_in_cur_sem,
        "future_plan": form.future_plan,
        "quality_of_work": form.quality_of_work,
        "quantity_of_work": form.quantity_of_work,
        "status": form.status,
        "date_of_submission": form.date_of_submission.strftime('%Y-%m-%d'),
        "remarks": form.remarks or "",
    }


def get_nodues_records_by_department(department):
    """Get all no dues records."""
    return NoDues.objects.all()


def serialize_nodues_record(record, department):
    """Serialize a no dues record for API response."""
    # Map department to field names
    department_field_map = {
        "hostel": ("hostel_clear", "hostel_notclear"),
        "library": ("library_clear", "library_notclear"),
        "mess": ("mess_clear", "mess_notclear"),
        "ece": ("ece_clear", "ece_notclear"),
        "physics_lab": ("physics_lab_clear", "physics_lab_notclear"),
        "bank": ("bank_clear", "bank_notclear"),
        "icard_dsa": ("icard_dsa_clear", "icard_dsa_notclear"),
        "design_studio": ("design_studio_clear", "design_studio_notclear"),
        "discipline_office": ("discipline_office_clear", "discipline_office_notclear"),
        "account": ("account_clear", "account_notclear"),
    }
    
    clear_field, notclear_field = department_field_map.get(department, ("hostel_clear", "hostel_notclear"))
    is_clear = getattr(record, clear_field, False)
    is_notclear = getattr(record, notclear_field, False)
    
    return {
        "id": record.id,
        "roll_no": record.roll_no.roll_no if record.roll_no else "",
        "name": record.name,
        "is_clear": is_clear,
        "is_notclear": is_notclear,
        "status": "Clear" if is_clear else ("Not Clear" if is_notclear else "Pending"),
    }


