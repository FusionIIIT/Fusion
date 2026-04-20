"""
HR2 Module Services - Stub Implementation

This is a stub implementation that allows the module to import without errors.
Full implementations will use actual Django models from models.py.
"""

import datetime
import json
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import CommandError
from django.db import transaction
from django.utils import timezone

from applications.globals.models import DepartmentInfo, Designation, ExtraInfo, HoldsDesignation, ModuleAccess
from applications.hr2.models import (
    AppraisalFormNew,
    AppraisalPeriod,
    CPDAAdvanceNew,
    CPDAReimbursementNew,
    Employee,
    EmployeeAttendance,
    EmployeeCategory,
    EmployeeDetailsExtended,
    EmployeeLeaveBalance,
    FacultyWorkload,
    LeaveApplicationNew,
    LeaveType,
    LTCApplicationNew,
    PerformanceAppraisalNew,
    PromotionApplication,
    TrainingNomination,
)
from applications.hr2 import selectors as hr2_selectors

try:
    from notifications.signals import notify
except ImportError:  # pragma: no cover - optional dependency
    notify = None

# ==================== CUSTOM EXCEPTIONS ====================

class InsufficientLeaveBalanceError(Exception):
    """Raised when employee doesn't have enough leave balance."""
    pass

class DuplicateLeaveApplicationError(Exception):
    """Raised when overlapping leave already exists."""
    pass

class InvalidWorkflowTransitionError(Exception):
    """Raised when workflow transition is invalid."""
    pass

class ResponsibilityNotAssignedError(Exception):
    """Raised when responsibility is not assigned."""
    pass

# ==================== LEAVE MANAGEMENT SERVICES ====================

def apply_for_leave(employee_extra_info, leave_type_id, from_date, to_date, reason,
                    address_during_leave="", contact_during_leave="", document=None,
                    academic_responsibility_user=None, academic_responsibility_designation=None,
                    administrative_responsibility_user=None, administrative_responsibility_designation=None):
    """Apply for leave - STUB IMPLEMENTATION."""
    raise NotImplementedError("Leave application service not yet fully implemented. Using LeaveForm model.")

def approve_leave_application(leave_app, approver_extra_info, remarks=""):
    """Approve leave application - STUB IMPLEMENTATION."""
    raise NotImplementedError("Leave approval service not yet fully implemented.")

def reject_leave_application(leave_app, approver_extra_info, remarks=""):
    """Reject leave application - STUB IMPLEMENTATION."""
    raise NotImplementedError("Leave rejection service not yet fully implemented.")

def handle_academic_responsibility(leave_app, approver_extra_info, action, remarks=""):
    """Handle academic responsibility for leave - STUB IMPLEMENTATION."""
    raise NotImplementedError("Academic responsibility handler not yet fully implemented.")

def handle_administrative_responsibility(leave_app, approver_extra_info, action, remarks=""):
    """Handle administrative responsibility for leave - STUB IMPLEMENTATION."""
    raise NotImplementedError("Administrative responsibility handler not yet fully implemented.")

# ==================== ATTENDANCE SERVICES ====================

def mark_attendance(employee_extra_info, date_val, status, in_time=None, out_time=None, remarks=""):
    """Mark attendance - STUB IMPLEMENTATION."""
    raise NotImplementedError("Attendance marking service not yet fully implemented.")

# ==================== FACULTY WORKLOAD SERVICES ====================

def calculate_faculty_workload(faculty_extra_info, semester, year):
    """Calculate faculty workload - STUB IMPLEMENTATION."""
    raise NotImplementedError("Faculty workload calculation service not yet fully implemented.")

# ==================== LTC SERVICES ====================

def apply_ltc(employee_extra_info, data):
    """Apply for LTC - STUB IMPLEMENTATION."""
    raise NotImplementedError("LTC application service not yet fully implemented.")

def approve_ltc(ltc_app, approver_extra_info, remarks=""):
    """Approve LTC - STUB IMPLEMENTATION."""
    raise NotImplementedError("LTC approval service not yet fully implemented.")

def reject_ltc(ltc_app, approver_extra_info, remarks=""):
    """Reject LTC - STUB IMPLEMENTATION."""
    raise NotImplementedError("LTC rejection service not yet fully implemented.")

# ==================== CPDA ADVANCE SERVICES ====================

def apply_cpda_advance(employee_extra_info, data):
    """Apply for CPDA Advance - STUB IMPLEMENTATION."""
    raise NotImplementedError("CPDA Advance application service not yet fully implemented.")

def approve_cpda_advance(cpda_adv, approver_extra_info, remarks=""):
    """Approve CPDA Advance - STUB IMPLEMENTATION."""
    raise NotImplementedError("CPDA Advance approval service not yet fully implemented.")

def reject_cpda_advance(cpda_adv, approver_extra_info, remarks=""):
    """Reject CPDA Advance - STUB IMPLEMENTATION."""
    raise NotImplementedError("CPDA Advance rejection service not yet fully implemented.")

# ==================== CPDA REIMBURSEMENT SERVICES ====================

def apply_cpda_reimbursement(employee_extra_info, data):
    """Apply for CPDA Reimbursement - STUB IMPLEMENTATION."""
    raise NotImplementedError("CPDA Reimbursement application service not yet fully implemented.")

def approve_cpda_reimbursement(cpda_reim, approver_extra_info, remarks=""):
    """Approve CPDA Reimbursement - STUB IMPLEMENTATION."""
    raise NotImplementedError("CPDA Reimbursement approval service not yet fully implemented.")

def reject_cpda_reimbursement(cpda_reim, approver_extra_info, remarks=""):
    """Reject CPDA Reimbursement - STUB IMPLEMENTATION."""
    raise NotImplementedError("CPDA Reimbursement rejection service not yet fully implemented.")

# ==================== APPRAISAL SERVICES ====================

def submit_appraisal(employee_extra_info, data):
    """Submit appraisal - STUB IMPLEMENTATION."""
    raise NotImplementedError("Appraisal submission service not yet fully implemented.")

def review_appraisal(appraisal_id, reviewer_extra_info, reviewer_scores, reviewer_remarks):
    """Review appraisal - STUB IMPLEMENTATION."""
    raise NotImplementedError("Appraisal review service not yet fully implemented.")


# ==================== API WRITE SERVICES ====================

def _update_instance_from_data(instance, data):
    for key, value in data.items():
        setattr(instance, key, value)
    instance.save()
    return instance


def update_instance(instance, validated_data):
    return _update_instance_from_data(instance, validated_data)


