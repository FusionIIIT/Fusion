"""
Services layer for otheracademic module.
Contains all business logic and write operations.
Views should call these services instead of containing business logic directly.
"""
from datetime import date, datetime
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction

from applications.otheracademic.models import (
    LeaveFormTable,
    LeavePG,
    BonafideFormTableUpdated,
    AssistantshipClaimFormStatusUpd,
    PGTAAssignment,
    PGFacultySupervisorAssignment,
    PGTAAssignmentHistory,
    PGFacultySupervisorAssignmentHistory,
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


class TAAssignmentServiceError(Exception):
    """Custom exception for PG TA assignment-related errors."""
    pass


def _get_bonafide_admin_recipients():
    """Return all academic-admin users eligible for bonafide notifications."""
    recipients = selectors.get_users_for_designation("acadadmin")
    if recipients.exists():
        return recipients

    # Backward-compatible fallback for alternate naming in some deployments.
    return selectors.get_users_for_designation("acad_admin")


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
    try:
        parsed_date_from = datetime.strptime(str(date_from), "%Y-%m-%d").date()
        parsed_date_to = datetime.strptime(str(date_to), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise LeaveServiceError("Invalid date format. Please use YYYY-MM-DD.")

    if parsed_date_from > parsed_date_to:
        raise LeaveServiceError("Invalid leave dates: end date must be on or after start date.")

    if selectors.ug_leave_overlap_exists(user.extrainfo, parsed_date_from, parsed_date_to):
        raise LeaveServiceError("Overlapping leave request already exists for the selected dates.")

    # Validate HOD exists
    hod_user = selectors.get_user_by_username(hod_credential)
    if not hod_user:
        raise LeaveServiceError(f"HOD with username '{hod_credential}' not found.")

    # Create leave record
    leave = LeaveFormTable.objects.create(
        student_name=f"{user.first_name}{user.last_name}",
        roll_no=user.extrainfo,
        date_from=parsed_date_from,
        date_to=parsed_date_to,
        leave_type=leave_type,
        upload_file=upload_file,
        address=address,
        purpose=purpose,
        date_of_application=date.today(),
        approved=False,
        rejected=False,
        hod=hod_user.username,
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
    try:
        parsed_date_from = datetime.strptime(str(date_from), "%Y-%m-%d").date()
        parsed_date_to = datetime.strptime(str(date_to), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise LeaveServiceError("Invalid date format. Please use YYYY-MM-DD.")

    if parsed_date_from > parsed_date_to:
        raise LeaveServiceError("Invalid leave dates: end date must be on or after start date.")

    if selectors.pg_leave_overlap_exists(user.extrainfo, parsed_date_from, parsed_date_to):
        raise LeaveServiceError("Overlapping leave request already exists for the selected dates.")

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
        programme="",
        discipline="",
        Semester=str(semester) if semester else "",
        roll_no=user.extrainfo,
        date_from=parsed_date_from,
        date_to=parsed_date_to,
        leave_type=leave_type,
        upload_file=upload_file,
        address=address,
        purpose=purpose,
        date_of_application=date.today(),
        mobile_no=mobile_number or "",
        parent_mobile_no=parents_mobile or "",
        alt_mobile_no=mobile_during_leave or "",
        ta_approved=False,
        ta_rejected=False,
        thesis_approved=False,
        thesis_rejected=False,
        hod_approved=False,
        hod_rejected=False,
        hod=hod_user.username,
        ta_supervisor=ta_user.username,
        thesis_supervisor=thesis_user.username,
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
    otheracademic_notif(user, ta_user, 'pg_leave_ta', leave.id, 'student', "A new leave application")

    return leave


def update_ug_leave_status(approved_ids, rejected_ids, actor_user):
    """Update status of UG leave requests (by HOD)."""
    if approved_ids:
        for leave_id in approved_ids:
            leave = selectors.get_leave_by_id(leave_id, is_pg=False)
            if not leave:
                continue
            if leave.hod.lower() != actor_user.username.lower():
                raise LeaveServiceError("You can only act on leave requests assigned to you.")
            if leave.approved or leave.rejected:
                raise LeaveServiceError("This leave request has already been finalized.")
            leave.approved = True
            leave.rejected = False
            leave.save(update_fields=["approved", "rejected"])
            if leave:
                student = selectors.get_user_by_extrainfo_id(leave.roll_no_id)
                if student:
                    otheracademic_notif(
                        actor_user,
                        student,
                        'ug_leave_hod_approve',
                        leave.id,
                        'admin',
                        "Your leave request has been approved by HOD.",
                    )
    if rejected_ids:
        for leave_id in rejected_ids:
            leave = selectors.get_leave_by_id(leave_id, is_pg=False)
            if not leave:
                continue
            if leave.hod.lower() != actor_user.username.lower():
                raise LeaveServiceError("You can only act on leave requests assigned to you.")
            if leave.approved or leave.rejected:
                raise LeaveServiceError("This leave request has already been finalized.")
            leave.approved = False
            leave.rejected = True
            leave.save(update_fields=["approved", "rejected"])
            if leave:
                student = selectors.get_user_by_extrainfo_id(leave.roll_no_id)
                if student:
                    otheracademic_notif(
                        actor_user,
                        student,
                        'ug_leave_hod_approve',
                        leave.id,
                        'admin',
                        "Your leave request has been rejected by HOD.",
                    )


def update_pg_leave_status_hod(approved_ids, rejected_ids, actor_user):
    """Update status of PG leave requests (by HOD - final approval)."""
    if approved_ids:
        for leave_id in approved_ids:
            leave = selectors.get_leave_by_id(leave_id, is_pg=True)
            if not leave:
                continue
            if leave.hod.lower() != actor_user.username.lower():
                raise LeaveServiceError("You can only act on leave requests assigned to you.")
            if not leave.thesis_approved or leave.thesis_rejected:
                raise LeaveServiceError("HOD can only act after thesis supervisor approval.")
            if leave.hod_approved or leave.hod_rejected:
                raise LeaveServiceError("This leave request has already been finalized by HOD.")
            leave.hod_approved = True
            leave.hod_rejected = False
            leave.save(update_fields=["hod_approved", "hod_rejected"])
            if leave:
                student = selectors.get_user_by_extrainfo_id(leave.roll_no_id)
                if student:
                    otheracademic_notif(
                        actor_user,
                        student,
                        'pg_leave_ta_approve',
                        leave.id,
                        'admin',
                        "Your PG leave request has been approved by HOD.",
                    )
    if rejected_ids:
        for leave_id in rejected_ids:
            leave = selectors.get_leave_by_id(leave_id, is_pg=True)
            if not leave:
                continue
            if leave.hod.lower() != actor_user.username.lower():
                raise LeaveServiceError("You can only act on leave requests assigned to you.")
            if not leave.thesis_approved or leave.thesis_rejected:
                raise LeaveServiceError("HOD can only act after thesis supervisor approval.")
            if leave.hod_approved or leave.hod_rejected:
                raise LeaveServiceError("This leave request has already been finalized by HOD.")
            leave.hod_approved = False
            leave.hod_rejected = True
            leave.save(update_fields=["hod_approved", "hod_rejected"])
            if leave:
                student = selectors.get_user_by_extrainfo_id(leave.roll_no_id)
                if student:
                    otheracademic_notif(
                        actor_user,
                        student,
                        'pg_leave_ta_approve',
                        leave.id,
                        'admin',
                        "Your PG leave request has been rejected by HOD.",
                    )


def update_pg_leave_status_ta(approved_ids, rejected_ids, actor_user):
    """Update status of PG leave requests (by TA supervisor)."""
    if approved_ids:
        for leave_id in approved_ids:
            leave = selectors.get_leave_by_id(leave_id, is_pg=True)
            if not leave:
                continue
            if leave.ta_supervisor.lower() != actor_user.username.lower():
                raise LeaveServiceError("You can only act on leave requests assigned to you.")
            if leave.ta_approved or leave.ta_rejected:
                raise LeaveServiceError("TA supervisor decision already exists for this request.")
            leave.ta_approved = True
            leave.ta_rejected = False
            leave.save(update_fields=["ta_approved", "ta_rejected"])
            if leave:
                thesis_user = selectors.get_user_by_username(leave.thesis_supervisor)
                student = selectors.get_user_by_extrainfo_id(leave.roll_no_id)
                if thesis_user:
                    otheracademic_notif(
                        actor_user,
                        thesis_user,
                        'pg_leave_thesis',
                        leave.id,
                        'student',
                        "A PG leave request is forwarded to you for thesis supervisor review.",
                    )
                if student:
                    otheracademic_notif(
                        actor_user,
                        student,
                        'pg_leave_ta_approve',
                        leave.id,
                        'admin',
                        "Your PG leave request has been approved by TA supervisor and moved to thesis supervisor.",
                    )
    if rejected_ids:
        for leave_id in rejected_ids:
            leave = selectors.get_leave_by_id(leave_id, is_pg=True)
            if not leave:
                continue
            if leave.ta_supervisor.lower() != actor_user.username.lower():
                raise LeaveServiceError("You can only act on leave requests assigned to you.")
            if leave.ta_approved or leave.ta_rejected:
                raise LeaveServiceError("TA supervisor decision already exists for this request.")
            leave.ta_approved = False
            leave.ta_rejected = True
            leave.save(update_fields=["ta_approved", "ta_rejected"])
            if leave:
                student = selectors.get_user_by_extrainfo_id(leave.roll_no_id)
                if student:
                    otheracademic_notif(
                        actor_user,
                        student,
                        'pg_leave_ta_approve',
                        leave.id,
                        'admin',
                        "Your PG leave request has been rejected at TA supervisor level.",
                    )


def update_pg_leave_status_thesis(approved_ids, rejected_ids, actor_user):
    """Update status of PG leave requests (by Thesis supervisor)."""
    if approved_ids:
        for leave_id in approved_ids:
            leave = selectors.get_leave_by_id(leave_id, is_pg=True)
            if not leave:
                continue
            if leave.thesis_supervisor.lower() != actor_user.username.lower():
                raise LeaveServiceError("You can only act on leave requests assigned to you.")
            if not leave.ta_approved or leave.ta_rejected:
                raise LeaveServiceError("Thesis supervisor can act only after TA approval.")
            if leave.thesis_approved or leave.thesis_rejected:
                raise LeaveServiceError("Thesis supervisor decision already exists for this request.")
            leave.thesis_approved = True
            leave.thesis_rejected = False
            leave.save(update_fields=["thesis_approved", "thesis_rejected"])
            if leave:
                hod_user = selectors.get_user_by_username(leave.hod)
                student = selectors.get_user_by_extrainfo_id(leave.roll_no_id)
                if hod_user:
                    otheracademic_notif(
                        actor_user,
                        hod_user,
                        'pg_leave_hod',
                        leave.id,
                        'student',
                        "A PG leave request is forwarded to you for HOD review.",
                    )
                if student:
                    otheracademic_notif(
                        actor_user,
                        student,
                        'pg_leave_ta_approve',
                        leave.id,
                        'admin',
                        "Your PG leave request has been approved by thesis supervisor and moved to HOD.",
                    )
    if rejected_ids:
        for leave_id in rejected_ids:
            leave = selectors.get_leave_by_id(leave_id, is_pg=True)
            if not leave:
                continue
            if leave.thesis_supervisor.lower() != actor_user.username.lower():
                raise LeaveServiceError("You can only act on leave requests assigned to you.")
            if not leave.ta_approved or leave.ta_rejected:
                raise LeaveServiceError("Thesis supervisor can act only after TA approval.")
            if leave.thesis_approved or leave.thesis_rejected:
                raise LeaveServiceError("Thesis supervisor decision already exists for this request.")
            leave.thesis_approved = False
            leave.thesis_rejected = True
            leave.save(update_fields=["thesis_approved", "thesis_rejected"])
            if leave:
                student = selectors.get_user_by_extrainfo_id(leave.roll_no_id)
                if student:
                    otheracademic_notif(
                        actor_user,
                        student,
                        'pg_leave_ta_approve',
                        leave.id,
                        'admin',
                        "Your PG leave request has been rejected at thesis supervisor level.",
                    )


def withdraw_ug_leave(user, leave_id):
    """Allow student to withdraw a UG leave request before final HOD decision."""
    leave = selectors.get_leave_by_id(leave_id, is_pg=False)
    if not leave:
        raise LeaveServiceError("Leave request not found.")
    if leave.roll_no_id != user.extrainfo.id:
        raise LeaveServiceError("You are not authorized to withdraw this leave request.")
    if leave.approved or leave.rejected:
        raise LeaveServiceError("Cannot withdraw a leave request that has already been verified by HOD.")

    hod_user = selectors.get_user_by_username(leave.hod)
    if hod_user:
        otheracademic_notif(
            user,
            hod_user,
            'ug_leave_hod',
            leave.id,
            'student',
            "A leave request has been withdrawn by the student.",
        )
    leave.delete()


def withdraw_pg_leave(user, leave_id):
    """Allow student to withdraw a PG leave request before final HOD decision."""
    leave = selectors.get_leave_by_id(leave_id, is_pg=True)
    if not leave:
        raise LeaveServiceError("Leave request not found.")
    if leave.roll_no_id != user.extrainfo.id:
        raise LeaveServiceError("You are not authorized to withdraw this leave request.")
    if leave.hod_approved or leave.hod_rejected:
        raise LeaveServiceError("Cannot withdraw a leave request that has already been verified by HOD.")

    hod_user = selectors.get_user_by_username(leave.hod)
    if hod_user:
        otheracademic_notif(
            user,
            hod_user,
            'pg_leave_hod',
            leave.id,
            'student',
            "A PG leave request has been withdrawn by the student.",
        )
    leave.delete()


# ==================== BONAFIDE SERVICES ====================

def submit_bonafide(user, branch, semester, purpose, download_file=None):
    """
    Submit a bonafide application.
    Creates bonafide record and sends notification to academic admin.
    """
    if not branch or not semester or not purpose:
        raise BonafideServiceError("Branch, semester, and purpose are required.")

    bonafide_form = BonafideFormTableUpdated.objects.create(
        student_names=f"{user.first_name} {user.last_name}",
        roll_nos=user.extrainfo,
        branch_types=branch,
        semester_types=semester,
        purposes=purpose,
        date_of_applications=date.today(),
        # Certificate is uploaded by admin after approval.
        download_file=None,
        approve=False,
        reject=False,
    )

    # Notify all academic admins
    for acad_admin_user in _get_bonafide_admin_recipients():
        otheracademic_notif(
            user,
            acad_admin_user,
            'bonafide_acadadmin',
            bonafide_form.id,
            'student',
            "A Bonafide request is pending for your approval."
        )

    return bonafide_form


def update_bonafide_status(approved_ids, rejected_ids, actor_user):
    """
    Update bonafide status and send notifications to students.
    """
    # Process approvals
    if approved_ids:
        for bonafide_id in approved_ids:
            bonafide = selectors.get_bonafide_by_id(bonafide_id)
            if bonafide:
                if bonafide.approve or bonafide.reject:
                    raise BonafideServiceError("Bonafide request is already finalized.")
                bonafide.approve = True
                bonafide.reject = False
                bonafide.save(update_fields=["approve", "reject"])
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
        for bonafide_id in rejected_ids:
            bonafide = selectors.get_bonafide_by_id(bonafide_id)
            if bonafide:
                if bonafide.approve or bonafide.reject:
                    raise BonafideServiceError("Bonafide request is already finalized.")
                bonafide.approve = False
                bonafide.reject = True
                bonafide.save(update_fields=["approve", "reject"])
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


def upload_bonafide_certificate(bonafide_id, certificate):
    """Upload bonafide certificate only after approval."""
    bonafide = selectors.get_bonafide_by_id(bonafide_id)
    if not bonafide:
        raise BonafideServiceError("Bonafide request not found.")
    if not bonafide.approve or bonafide.reject:
        raise BonafideServiceError("Certificate can be uploaded only for approved bonafide requests.")

    bonafide.download_file = certificate
    bonafide.save(update_fields=["download_file"])
    return bonafide


def withdraw_bonafide(user, bonafide_id):
    """Allow student to withdraw only pending bonafide requests."""
    bonafide = selectors.get_bonafide_by_id(bonafide_id)
    if not bonafide:
        raise BonafideServiceError("Bonafide request not found.")
    if bonafide.roll_nos_id != user.extrainfo.id:
        raise BonafideServiceError("You are not authorized to withdraw this bonafide request.")
    if bonafide.approve or bonafide.reject:
        raise BonafideServiceError("Only pending bonafide requests can be withdrawn.")

    for acad_admin_user in _get_bonafide_admin_recipients():
        otheracademic_notif(
            user,
            acad_admin_user,
            'bonafide_acadadmin',
            bonafide.id,
            'student',
            "A Bonafide application has been withdrawn by the student.",
        )
    bonafide.delete()


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

    # PG-only eligibility for assistantship.
    is_pg_student = selectors.get_pg_students_for_assignment().filter(id=user.extrainfo).exists()
    if not is_pg_student:
        raise AssistantshipServiceError("Only PG students can submit assistantship claims.")

    # Resolve assigned faculty supervisor for this PG student (if configured).
    supervisor_assignment = selectors.get_pg_faculty_supervisor_assignment_for_student(
        user.extrainfo.id
    )
    if not supervisor_assignment:
        raise AssistantshipServiceError(
            "Faculty Supervisor is not assigned for this PG student. Please contact Department Admin."
        )

    ta_supervisor_user = supervisor_assignment.faculty_supervisor
    if ta_supervisor and ta_supervisor_user.username.lower() != str(ta_supervisor).lower():
        raise AssistantshipServiceError(
            "Faculty Supervisor does not match the configured assignment for this PG student."
        )

    # Resolve Department Admin for next stage.
    dept_admin_user = None
    if hod:
        candidate = selectors.get_user_by_username(hod)
        if candidate and selectors.user_has_designation(candidate, "dept_admin"):
            dept_admin_user = candidate

    if not dept_admin_user:
        dept_admin_user = (
            selectors.get_first_user_for_designation("dept_admin")
            or selectors.get_first_user_for_designation("deptadmin")
        )

    if not dept_admin_user:
        raise AssistantshipServiceError("Department Admin is not configured.")

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
        ta_supervisor=ta_supervisor_user.username,
        thesis_supervisor=thesis_supervisor or "",
        hod=dept_admin_user.username,
        applicability=applicability,
        TA_approved=False,
        TA_rejected=False,
        Ths_approved=False,
        Ths_rejected=False,
        HOD_approved=False,
        HOD_rejected=False,
        Acad_approved=False,
        Acad_rejected=False,
        remark="",
    )

    # Send notification to faculty supervisor (first review stage).
    otheracademic_notif(
        user,
        ta_supervisor_user,
        "ast_ta",
        assistantship_form.id,
        "student",
        "A PG assistantship form is waiting for your verification.",
    )

    return assistantship_form


def update_assistantship_status_ta(approved_ids, rejected_ids, actor_user):
    """Update assistantship status by faculty supervisor."""
    if approved_ids:
        for form_id in approved_ids:
            form = selectors.get_assistantship_by_id(form_id)
            if not form:
                continue
            if form.ta_supervisor.lower() != actor_user.username.lower():
                raise AssistantshipServiceError("You can only review forms assigned to you.")
            if form.TA_approved or form.TA_rejected:
                raise AssistantshipServiceError("This assistantship form is already reviewed.")

            form.TA_approved = True
            form.TA_rejected = False
            form.save(update_fields=["TA_approved", "TA_rejected"])

            student_user = selectors.get_user_by_extrainfo_id(form.roll_no_id)
            dept_admin_users = selectors.get_users_for_designation("dept_admin")
            if not dept_admin_users.exists():
                dept_admin_users = selectors.get_users_for_designation("deptadmin")

            if student_user:
                otheracademic_notif(
                    actor_user,
                    student_user,
                    "ast_ta_accept",
                    form.id,
                    "admin",
                    "Your assistantship form has been verified by Faculty Supervisor.",
                )
            for dept_admin_user in dept_admin_users:
                otheracademic_notif(
                    actor_user,
                    dept_admin_user,
                    "ast_hod",
                    form.id,
                    "admin",
                    "A verified assistantship form is waiting for Department Admin approval.",
                )
    if rejected_ids:
        for form_id in rejected_ids:
            form = selectors.get_assistantship_by_id(form_id)
            if not form:
                continue
            if form.ta_supervisor.lower() != actor_user.username.lower():
                raise AssistantshipServiceError("You can only review forms assigned to you.")
            if form.TA_approved or form.TA_rejected:
                raise AssistantshipServiceError("This assistantship form is already reviewed.")

            form.TA_approved = False
            form.TA_rejected = True
            form.save(update_fields=["TA_approved", "TA_rejected"])

            student_user = selectors.get_user_by_extrainfo_id(form.roll_no_id)
            if student_user:
                otheracademic_notif(
                    actor_user,
                    student_user,
                    "ast_ta_accept",
                    form.id,
                    "admin",
                    "Your assistantship form has been rejected by Faculty Supervisor.",
                )


def update_assistantship_status_thesis(approved_ids, rejected_ids):
    """Update assistantship status by Thesis supervisor."""
    if approved_ids:
        AssistantshipClaimFormStatusUpd.objects.filter(id__in=approved_ids).update(Ths_approved=True)
    if rejected_ids:
        AssistantshipClaimFormStatusUpd.objects.filter(id__in=rejected_ids).update(Ths_rejected=True)


def update_assistantship_status_hod(approved_ids, rejected_ids, actor_user):
    """Update assistantship status by Department Admin (stage 2 verification)."""
    if approved_ids:
        for form_id in approved_ids:
            form = selectors.get_assistantship_by_id(form_id)
            if not form:
                continue
            if not form.TA_approved or form.TA_rejected:
                raise AssistantshipServiceError("Department Admin can act only after Faculty Supervisor verification.")
            if form.HOD_approved or form.HOD_rejected:
                raise AssistantshipServiceError("This assistantship form is already reviewed by Department Admin.")

            form.HOD_approved = True
            form.HOD_rejected = False
            form.save(update_fields=["HOD_approved", "HOD_rejected", "remark"])

            student_user = selectors.get_user_by_extrainfo_id(form.roll_no_id)
            hod_users = selectors.get_users_for_designation_contains("hod")
            if student_user:
                otheracademic_notif(
                    actor_user,
                    student_user,
                    "ast_ta_accept",
                    form.id,
                    "admin",
                    "Your assistantship has been verified by Department Admin and forwarded to HOD.",
                )
            for hod_user in hod_users:
                if hod_user.id == actor_user.id:
                    continue
                otheracademic_notif(
                    actor_user,
                    hod_user,
                    "ast_hod",
                    form.id,
                    "admin",
                    "A verified assistantship form is waiting for HOD approval.",
                )
    if rejected_ids:
        for form_id in rejected_ids:
            form = selectors.get_assistantship_by_id(form_id)
            if not form:
                continue
            if not form.TA_approved or form.TA_rejected:
                raise AssistantshipServiceError("Department Admin can act only after Faculty Supervisor verification.")
            if form.HOD_approved or form.HOD_rejected:
                raise AssistantshipServiceError("This assistantship form is already reviewed by Department Admin.")

            form.HOD_approved = False
            form.HOD_rejected = True
            form.remark = "Rejected by Department Admin"
            form.save(update_fields=["HOD_approved", "HOD_rejected", "remark"])

            student_user = selectors.get_user_by_extrainfo_id(form.roll_no_id)
            if student_user:
                otheracademic_notif(
                    actor_user,
                    student_user,
                    "ast_ta_accept",
                    form.id,
                    "admin",
                    "Your assistantship has been rejected by Department Admin.",
                )


def withdraw_assistantship(user, form_id):
    """Allow PG student to withdraw assistantship before faculty review."""
    form = selectors.get_assistantship_by_id(form_id)
    if not form:
        raise AssistantshipServiceError("Assistantship form not found.")
    if form.roll_no_id != user.extrainfo.id:
        raise AssistantshipServiceError("You are not authorized to withdraw this assistantship form.")
    if form.TA_approved or form.TA_rejected:
        raise AssistantshipServiceError("Cannot withdraw after faculty supervisor has reviewed the form.")

    supervisor_user = selectors.get_user_by_username(form.ta_supervisor)
    if supervisor_user:
        otheracademic_notif(
            user,
            supervisor_user,
            "ast_ta",
            form.id,
            "student",
            "A PG assistantship form was withdrawn by the student.",
        )
    form.delete()


def update_assistantship_status_acad_admin(approved_ids, rejected_ids, actor_user):
    """Update assistantship status by Academic Admin (stage 5 disbursement audit)."""
    if approved_ids:
        for form_id in approved_ids:
            form = selectors.get_assistantship_by_id(form_id)
            if not form:
                continue
            if not form.Acad_approved or form.Acad_rejected:
                raise AssistantshipServiceError(
                    "Academic Admin can disburse only after HOD approval."
                )
            if form.remark == "Stipend disbursed (audit completed)":
                raise AssistantshipServiceError("This assistantship form is already marked as disbursed.")

            form.remark = "Stipend disbursed (audit completed)"
            form.save(update_fields=["remark"])

            student_user = selectors.get_user_by_extrainfo_id(form.roll_no_id)
            if student_user and actor_user:
                otheracademic_notif(
                    actor_user,
                    student_user,
                    "ast_ta_accept",
                    form.id,
                    "admin",
                    "Your assistantship stipend has been marked as disbursed by Academic Admin.",
                )

    if rejected_ids:
        for form_id in rejected_ids:
            form = selectors.get_assistantship_by_id(form_id)
            if not form:
                continue
            if not form.Acad_approved or form.Acad_rejected:
                raise AssistantshipServiceError(
                    "Academic Admin can act only after HOD approval."
                )
            if form.remark == "Stipend disbursed (audit completed)":
                raise AssistantshipServiceError("Cannot reject after stipend is marked disbursed.")

            form.remark = "Disbursement held by Academic Admin"
            form.save(update_fields=["remark"])

            student_user = selectors.get_user_by_extrainfo_id(form.roll_no_id)
            if student_user and actor_user:
                otheracademic_notif(
                    actor_user,
                    student_user,
                    "ast_ta_accept",
                    form.id,
                    "admin",
                    "Your assistantship disbursement has been put on hold by Academic Admin.",
                )


def update_assistantship_status_dean(approved_ids, rejected_ids, actor_user):
    """Update assistantship status by HOD (stage 4 final approval/rejection)."""
    if approved_ids:
        for form_id in approved_ids:
            form = selectors.get_assistantship_by_id(form_id)
            if not form:
                continue
            if not form.HOD_approved or form.HOD_rejected:
                raise AssistantshipServiceError("HOD can act only after Department Admin verification.")
            if form.Acad_approved or form.Acad_rejected:
                raise AssistantshipServiceError("This assistantship form is already reviewed by HOD.")

            form.Acad_approved = True
            form.Acad_rejected = False
            form.remark = "Approved by HOD"
            form.save(update_fields=["Acad_approved", "Acad_rejected", "remark"])

            student_user = selectors.get_user_by_extrainfo_id(form.roll_no_id)
            acad_admin_user = selectors.get_first_user_for_designation("acadadmin")
            if student_user and actor_user:
                otheracademic_notif(
                    actor_user,
                    student_user,
                    "ast_ta_accept",
                    form.id,
                    "admin",
                    "Your assistantship has been approved by HOD and forwarded to Academic Admin for disbursement audit.",
                )
            if acad_admin_user and actor_user:
                otheracademic_notif(
                    actor_user,
                    acad_admin_user,
                    "ast_hod",
                    form.id,
                    "admin",
                    "An HOD-approved assistantship form is waiting for disbursement audit.",
                )

    if rejected_ids:
        for form_id in rejected_ids:
            form = selectors.get_assistantship_by_id(form_id)
            if not form:
                continue
            if not form.HOD_approved or form.HOD_rejected:
                raise AssistantshipServiceError("HOD can act only after Department Admin verification.")
            if form.Acad_approved or form.Acad_rejected:
                raise AssistantshipServiceError("This assistantship form is already reviewed by HOD.")

            form.Acad_approved = False
            form.Acad_rejected = True
            form.remark = "Rejected by HOD"
            form.save(update_fields=["Acad_approved", "Acad_rejected", "remark"])

            student_user = selectors.get_user_by_extrainfo_id(form.roll_no_id)
            if student_user and actor_user:
                otheracademic_notif(
                    actor_user,
                    student_user,
                    "ast_ta_accept",
                    form.id,
                    "admin",
                    "Your assistantship has been rejected by HOD.",
                )


def update_assistantship_status_director(approved_ids, rejected_ids):
    """Update assistantship status by Director."""
    return None


def get_assistantship_status_text(form):
    """
    Determine the overall status text for an assistantship form.
    Returns 'Rejected', 'Approved', or 'Pending'.
    """
    is_rejected = any([
        form.TA_rejected,
        form.HOD_rejected,
        form.Acad_rejected,
    ])

    if is_rejected:
        return "Rejected"
    elif form.remark == "Stipend disbursed (audit completed)":
        return "Approved"
    else:
        return "Pending"


def get_assistantship_approval_stages(form):
    """Get approval status for each stage of the PG assistantship workflow."""
    stages = {
        "Faculty_Supervisor": ("TA_approved", "TA_rejected"),
        "Department_Admin": ("HOD_approved", "HOD_rejected"),
        "HOD": ("Acad_approved", "Acad_rejected"),
    }

    result = {}
    for stage_name, (approved_field, rejected_field) in stages.items():
        if getattr(form, approved_field):
            result[stage_name] = "Approved"
        elif getattr(form, rejected_field):
            result[stage_name] = "Rejected"
        else:
            result[stage_name] = "Pending"

    if form.remark == "Stipend disbursed (audit completed)":
        result["Acad_Admin_Audit"] = "Disbursed"
    elif form.Acad_approved and not form.Acad_rejected:
        result["Acad_Admin_Audit"] = "Pending"
    elif form.Acad_rejected:
        result["Acad_Admin_Audit"] = "On Hold"
    else:
        result["Acad_Admin_Audit"] = "Pending"

    return result


# ==================== PG TA ASSIGNMENT SERVICES ====================

def get_pg_ta_assignment_options():
    """Return PG students, subject options, and existing TA assignments."""
    students = selectors.get_pg_students_for_ta_assignment()
    subjects = selectors.get_subject_options_for_ta_assignment()
    assignments = selectors.get_all_pg_ta_assignments()

    assignment_map = {}
    for row in assignments:
        assignment_map.setdefault(row.pg_student_id, []).append(row)

    student_rows = []
    for student in students:
        existing_assignments = assignment_map.get(student.id_id, [])
        full_name = f"{student.id.user.first_name} {student.id.user.last_name}".strip() or student.id.user.username
        student_rows.append({
            "roll_no": student.id_id,
            "name": full_name,
            "programme": student.programme,
            "assigned_subject_ids": [row.subject_id for row in existing_assignments],
            "assigned_subjects": [
                {
                    "id": row.subject_id,
                    "code": row.subject.code,
                    "name": row.subject.name,
                    "label": f"{row.subject.code} - {row.subject.name}",
                }
                for row in existing_assignments
            ],
        })

    subject_rows = [
        {
            "id": subject.id,
            "code": subject.code,
            "name": subject.name,
            "label": f"{subject.code} - {subject.name}",
        }
        for subject in subjects
    ]

    return {
        "students": student_rows,
        "subjects": subject_rows,
    }


def upsert_pg_ta_assignments(assignments, actor_user):
    """Create, update, or remove TA assignments for PG students."""
    if not isinstance(assignments, list) or not assignments:
        raise TAAssignmentServiceError("At least one assignment is required.")

    updated_count = 0
    desired_subjects_by_student = {}

    for item in assignments:
        roll_no = item.get("roll_no")
        subject_ids = item.get("subject_ids")

        if not roll_no:
            raise TAAssignmentServiceError("Each assignment must include roll_no.")

        if subject_ids is None:
            subject_id = item.get("subject_id")
            subject_ids = [subject_id] if subject_id else []

        if not isinstance(subject_ids, list):
            raise TAAssignmentServiceError("subject_ids must be a list of subject ids.")

        clean_subject_ids = [int(subject_id) for subject_id in subject_ids if subject_id]
        desired_subjects_by_student.setdefault(str(roll_no), set()).update(clean_subject_ids)

    with transaction.atomic():
        for roll_no, desired_subject_ids in desired_subjects_by_student.items():
            student_user = selectors.get_user_by_username(str(roll_no))
            if not student_user:
                raise TAAssignmentServiceError(f"Student '{roll_no}' not found.")

            student = selectors.get_pg_students_for_ta_assignment().filter(id=student_user.extrainfo).first()
            if not student:
                raise TAAssignmentServiceError(f"Student '{roll_no}' is not a PG student.")

            existing_assignments = {
                row.subject_id: row
                for row in PGTAAssignment.objects.filter(pg_student=student_user.extrainfo)
            }

            subjects_qs = selectors.get_subject_options_for_ta_assignment().filter(
                id__in=desired_subject_ids
            )
            found_subjects = {subject.id: subject for subject in subjects_qs}
            missing_subject_ids = desired_subject_ids - set(found_subjects)
            if missing_subject_ids:
                missing_list = ", ".join(str(subject_id) for subject_id in sorted(missing_subject_ids))
                raise TAAssignmentServiceError(f"Subject id(s) '{missing_list}' not found.")

            for subject_id in desired_subject_ids:
                subject = found_subjects[subject_id]
                if subject_id not in existing_assignments:
                    PGTAAssignment.objects.create(
                        pg_student=student_user.extrainfo,
                        subject=subject,
                        assigned_by=actor_user,
                    )
                    PGTAAssignmentHistory.objects.create(
                        pg_student=student_user.extrainfo,
                        subject=subject,
                        assigned_by=actor_user,
                    )
                    updated_count += 1

            for subject_id, assignment in existing_assignments.items():
                if subject_id not in desired_subjects_by_student[roll_no]:
                    assignment.delete()
                    updated_count += 1

    return updated_count


def get_pg_faculty_supervisor_assignment_options():
    """Return PG students, faculty options, and existing faculty supervisor assignments."""
    students = selectors.get_pg_students_for_assignment()
    faculties = selectors.get_faculty_members_for_supervisor_assignment()
    assignments = selectors.get_all_pg_faculty_supervisor_assignments()

    assignment_map = {row.pg_student_id: row for row in assignments}

    student_rows = []
    for student in students:
        existing = assignment_map.get(student.id_id)
        full_name = f"{student.id.user.first_name} {student.id.user.last_name}".strip() or student.id.user.username
        student_rows.append({
            "roll_no": student.id_id,
            "name": full_name,
            "programme": student.programme,
            "assigned_faculty_id": existing.faculty_supervisor_id if existing else None,
            "assigned_faculty": (
                existing.faculty_supervisor.get_full_name().strip() or existing.faculty_supervisor.username
            ) if existing else None,
        })

    faculty_rows = []
    for faculty in faculties:
        user = faculty.id.user
        label_name = user.get_full_name().strip() or user.username
        faculty_rows.append(
            {
                "id": user.id,
                "username": user.username,
                "name": label_name,
                "label": f"{label_name} ({user.username})",
            }
        )

    return {
        "students": student_rows,
        "faculties": faculty_rows,
    }


def upsert_pg_faculty_supervisor_assignments(assignments, actor_user):
    """Create or update faculty supervisor assignments for PG students."""
    if not isinstance(assignments, list) or not assignments:
        raise TAAssignmentServiceError("At least one assignment is required.")

    valid_faculty_user_ids = set(
        selectors.get_faculty_members_for_supervisor_assignment().values_list("id__user_id", flat=True)
    )

    designation, _ = Designation.objects.get_or_create(
        name="faculty_supervisor",
        defaults={"full_name": "Faculty Supervisor", "type": "academic"},
    )

    updated_count = 0
    with transaction.atomic():
        for item in assignments:
            roll_no = item.get("roll_no")
            faculty_user_id = item.get("faculty_user_id")

            if not roll_no or not faculty_user_id:
                raise TAAssignmentServiceError("Each assignment must include roll_no and faculty_user_id.")

            student_user = selectors.get_user_by_username(str(roll_no))
            if not student_user:
                raise TAAssignmentServiceError(f"Student '{roll_no}' not found.")

            student = selectors.get_pg_students_for_assignment().filter(id=student_user.extrainfo).first()
            if not student:
                raise TAAssignmentServiceError(f"Student '{roll_no}' is not a valid PG student for assignment.")

            try:
                faculty_user_id = int(faculty_user_id)
            except (TypeError, ValueError):
                raise TAAssignmentServiceError("Invalid faculty_user_id.")

            if faculty_user_id not in valid_faculty_user_ids:
                raise TAAssignmentServiceError(f"Faculty user id '{faculty_user_id}' is not valid.")

            faculty_user = User.objects.filter(id=faculty_user_id).first()
            if not faculty_user:
                raise TAAssignmentServiceError(f"Faculty user id '{faculty_user_id}' not found.")

            # BR-52: restrict to faculty from relevant student department when both are available.
            student_department_id = getattr(student_user.extrainfo, "department_id", None)
            faculty_department_id = getattr(faculty_user.extrainfo, "department_id", None)
            if student_department_id and faculty_department_id and student_department_id != faculty_department_id:
                raise TAAssignmentServiceError(
                    "Faculty Supervisor must belong to the student's department."
                )

            PGFacultySupervisorAssignment.objects.update_or_create(
                pg_student=student_user.extrainfo,
                defaults={
                    "faculty_supervisor": faculty_user,
                    "assigned_by": actor_user,
                },
            )

            PGFacultySupervisorAssignmentHistory.objects.create(
                pg_student=student_user.extrainfo,
                faculty_supervisor=faculty_user,
                assigned_by=actor_user,
            )

            HoldsDesignation.objects.get_or_create(
                user=faculty_user,
                working=faculty_user,
                designation=designation,
            )
            updated_count += 1

    return updated_count