def create_leave_application(request_user, validated_data):
    employee_id = (validated_data.get('employee_id') or '').strip()
    employee = hr2_selectors.get_employee_for_user(request_user)
    if employee is None and employee_id:
        employee = hr2_selectors.get_employee_by_id_optional(employee_id)
    if employee is None:
        raise ValidationError({"employee_id": "Employee profile not found."})

    nominee_id = (validated_data.get('nominee_employee_id') or '').strip()
    nominee_status = 'PENDING' if nominee_id else 'NOT_REQUIRED'

    role_flags = hr2_selectors.get_role_flags(employee.user)
    is_director = role_flags.get('is_director')
    is_hod = role_flags.get('is_hod')
    is_registrar = role_flags.get('is_registrar')
    is_hr_admin = role_flags.get('is_hr_admin')
    is_accountant = role_flags.get('is_accountant')

    leave_type_name = (validated_data.get('leave_type') or '').strip()
    is_cl_rh_leave = leave_type_name in ['Casual', 'Restricted']

    employee_name = employee.user.get_full_name() or employee.user.username
    department_name = employee.department.name if employee.department else (validated_data.get('department') or '')
    designation_name = ''
    designation_record = hr2_selectors.get_employee_current_designation_for_user(employee.user)
    if designation_record:
        designation_name = designation_record.full_name or designation_record.name
    else:
        designation_name = validated_data.get('designation') or ''

    approval_status = 'PENDING'
    approver_role = ''
    if is_director:
        approval_status = 'APPROVED'
        approver_role = 'Director'
    elif is_registrar:
        approval_status = 'FORWARDED'
        approver_role = 'Director'
    elif is_hod:
        if is_cl_rh_leave:
            approval_status = 'PENDING'
            approver_role = 'HOD'
        else:
            approval_status = 'FORWARDED'
            approver_role = 'Director'
    elif is_hr_admin or is_accountant:
        approval_status = 'FORWARDED'
        approver_role = 'Registrar'

    data = dict(validated_data)
    data.pop('employee_id', None)
    data.pop('nominee_employee_id', None)
    leave_app = LeaveApplicationNew(
        employee=employee,
        employee_name=employee_name,
        department=department_name,
        designation=designation_name,
        handover_to=nominee_id,
        nominee_status=nominee_status,
        approval_status=approval_status,
        current_approver_role=approver_role,
        **data,
    )
    leave_app.save()

    if is_director:
        apply_leave_balance_for_approval(leave_app)
        leave_app.save(update_fields=['leave_balance_before', 'leave_balance_after'])

    return leave_app


def update_leave_application(leave_app, validated_data):
    return _update_instance_from_data(leave_app, validated_data)


def withdraw_leave_application(leave_app, user, remarks):
    if leave_app.employee != user.extrainfo:
        raise PermissionError("Not authorized")
    if leave_app.approval_status not in ['PENDING', 'FORWARDED']:
        raise ValidationError({"approval_status": "Only pending or forwarded requests can be withdrawn."})

    role_flags = hr2_selectors.get_role_flags(user)
    if role_flags.get('is_registrar'):
        leave_app.approval_status = 'REJECTED'
        leave_app.current_approver_role = 'Registrar'
    elif role_flags.get('is_accountant'):
        leave_app.approval_status = 'REJECTED'
        leave_app.current_approver_role = 'Accountant'
    elif role_flags.get('is_hr_admin'):
        leave_app.approval_status = 'REJECTED'
        leave_app.current_approver_role = 'HR Admin'
    else:
        leave_app.approval_status = 'WITHDRAWN'
        leave_app.current_approver_role = 'Employee'

    leave_app.remarks = (remarks or '').strip()
    leave_app.save(update_fields=['approval_status', 'current_approver_role', 'remarks'])
    return leave_app


def request_leave_cancellation(leave_app, user, reason):
    if leave_app.employee != user.extrainfo:
        raise PermissionError("Not authorized")
    if leave_app.approval_status != 'APPROVED':
        raise ValidationError({"approval_status": "Only approved requests can be cancelled."})
    if leave_app.cancel_status != 'NOT_REQUESTED':
        raise ValidationError({"cancel_status": "Cancellation already processed or pending."})

    today = timezone.now().date()
    if today >= leave_app.start_date:
        raise ValidationError({"start_date": "Cancellation allowed only up to 1 day prior to start date."})

    role_flags = hr2_selectors.get_role_flags(user)
    requester_role = 'Employee'
    if role_flags.get('is_director'):
        requester_role = 'Director'
    elif role_flags.get('is_hod'):
        requester_role = 'HOD'
    elif role_flags.get('is_registrar'):
        requester_role = 'Registrar'
    elif role_flags.get('is_accountant'):
        requester_role = 'Accountant'
    elif role_flags.get('is_hr_admin'):
        requester_role = 'HR Admin'

    cancel_approver_role = 'HOD'
    if requester_role in ['HOD', 'Director', 'Registrar']:
        cancel_approver_role = 'Director'
    elif requester_role in ['Accountant', 'HR Admin']:
        cancel_approver_role = 'Registrar'

    leave_app.cancel_status = 'REQUESTED'
    leave_app.cancel_requested_at = timezone.now()
    leave_app.cancel_requested_by_role = requester_role
    leave_app.cancel_current_approver_role = cancel_approver_role
    leave_app.cancel_reason = (reason or '').strip()
    leave_app.save(update_fields=[
        'cancel_status',
        'cancel_requested_at',
        'cancel_requested_by_role',
        'cancel_current_approver_role',
        'cancel_reason',
    ])
    return leave_app


def decide_leave_cancellation(leave_app, user, decision, remarks):
    decision = (decision or '').lower()
    if decision not in ['approve', 'reject']:
        raise ValidationError({"decision": "Invalid decision"})
    if leave_app.cancel_status != 'REQUESTED':
        raise ValidationError({"cancel_status": "No cancellation request pending."})

    approver_role = (leave_app.cancel_current_approver_role or '').lower()
    role_flags = hr2_selectors.get_role_flags(user)
    allowed = False
    if approver_role == 'hod':
        allowed = role_flags.get('is_hod')
    elif approver_role == 'director':
        allowed = role_flags.get('is_director')
    elif approver_role == 'registrar':
        allowed = role_flags.get('is_registrar')

    if not allowed:
        raise PermissionError("Not authorized")

    leave_app.cancel_decided_at = timezone.now()
    leave_app.cancel_decision_remarks = (remarks or '').strip()

    if decision == 'approve':
        leave_app.cancel_status = 'APPROVED'
        leave_app.approval_status = 'CANCELLED'
        leave_app.current_approver_role = leave_app.cancel_current_approver_role
        restore_leave_balance_for_cancellation(leave_app)
    else:
        leave_app.cancel_status = 'REJECTED'

    leave_app.save(update_fields=[
        'cancel_status',
        'cancel_decided_at',
        'cancel_decision_remarks',
        'approval_status',
        'current_approver_role',
        'leave_balance_before',
        'leave_balance_after',
    ])
    return leave_app


def request_leave_extension(leave_app, user, new_end_date, reason):
    if leave_app.employee != user.extrainfo:
        raise PermissionError("Not authorized")
    if leave_app.approval_status != 'APPROVED':
        raise ValidationError({"approval_status": "Only approved requests can be extended."})
    if leave_app.extension_status != 'NOT_REQUESTED':
        raise ValidationError({"extension_status": "Extension already processed or pending."})

    today = timezone.now().date()
    if today >= leave_app.end_date:
        raise ValidationError({"end_date": "Extension allowed only before the original end date."})
    if new_end_date <= leave_app.end_date:
        raise ValidationError({"end_date": "New end date must be after the current end date."})

    new_total_days = Decimal((new_end_date - leave_app.start_date).days + 1)

    role_flags = hr2_selectors.get_role_flags(user)
    requester_role = 'Employee'
    if role_flags.get('is_director'):
        requester_role = 'Director'
    elif role_flags.get('is_hod'):
        requester_role = 'HOD'
    elif role_flags.get('is_registrar'):
        requester_role = 'Registrar'
    elif role_flags.get('is_accountant'):
        requester_role = 'Accountant'
    elif role_flags.get('is_hr_admin'):
        requester_role = 'HR Admin'

    approver_role = 'HOD'
    if requester_role in ['HOD', 'Director', 'Registrar']:
        approver_role = 'Director'
    elif requester_role in ['Accountant', 'HR Admin']:
        approver_role = 'Registrar'

    leave_app.extension_status = 'REQUESTED'
    leave_app.extension_requested_at = timezone.now()
    leave_app.extension_requested_by_role = requester_role
    leave_app.extension_current_approver_role = approver_role
    leave_app.extension_reason = (reason or '').strip()
    leave_app.extension_new_end_date = new_end_date
    leave_app.extension_new_total_days = new_total_days
    leave_app.save(update_fields=[
        'extension_status',
        'extension_requested_at',
        'extension_requested_by_role',
        'extension_current_approver_role',
        'extension_reason',
        'extension_new_end_date',
        'extension_new_total_days',
    ])
    return leave_app


def decide_leave_extension(leave_app, user, decision, remarks):
    decision = (decision or '').lower()
    if decision not in ['approve', 'reject']:
        raise ValidationError({"decision": "Invalid decision"})
    if leave_app.extension_status != 'REQUESTED':
        raise ValidationError({"extension_status": "No extension request pending."})

    approver_role = (leave_app.extension_current_approver_role or '').lower()
    role_flags = hr2_selectors.get_role_flags(user)
    allowed = False
    if approver_role == 'hod':
        allowed = role_flags.get('is_hod')
    elif approver_role == 'director':
        allowed = role_flags.get('is_director')
    elif approver_role == 'registrar':
        allowed = role_flags.get('is_registrar')

    if not allowed:
        raise PermissionError("Not authorized")

    leave_app.extension_decided_at = timezone.now()
    leave_app.extension_decision_remarks = (remarks or '').strip()

    if decision == 'approve':
        if not apply_leave_balance_for_extension(leave_app):
            raise InsufficientLeaveBalanceError("Insufficient leave balance for extension.")
        leave_app.extension_status = 'APPROVED'
        leave_app.current_approver_role = leave_app.extension_current_approver_role
        leave_app.end_date = leave_app.extension_new_end_date
        leave_app.total_days = leave_app.extension_new_total_days
    else:
        leave_app.extension_status = 'REJECTED'

    leave_app.save(update_fields=[
        'extension_status',
        'extension_decided_at',
        'extension_decision_remarks',
        'current_approver_role',
        'leave_balance_before',
        'leave_balance_after',
        'end_date',
        'total_days',
    ])
    return leave_app


def submit_leave_resumption(leave_app, user, resumption_date, reason):
    if leave_app.employee != user.extrainfo:
        raise PermissionError("Not authorized")
    if leave_app.approval_status != 'APPROVED':
        raise ValidationError({"approval_status": "Resumption allowed only for approved leaves."})
    if leave_app.resumption_status != 'NOT_REQUESTED':
        raise ValidationError({"resumption_status": "Resumption already submitted or processed."})
    if resumption_date <= leave_app.end_date:
        raise ValidationError({"resumption_date": "Resumption date must be after the leave end date."})

    leave_app.resumption_status = 'SUBMITTED'
    leave_app.resumption_date = resumption_date
    leave_app.resumption_reason = (reason or '').strip()
    leave_app.resumption_submitted_at = timezone.now()
    leave_app.resumption_current_approver_role = 'HOD'
    leave_app.save(update_fields=[
        'resumption_status',
        'resumption_date',
        'resumption_reason',
        'resumption_submitted_at',
        'resumption_current_approver_role',
    ])
    return leave_app


def decide_leave_resumption(leave_app, user, decision, remarks):
    decision = (decision or '').lower()
    if decision not in ['approve', 'reject']:
        raise ValidationError({"decision": "Invalid decision"})
    if leave_app.resumption_status != 'SUBMITTED':
        raise ValidationError({"resumption_status": "No resumption request pending."})

    role_flags = hr2_selectors.get_role_flags(user)
    if not role_flags.get('is_hod'):
        raise PermissionError("Not authorized")

    leave_app.resumption_decided_at = timezone.now()
    leave_app.resumption_decision_remarks = (remarks or '').strip()
    if decision == 'approve':
        leave_app.resumption_status = 'APPROVED'
        leave_app.current_approver_role = 'HOD'
    else:
        leave_app.resumption_status = 'REJECTED'

    leave_app.save(update_fields=[
        'resumption_status',
        'resumption_decided_at',
        'resumption_decision_remarks',
        'current_approver_role',
    ])
    return leave_app


def respond_leave_nominee(leave_app, user, action):
    action = (action or '').lower()
    if action not in ['accept', 'decline']:
        raise ValidationError({"action": "Invalid action"})
    if leave_app.handover_to != user.extrainfo.id:
        raise PermissionError("Not authorized")

    leave_app.nominee_status = 'ACCEPTED' if action == 'accept' else 'DECLINED'
    leave_app.nominee_responded_at = datetime.datetime.utcnow()
    leave_app.save(update_fields=['nominee_status', 'nominee_responded_at'])
    return leave_app


def request_leave_document(leave_app, user, message):
    if not message:
        raise ValidationError({"message": "Document request message is required."})
    role_flags = hr2_selectors.get_role_flags(user)
    if not role_flags.get('is_hod'):
        raise PermissionError("Not authorized")
    if leave_app.document_request_status == 'REQUESTED':
        raise ValidationError({"document_request_status": "Document already requested."})

    leave_app.document_request_message = message
    leave_app.document_request_status = 'REQUESTED'
    leave_app.document_requested_at = datetime.datetime.utcnow()
    leave_app.save(update_fields=['document_request_message', 'document_request_status', 'document_requested_at'])
    return leave_app


def submit_leave_document(leave_app, user, submission):
    if not submission:
        raise ValidationError({"submission": "Document submission is required."})
    if leave_app.employee != user.extrainfo:
        raise PermissionError("Not authorized")
    if leave_app.document_request_status != 'REQUESTED':
        raise ValidationError({"document_request_status": "No document requested for this leave."})

    leave_app.document_submission = submission
    leave_app.document_request_status = 'SUBMITTED'
    leave_app.document_submitted_at = datetime.datetime.utcnow()
    leave_app.save(update_fields=['document_submission', 'document_request_status', 'document_submitted_at'])
    return leave_app


def decide_leave_application(leave_app, user, decision, remarks):
    decision = (decision or '').lower()
    if decision not in ['approve', 'reject', 'forward']:
        raise ValidationError({"decision": "Invalid decision"})

    role_flags = hr2_selectors.get_role_flags(user)
    approver_role = 'HOD'
    if role_flags.get('is_registrar'):
        approver_role = 'Registrar'
    elif role_flags.get('is_director'):
        approver_role = 'Director'

    leave_type_name = (leave_app.leave_type or '').strip()
    is_cl_rh_leave = leave_type_name in ['Casual', 'Restricted']
    if decision == 'approve' and not is_cl_rh_leave and approver_role == 'HOD':
        raise ValidationError({"decision": "Only CL/RH leaves can be approved by HOD. Please forward to Director."})
    if decision == 'forward' and is_cl_rh_leave:
        decision = 'approve'

    if decision == 'approve':
        leave_app.approval_status = 'APPROVED'
        leave_app.current_approver_role = approver_role
        apply_leave_balance_for_approval(leave_app)
    elif decision == 'forward':
        leave_app.approval_status = 'FORWARDED'
        leave_app.current_approver_role = 'Director'
    else:
        leave_app.approval_status = 'REJECTED'
        leave_app.current_approver_role = approver_role

    leave_app.remarks = remarks
    leave_app.save(update_fields=[
        'approval_status',
        'remarks',
        'current_approver_role',
        'leave_balance_before',
        'leave_balance_after',
    ])
    return leave_app


def apply_leave_balance_for_approval(leave_app):
    leave_type = hr2_selectors.get_leave_type_by_name(leave_app.leave_type)
    if not leave_type:
        return
    year = leave_app.start_date.year
    balance = hr2_selectors.get_leave_balance_for_employee_year(
        leave_app.employee,
        leave_type,
        year,
    )
    if balance is None:
        balance = hr2_selectors.get_latest_leave_balance_for_employee(leave_app.employee, leave_type)
    if balance is None or balance.year != year:
        balance = EmployeeLeaveBalance(
            employee=leave_app.employee,
            leave_type=leave_type,
            year=year,
            opening_balance=Decimal('0'),
            accrued=Decimal('0'),
            availed=Decimal('0'),
            current_balance=Decimal('0'),
        )
        balance.save()

    total_days = Decimal(str(leave_app.total_days or 0))
    before_balance = balance.current_balance
    balance.availed = (balance.availed or 0) + total_days
    balance.current_balance = (balance.current_balance or 0) - total_days
    balance.save(update_fields=['availed', 'current_balance'])

    if leave_app.leave_balance_before is None:
        leave_app.leave_balance_before = before_balance
    leave_app.leave_balance_after = balance.current_balance


def restore_leave_balance_for_cancellation(leave_app):
    leave_type = hr2_selectors.get_leave_type_by_name(leave_app.leave_type)
    if not leave_type:
        return
    year = leave_app.start_date.year
    balance = hr2_selectors.get_leave_balance_for_employee_year(
        leave_app.employee,
        leave_type,
        year,
    )
    if balance is None:
        balance = hr2_selectors.get_latest_leave_balance_for_employee(leave_app.employee, leave_type)
    if balance is None:
        return

    total_days = Decimal(str(leave_app.total_days or 0))
    before_balance = balance.current_balance
    balance.availed = (balance.availed or 0) - total_days
    balance.current_balance = (balance.current_balance or 0) + total_days
    balance.save(update_fields=['availed', 'current_balance'])

    if leave_app.leave_balance_before is None:
        leave_app.leave_balance_before = before_balance
    leave_app.leave_balance_after = balance.current_balance


def apply_leave_balance_for_extension(leave_app):
    if not leave_app.extension_new_total_days:
        return False
    delta_days = Decimal(str(leave_app.extension_new_total_days)) - Decimal(str(leave_app.total_days or 0))
    if delta_days <= 0:
        return False

    leave_type = hr2_selectors.get_leave_type_by_name(leave_app.leave_type)
    if not leave_type:
        return False
    year = leave_app.start_date.year
    balance = hr2_selectors.get_leave_balance_for_employee_year(
        leave_app.employee,
        leave_type,
        year,
    )
    if balance is None:
        balance = hr2_selectors.get_latest_leave_balance_for_employee(leave_app.employee, leave_type)
    if balance is None:
        return False

    if (balance.current_balance or 0) < delta_days:
        return False

    before_balance = balance.current_balance
    balance.availed = (balance.availed or 0) + delta_days
    balance.current_balance = (balance.current_balance or 0) - delta_days
    balance.save(update_fields=['availed', 'current_balance'])

    if leave_app.leave_balance_before is None:
        leave_app.leave_balance_before = before_balance
    leave_app.leave_balance_after = balance.current_balance
    return True


def create_attendance(employee, validated_data):
    attendance = EmployeeAttendance(employee=employee, **validated_data)
    attendance.save()
    return attendance


def create_performance_appraisal(employee, validated_data):
    appraisal = PerformanceAppraisalNew(employee=employee, **validated_data)
    appraisal.save()
    return appraisal


def create_training_nomination(employee, nominated_by, validated_data):
    nomination = TrainingNomination(employee=employee, nominated_by=nominated_by, **validated_data)
    nomination.save()
    return nomination


def create_promotion_application(employee, validated_data):
    promotion = PromotionApplication(employee=employee, **validated_data)
    promotion.save()
    return promotion


def create_ltc_application(employee, validated_data):
    ltc = LTCApplicationNew(employee=employee, **validated_data)
    ltc.save()
    return ltc


def update_ltc_application(ltc, validated_data):
    return _update_instance_from_data(ltc, validated_data)


def withdraw_ltc_application(ltc, user, remarks):
    if ltc.employee != user.extrainfo:
        raise PermissionError("Not authorized")
    if ltc.approval_status != 'PENDING':
        raise ValidationError({"approval_status": "Only pending requests can be withdrawn."})

    ltc.approval_status = 'WITHDRAWN'
    ltc.remarks = (remarks or '').strip()
    ltc.save(update_fields=['approval_status', 'remarks'])
    return ltc


def decide_ltc_application(ltc, decision, remarks):
    decision = (decision or '').lower()
    if decision not in ['approve', 'reject', 'forward']:
        raise ValidationError({"decision": "Invalid decision"})

    if decision == 'approve':
        ltc.approval_status = 'APPROVED'
        ltc.accountant_status = 'APPROVED'
    elif decision == 'forward':
        ltc.approval_status = 'FORWARDED'
        ltc.verified_by_hr = True
        ltc.accountant_status = 'PENDING'
    else:
        ltc.approval_status = 'REJECTED'
        ltc.accountant_status = 'REJECTED'

    ltc.remarks = remarks
    ltc.save(update_fields=['approval_status', 'remarks', 'verified_by_hr', 'accountant_status'])
    return ltc


def create_cpda_advance(employee, validated_data):
    cpda = CPDAAdvanceNew(employee=employee, **validated_data)
    cpda.save()
    return cpda


def withdraw_cpda_advance(cpda, user, remarks):
    if cpda.employee != user.extrainfo:
        raise PermissionError("Not authorized")
    if cpda.approval_status != 'PENDING':
        raise ValidationError({"approval_status": "Only pending requests can be withdrawn."})

    cpda.approval_status = 'WITHDRAWN'
    cpda.remarks = (remarks or '').strip()
    cpda.save(update_fields=['approval_status', 'remarks'])
    return cpda


def decide_cpda_advance(cpda, user, decision, remarks):
    decision = (decision or '').lower()
    if decision not in ['approve', 'reject', 'forward-director']:
        raise ValidationError({"decision": "Invalid decision"})

    role_flags = hr2_selectors.get_role_flags(user)
    if role_flags.get('is_hr_staff'):
        if decision == 'reject':
            cpda.approval_status = 'REJECTED'
            cpda.accountant_processing_status = 'REJECTED'
        else:
            cpda.approval_status = 'FORWARDED'
            cpda.verified_by_hr = True
            cpda.accountant_processing_status = 'DIRECTOR_REVIEW'
    elif role_flags.get('is_director'):
        if decision == 'reject':
            cpda.approval_status = 'REJECTED'
            cpda.accountant_processing_status = 'REJECTED'
        else:
            cpda.approval_status = 'FORWARDED'
            cpda.accountant_processing_status = 'PENDING'
    elif role_flags.get('is_accountant'):
        if decision == 'reject':
            cpda.approval_status = 'REJECTED'
            cpda.accountant_processing_status = 'REJECTED'
        else:
            cpda.approval_status = 'APPROVED'
            cpda.accountant_processing_status = 'APPROVED'
    else:
        raise PermissionError("Not authorized")

    cpda.remarks = remarks
    cpda.save(update_fields=['approval_status', 'remarks', 'verified_by_hr', 'accountant_processing_status'])
    return cpda


def create_cpda_reimbursement(employee, validated_data):
    reimbursement = CPDAReimbursementNew(employee=employee, **validated_data)
    reimbursement.save()
    return reimbursement


def decide_cpda_reimbursement(reimbursement, decision, reviewer, remarks):
    decision = (decision or '').lower()
    if decision == 'approve':
        reimbursement.approval_status = 'APPROVED'
        reimbursement.verified_by_hr = True
    else:
        reimbursement.approval_status = 'REJECTED'
    reimbursement.remarks = remarks
    reimbursement.save(update_fields=['approval_status', 'verified_by_hr', 'remarks'])
    return reimbursement


def create_appraisal_form(employee, validated_data):
    appraisal = AppraisalFormNew(employee=employee, **validated_data)
    appraisal.save()
    return appraisal


def review_appraisal_form(appraisal, user, action, remarks, rating):
    role_flags = hr2_selectors.get_role_flags(user)
    if role_flags.get('is_hod') and appraisal.assigned_reviewer_role.upper() != 'HOD':
        raise PermissionError("Not assigned to HOD review.")
    if role_flags.get('is_director') and appraisal.assigned_reviewer_role.upper() != 'DIRECTOR':
        raise PermissionError("Not assigned to Director review.")
    if not (role_flags.get('is_hod') or role_flags.get('is_director')):
        raise PermissionError("Not authorized to review.")

    appraisal.reviewer_id = str(user.extrainfo.id)
    appraisal.reviewer_comments = (remarks or '')
    if rating:
        appraisal.rating = str(rating)

    if action == 'approve':
        appraisal.status = 'APPROVED'
        appraisal.assigned_reviewer_role = ''
        appraisal.assigned_reviewer = None
    elif action == 'forward':
        appraisal.status = 'REVIEWED'
        appraisal.assigned_reviewer_role = 'DIRECTOR'
        appraisal.assigned_reviewer = None
    else:
        appraisal.status = 'REVIEWED'

    appraisal.save(update_fields=[
        'reviewer_id',
        'reviewer_comments',
        'rating',
        'status',
        'assigned_reviewer_role',
        'assigned_reviewer',
    ])
    return appraisal


def assign_appraisal_reviewer(appraisal, user, role, reviewer_id):
    role_flags = hr2_selectors.get_role_flags(user)
    if not role_flags.get('is_hr_staff'):
        raise PermissionError("Not authorized to assign.")
    if role not in ['HOD', 'DIRECTOR']:
        raise ValidationError({"role": "Role must be HOD or DIRECTOR."})
    if appraisal.status != 'PENDING':
        raise ValidationError({"status": "Only pending appraisals can be assigned."})

    assigned_reviewer = hr2_selectors.get_reviewer_by_id(reviewer_id)
    if reviewer_id and not assigned_reviewer:
        raise ValidationError({"reviewer_id": "Reviewer not found."})

    appraisal.assigned_reviewer_role = role
    appraisal.assigned_reviewer = assigned_reviewer
    appraisal.assigned_by = user.extrainfo
    appraisal.assigned_at = timezone.now()
    appraisal.save(update_fields=[
        'assigned_reviewer_role',
        'assigned_reviewer',
        'assigned_by',
        'assigned_at',
    ])
    return appraisal


# ==================== MANAGEMENT COMMAND SERVICES ====================

DEFAULT_LEAVE_BALANCES = [
    ("Casual", "CL", 10),
    ("Restricted", "RL", 5),
    ("Medical", "ML", 12),
    ("Earned", "EL", 18),
    ("Vacation", "VL", 20),
    ("Sabbatical", "SL", 0),
]

ROLE_LEAVE_BALANCES = {
    "EMP1002": {"CL": 12, "RL": 6, "ML": 15, "EL": 25, "VL": 30, "SL": 10},
    "EMP1003": {"CL": 15, "RL": 8, "ML": 20, "EL": 30, "VL": 35, "SL": 15},
    "EMP1004": {"CL": 12, "RL": 6, "ML": 15, "EL": 22, "VL": 28, "SL": 5},
    "EMP1005": {"CL": 10, "RL": 5, "ML": 12, "EL": 20, "VL": 25, "SL": 0},
    "EMP1006": {"CL": 10, "RL": 5, "ML": 12, "EL": 18, "VL": 22, "SL": 0},
    "EMP1007": {"CL": 12, "RL": 6, "ML": 15, "EL": 25, "VL": 30, "SL": 12},
}


def seed_leave_balances(employee_id=None, seed_all=False, year=None):
    if year is None:
        year = datetime.date.today().year

    for name, code, _value in DEFAULT_LEAVE_BALANCES:
        LeaveType.objects.get_or_create(
            name=name,
            code=code,
            defaults={"is_active": True},
        )

    if seed_all:
        employees = ExtraInfo.objects.all()
    else:
        if not employee_id:
            employee_id = "EMP1001"
        try:
            employees = [ExtraInfo.objects.get(id=employee_id)]
        except ExtraInfo.DoesNotExist as exc:
            raise CommandError(f"Employee not found: {employee_id}") from exc

    seeded_count = 0
    for employee in employees:
        balance_map = ROLE_LEAVE_BALANCES.get(employee.id, {})
        for name, code, default_value in DEFAULT_LEAVE_BALANCES:
            value = balance_map.get(code, default_value)
            leave_type = LeaveType.objects.get(code=code)
            EmployeeLeaveBalance.objects.update_or_create(
                employee=employee,
                leave_type=leave_type,
                year=year,
                defaults={
                    "opening_balance": value,
                    "accrued": 0,
                    "availed": 0,
                    "current_balance": value,
                },
            )
        seeded_count += 1

    return {"seeded_count": seeded_count, "year": year}


def _parse_date(value):
    if not value:
        return None
    return datetime.date.fromisoformat(value)


def _parse_gender(value):
    if not value:
        return "M"
    value = value.strip().lower()
    if value.startswith("f"):
        return "F"
    if value.startswith("m"):
        return "M"
    return "O"


def _split_name(full_name):
    if not full_name:
        return "", ""
    parts = full_name.strip().split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def seed_hr_demo_data():
    departments = [
        "Computer Science and Engineering",
        "Administration",
        "Finance",
        "Director Office",
    ]

    employees = [
        {
            "employee_id": "EMP1001",
            "name": "Rahul Sharma",
            "email": "rahul.sharma@iiitdmj.ac.in",
            "phone": "9876543210",
            "gender": "Male",
            "dob": "1990-05-12",
            "department": "Computer Science and Engineering",
            "designation": "Assistant Professor",
            "role": "Employee",
            "employment_type": "Permanent",
            "date_of_joining": "2021-08-01",
            "reporting_to": "EMP1002",
            "status": "Active",
        },
        {
            "employee_id": "EMP1007",
            "name": "Dr. Anjali Mehta",
            "email": "anjali.mehta@iiitdmj.ac.in",
            "phone": "9876543216",
            "gender": "Female",
            "dob": "1985-11-08",
            "department": "Computer Science and Engineering",
            "designation": "Professor",
            "role": "Employee",
            "employment_type": "Permanent",
            "date_of_joining": "2016-07-20",
            "reporting_to": "EMP1002",
            "status": "Active",
        },
        {
            "employee_id": "EMP1002",
            "name": "Dr. Anil Kumar",
            "email": "anil.kumar@iiitdmj.ac.in",
            "phone": "9876543211",
            "gender": "Male",
            "dob": "1980-07-20",
            "department": "Computer Science and Engineering",
            "designation": "Professor and HOD",
            "role": "HOD",
            "employment_type": "Permanent",
            "date_of_joining": "2015-06-15",
            "reporting_to": "EMP1003",
            "status": "Active",
        },
        {
            "employee_id": "EMP1003",
            "name": "Dr. Meena Verma",
            "email": "director@iiitdmj.ac.in",
            "phone": "9876543212",
            "gender": "Female",
            "dob": "1975-02-11",
            "department": "Director Office",
            "designation": "Director",
            "role": "Director",
            "employment_type": "Permanent",
            "date_of_joining": "2019-01-10",
            "reporting_to": None,
            "status": "Active",
        },
        {
            "employee_id": "EMP1004",
            "name": "Suresh Verma",
            "email": "registrar@iiitdmj.ac.in",
            "phone": "9876543213",
            "gender": "Male",
            "dob": "1982-03-10",
            "department": "Administration",
            "designation": "Registrar",
            "role": "Registrar",
            "employment_type": "Permanent",
            "date_of_joining": "2018-01-15",
            "reporting_to": "EMP1003",
            "status": "Active",
        },
        {
            "employee_id": "EMP1005",
            "name": "Priya Nair",
            "email": "hr.admin@iiitdmj.ac.in",
            "phone": "9876543214",
            "gender": "Female",
            "dob": "1987-09-25",
            "department": "Administration",
            "designation": "HR Administrator",
            "role": "HR Admin",
            "employment_type": "Permanent",
            "date_of_joining": "2020-11-05",
            "reporting_to": "EMP1004",
            "status": "Active",
        },
        {
            "employee_id": "EMP1006",
            "name": "Arun Joshi",
            "email": "accountant@iiitdmj.ac.in",
            "phone": "9876543215",
            "gender": "Male",
            "dob": "1985-12-18",
            "department": "Finance",
            "designation": "Accountant",
            "role": "Accountant",
            "employment_type": "Permanent",
            "date_of_joining": "2019-08-12",
            "reporting_to": "EMP1004",
            "status": "Active",
        },
    ]

    users = [
        {"linked_employee_id": "EMP1001", "username": "rahul1001", "password": "rahul123"},
        {"linked_employee_id": "EMP1007", "username": "anjali1007", "password": "anjali123"},
        {"linked_employee_id": "EMP1002", "username": "hod1002", "password": "hod123"},
        {"linked_employee_id": "EMP1003", "username": "director1003", "password": "director123"},
        {"linked_employee_id": "EMP1004", "username": "registrar1004", "password": "registrar123"},
        {"linked_employee_id": "EMP1005", "username": "hradmin1005", "password": "hradmin123"},
        {"linked_employee_id": "EMP1006", "username": "accountant1006", "password": "accountant123"},
    ]

    leave_balance = {
        "employee_id": "EMP1001",
        "casual_leave": 10,
        "restricted_leave": 5,
        "medical_leave": 12,
        "earned_leave": 18,
        "vacation_leave": 20,
        "sabbatical_leave": 0,
    }

    leave_request = {
        "employee_id": "EMP1001",
        "employee_name": "Rahul Sharma",
        "department": "Computer Science and Engineering",
        "designation": "Assistant Professor",
        "leave_type": "Casual",
        "start_date": "2026-04-10",
        "end_date": "2026-04-12",
        "total_days": 3,
        "reason": "Personal work",
        "contact_during_leave": "9876543210",
        "address_during_leave": "Jabalpur, MP",
        "handover_notes": "Classes handed over to Dr. X",
        "attachment_file": "",
        "leave_balance_before": 10,
        "leave_balance_after": 7,
        "approval_status": "PENDING",
        "current_approver_role": "HOD",
        "remarks": "",
    }

    appraisal_request = {
        "employee_id": "EMP1001",
        "employee_name": "Rahul Sharma",
        "department": "Computer Science and Engineering",
        "designation": "Assistant Professor",
        "appraisal_year": "2025-2026",
        "self_summary": "Completed teaching and research responsibilities effectively.",
        "teaching_performance": "Good",
        "research_work": "Worked on 2 projects",
        "publications": "1 journal paper",
        "trainings_attended": "AI workshop",
        "administrative_contributions": "Exam coordination",
        "goals_achieved": "Completed syllabus and guided students",
        "future_goals": "Publish more papers",
        "reviewer_id": "EMP1002",
        "status": "PENDING",
        "remarks": "",
    }

    ltc_request = {
        "employee_id": "EMP1001",
        "employee_name": "Rahul Sharma",
        "department": "Computer Science and Engineering",
        "designation": "Assistant Professor",
        "ltc_block_year": "2024-2027",
        "travel_start_date": "2026-05-05",
        "travel_end_date": "2026-05-12",
        "destination": "Delhi",
        "purpose_of_travel": "Family travel",
        "family_members": [{"name": "Priya Sharma", "relationship": "Spouse"}],
        "travel_mode": "Train",
        "ticket_number": "IRCTC12345",
        "ticket_cost": 12000,
        "accommodation_cost": 8000,
        "other_expenses": 2000,
        "total_amount_claimed": 22000,
        "tickets_upload": "",
        "bills_upload": "",
        "previous_ltc_used": True,
        "last_ltc_date": "2023-06-15",
        "verified_by_hr": False,
        "approval_status": "PENDING",
        "accountant_status": "Not Started",
        "remarks": "",
    }

    cpda_request = {
        "employee_id": "EMP1001",
        "employee_name": "Rahul Sharma",
        "department": "Computer Science and Engineering",
        "designation": "Assistant Professor",
        "event_name": "National Conference on AI",
        "event_type": "Conference",
        "organized_by": "IIT Delhi",
        "venue": "New Delhi",
        "start_date": "2026-06-20",
        "end_date": "2026-06-22",
        "registration_fee": 5000,
        "travel_expense": 8000,
        "accommodation_expense": 6000,
        "other_expenses": 1000,
        "total_amount": 20000,
        "purpose_of_attending": "Present paper and improve research skills",
        "benefits_to_institution": "Research development and academic exposure",
        "invitation_letter": "",
        "receipts": "",
        "certificates": "",
        "verified_by_hr": False,
        "approval_status": "PENDING",
        "accountant_processing_status": "Not Started",
        "remarks": "",
    }

    with transaction.atomic():
        for name in departments:
            DepartmentInfo.objects.get_or_create(name=name)

        teaching_category, _ = EmployeeCategory.objects.get_or_create(
            name="Teaching", defaults={"category_type": "TEACHING"}
        )
        non_teaching_category, _ = EmployeeCategory.objects.get_or_create(
            name="Non-Teaching", defaults={"category_type": "NON_TEACHING"}
        )

        user_lookup = {item["linked_employee_id"]: item for item in users}

        for employee in employees:
            user_info = user_lookup.get(employee["employee_id"], {})
            username = user_info.get("username") or employee["employee_id"].lower()
            first_name, last_name = _split_name(employee["name"])

            user, created = get_user_model().objects.get_or_create(
                username=username,
                defaults={
                    "email": employee["email"],
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )
            if created and user_info.get("password"):
                user.set_password(user_info["password"])
                user.save()

            department_obj = DepartmentInfo.objects.get(name=employee["department"])

            extra_info, _ = ExtraInfo.objects.get_or_create(
                id=employee["employee_id"],
                defaults={
                    "user": user,
                    "sex": _parse_gender(employee["gender"]),
                    "date_of_birth": _parse_date(employee["dob"]),
                    "user_type": "faculty"
                    if employee["department"] == "Computer Science and Engineering"
                    else "staff",
                    "department": department_obj,
                    "phone_no": int(employee["phone"]),
                    "address": "",
                },
            )

            category = teaching_category if extra_info.user_type == "faculty" else non_teaching_category
            EmployeeDetailsExtended.objects.get_or_create(
                extra_info=extra_info,
                defaults={
                    "category": category,
                    "date_of_joining": _parse_date(employee["date_of_joining"]),
                    "appointment_type": employee["employment_type"],
                },
            )

            designation_type = "academic" if extra_info.user_type == "faculty" else "administrative"
            designation, _ = Designation.objects.get_or_create(
                name=employee["designation"],
                defaults={
                    "full_name": employee["designation"],
                    "type": designation_type,
                },
            )

            HoldsDesignation.objects.get_or_create(
                user=user,
                working=user,
                designation=designation,
            )

        leave_types = [
            ("Casual", "CL", leave_balance["casual_leave"]),
            ("Restricted", "RL", leave_balance["restricted_leave"]),
            ("Medical", "ML", leave_balance["medical_leave"]),
            ("Earned", "EL", leave_balance["earned_leave"]),
            ("Vacation", "VL", leave_balance["vacation_leave"]),
            ("Sabbatical", "SL", leave_balance["sabbatical_leave"]),
        ]

        for name, code, _value in leave_types:
            LeaveType.objects.get_or_create(
                name=name,
                code=code,
                defaults={"is_active": True},
            )

        employee_user = ExtraInfo.objects.get(id=leave_balance["employee_id"])
        year = datetime.date.today().year

        for name, code, value in leave_types:
            leave_type = LeaveType.objects.get(code=code)
            EmployeeLeaveBalance.objects.update_or_create(
                employee=employee_user,
                leave_type=leave_type,
                year=year,
                defaults={
                    "opening_balance": value,
                    "accrued": 0,
                    "availed": 0,
                    "current_balance": value,
                },
            )

        LeaveApplicationNew.objects.get_or_create(
            employee=employee_user,
            start_date=_parse_date(leave_request["start_date"]),
            end_date=_parse_date(leave_request["end_date"]),
            defaults={
                "employee_name": leave_request["employee_name"],
                "department": leave_request["department"],
                "designation": leave_request["designation"],
                "leave_type": leave_request["leave_type"],
                "total_days": leave_request["total_days"],
                "reason": leave_request["reason"],
                "contact_during_leave": leave_request["contact_during_leave"],
                "address_during_leave": leave_request["address_during_leave"],
                "handover_to": "Dr. X",
                "handover_notes": leave_request["handover_notes"],
                "medical_certificate": "",
                "attachment_file": leave_request["attachment_file"],
                "leave_balance_before": leave_request["leave_balance_before"],
                "leave_balance_after": leave_request["leave_balance_after"],
                "approval_status": leave_request["approval_status"],
                "current_approver_role": leave_request["current_approver_role"],
                "remarks": leave_request["remarks"],
            },
        )

        AppraisalFormNew.objects.get_or_create(
            employee=employee_user,
            appraisal_year=appraisal_request["appraisal_year"],
            defaults={
                "employee_name": appraisal_request["employee_name"],
                "department": appraisal_request["department"],
                "designation": appraisal_request["designation"],
                "self_summary": appraisal_request["self_summary"],
                "key_responsibilities": "Teaching, research, and academic mentoring.",
                "achievements": appraisal_request["goals_achieved"],
                "challenges_faced": "",
                "teaching_performance": appraisal_request["teaching_performance"],
                "research_work": appraisal_request["research_work"],
                "publications": appraisal_request["publications"],
                "projects_handled": "",
                "administrative_contributions": appraisal_request["administrative_contributions"],
                "trainings_attended": appraisal_request["trainings_attended"],
                "certifications": "",
                "workshops": "",
                "goals_achieved": appraisal_request["goals_achieved"],
                "future_goals": appraisal_request["future_goals"],
                "supporting_documents": "",
                "reviewer_id": appraisal_request["reviewer_id"],
                "reviewer_comments": "",
                "rating": "",
                "status": appraisal_request["status"],
                "remarks": appraisal_request["remarks"],
            },
        )

        block_year = int(ltc_request["ltc_block_year"].split("-")[0])
        LTCApplicationNew.objects.get_or_create(
            employee=employee_user,
            travel_start_date=_parse_date(ltc_request["travel_start_date"]),
            travel_end_date=_parse_date(ltc_request["travel_end_date"]),
            defaults={
                "employee_name": ltc_request["employee_name"],
                "department": ltc_request["department"],
                "designation": ltc_request["designation"],
                "ltc_block_year": block_year,
                "destination": ltc_request["destination"],
                "purpose_of_travel": ltc_request["purpose_of_travel"],
                "family_members": json.dumps(ltc_request["family_members"]),
                "relationship_details": "Spouse",
                "travel_mode": ltc_request["travel_mode"],
                "ticket_number": ltc_request["ticket_number"],
                "ticket_cost": ltc_request["ticket_cost"],
                "accommodation_cost": ltc_request["accommodation_cost"],
                "other_expenses": ltc_request["other_expenses"],
                "total_amount_claimed": ltc_request["total_amount_claimed"],
                "tickets_upload": ltc_request["tickets_upload"],
                "bills_upload": ltc_request["bills_upload"],
                "previous_ltc_used": ltc_request["previous_ltc_used"],
                "last_ltc_date": _parse_date(ltc_request["last_ltc_date"]),
                "verified_by_hr": ltc_request["verified_by_hr"],
                "approval_status": ltc_request["approval_status"],
                "accountant_status": ltc_request["accountant_status"],
                "remarks": ltc_request["remarks"],
            },
        )

        CPDAAdvanceNew.objects.get_or_create(
            employee=employee_user,
            start_date=_parse_date(cpda_request["start_date"]),
            end_date=_parse_date(cpda_request["end_date"]),
            defaults={
                "employee_name": cpda_request["employee_name"],
                "department": cpda_request["department"],
                "designation": cpda_request["designation"],
                "event_name": cpda_request["event_name"],
                "event_type": cpda_request["event_type"],
                "organized_by": cpda_request["organized_by"],
                "venue": cpda_request["venue"],
                "registration_fee": cpda_request["registration_fee"],
                "travel_expense": cpda_request["travel_expense"],
                "accommodation_expense": cpda_request["accommodation_expense"],
                "other_expenses": cpda_request["other_expenses"],
                "total_amount": cpda_request["total_amount"],
                "purpose_of_attending": cpda_request["purpose_of_attending"],
                "benefits_to_institution": cpda_request["benefits_to_institution"],
                "invitation_letter": cpda_request["invitation_letter"],
                "receipts": cpda_request["receipts"],
                "certificates": cpda_request["certificates"],
                "verified_by_hr": cpda_request["verified_by_hr"],
                "approval_status": cpda_request["approval_status"],
                "accountant_processing_status": cpda_request["accountant_processing_status"],
                "remarks": cpda_request["remarks"],
            },
        )

    return {"employees_seeded": len(employees)}


def seed_hr2_demo_data():
    User = get_user_model()
    now = timezone.now()

    department, _ = DepartmentInfo.objects.get_or_create(name="Computer Science")

    designation, _ = Designation.objects.get_or_create(
        name="Faculty",
        defaults={"full_name": "Faculty", "type": "academic"},
    )

    module_access, _ = ModuleAccess.objects.get_or_create(designation="Faculty")
    if not module_access.hr:
        module_access.hr = True
        module_access.save()

    user, created = User.objects.get_or_create(
        username="rahul123",
        defaults={
            "first_name": "Rahul",
            "last_name": "Sharma",
            "email": "rahul.sharma@iiitdmj.ac.in",
        },
    )
    if created:
        user.set_password("user@123")
        user.save()
    else:
        user.email = "rahul.sharma@iiitdmj.ac.in"
        user.first_name = user.first_name or "Rahul"
        user.last_name = user.last_name or "Sharma"
        user.set_password("user@123")
        user.save()

    extra_info, _ = ExtraInfo.objects.get_or_create(
        id="EMP001",
        defaults={
            "user": user,
            "title": "Dr.",
            "sex": "M",
            "date_of_birth": "1990-05-12",
            "user_status": "PRESENT",
            "address": "IIITDMJ Campus",
            "phone_no": 9876543210,
            "user_type": "faculty",
            "department": department,
            "about_me": "Faculty member",
            "last_selected_role": "Faculty",
        },
    )
    if extra_info.user_id != user.id:
        extra_info.user = user
    extra_info.department = department
    extra_info.phone_no = 9876543210
    extra_info.last_selected_role = "Faculty"
    extra_info.save()

    HoldsDesignation.objects.get_or_create(
        user=user,
        working=user,
        designation=designation,
    )

    Employee.objects.get_or_create(
        id=user,
        defaults={
            "father_name": "Rajesh Sharma",
            "mother_name": "Sunita Sharma",
            "category": "General",
            "caste": "N/A",
            "home_state": "Madhya Pradesh",
            "home_district": "Jabalpur",
            "full_address": "IIITDMJ Campus, Dumna Airport Road",
            "date_of_joining": "2021-08-01",
            "date_of_birth": "1990-05-12",
            "blood_group": "O+",
            "phone_number": "9876543210",
            "personal_email": "rahul.sharma@iiitdmj.ac.in",
            "emergency_contact_number": "9876543211",
            "emergency_contact_name": "Rajesh Sharma",
            "employee_type": "Faculty",
        },
    )

    leave_type_map = {
        "Casual": ("CL", Decimal("10")),
        "Earned": ("EL", Decimal("18")),
        "Medical": ("ML", Decimal("12")),
        "Restricted": ("RL", Decimal("5")),
        "Vacation": ("VL", Decimal("25")),
        "Sabbatical": ("SL", Decimal("0")),
    }

    current_year = now.year
    for name, (code, balance) in leave_type_map.items():
        leave_type, _ = LeaveType.objects.get_or_create(
            name=name,
            defaults={"code": code, "is_active": True},
        )
        EmployeeLeaveBalance.objects.get_or_create(
            employee=extra_info,
            leave_type=leave_type,
            year=current_year,
            defaults={
                "opening_balance": balance,
                "accrued": Decimal("0"),
                "availed": Decimal("0"),
                "current_balance": balance,
            },
        )

    if notify:
        notify.send(
            sender=user,
            recipient=user,
            verb="Welcome to HR Portal",
            description="Welcome to HR Portal",
        )

    return {"employee_id": extra_info.id}


def convert_vl_to_earned(source_year=None, dry_run=False):
    if source_year is None:
        source_year = datetime.date.today().year
    target_year = source_year + 1

    vl_type = LeaveType.objects.filter(code__iexact="VL").first() or LeaveType.objects.filter(name__iexact="Vacation").first()
    el_type = LeaveType.objects.filter(code__iexact="EL").first() or LeaveType.objects.filter(name__iexact="Earned").first()

    if not vl_type or not el_type:
        raise CommandError("Leave types VL/Earned not found. Ensure LeaveType records exist.")

    all_employees = ExtraInfo.objects.all()
    converted_count = 0
    total_converted = Decimal("0.0")

    next_year_defaults = {
        "CL": Decimal("8.0"),
        "RL": Decimal("2.0"),
        "VL": Decimal("60.0"),
    }
    leave_types = {lt.code.upper(): lt for lt in LeaveType.objects.all() if lt.code}

    for employee in all_employees:
        is_faculty = employee.user_type == "faculty"
        converted = Decimal("0.0")

        vl_balance = EmployeeLeaveBalance.objects.filter(
            employee=employee,
            leave_type=vl_type,
            year=source_year,
        ).first()
        if is_faculty and vl_balance:
            vl_current = Decimal(str(vl_balance.current_balance or 0))
            if vl_current > 0:
                converted = (vl_current / Decimal("2")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
                if not dry_run:
                    vl_balance.current_balance = Decimal("0.0")
                    vl_balance.save(update_fields=["current_balance"])
                if converted > 0:
                    converted_count += 1
                    total_converted += converted

        if dry_run:
            continue

        for code, leave_type in leave_types.items():
            if code == "EL":
                opening = Decimal("0.0")
                accrued = converted
                current = converted
            elif code in next_year_defaults:
                opening = next_year_defaults[code]
                accrued = Decimal("0.0")
                current = opening
            else:
                opening = Decimal("0.0")
                accrued = Decimal("0.0")
                current = Decimal("0.0")

            EmployeeLeaveBalance.objects.update_or_create(
                employee=employee,
                leave_type=leave_type,
                year=target_year,
                defaults={
                    "opening_balance": opening,
                    "accrued": accrued,
                    "availed": Decimal("0.0"),
                    "current_balance": current,
                },
            )

    return {
        "dry_run": dry_run,
        "converted_count": converted_count,
        "total_converted": total_converted,
        "source_year": source_year,
        "target_year": target_year,
    }