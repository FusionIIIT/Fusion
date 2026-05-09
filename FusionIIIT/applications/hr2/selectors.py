from datetime import date

from django.db.models import Q
from django.http import Http404

from applications.globals.models import ExtraInfo, HoldsDesignation
from .models import (
    AppraisalFormNew,
    AppraisalPeriod,
    CPDAAdvanceNew,
    CPDAReimbursementNew,
    EmployeeAttendance,
    EmployeeLeaveBalance,
    FacultyWorkload,
    LeaveApplicationNew,
    LeaveType,
    LTCApplicationNew,
    PerformanceAppraisalNew,
    PromotionApplication,
    TrainingNomination,
    TrainingProgram,
)

# ==================== EMPLOYEE SELECTORS ====================

def get_employee_by_id(employee_id):
    return ExtraInfo.objects.select_related('user', 'department').get(id=employee_id)


def get_employee_by_id_optional(employee_id):
    if not employee_id:
        return None
    return ExtraInfo.objects.filter(id=employee_id).select_related('user', 'department').first()


def get_employee_by_id_or_404(employee_id):
    try:
        return get_employee_by_id(employee_id)
    except ExtraInfo.DoesNotExist as exc:
        raise Http404(f"Employee not found: {employee_id}") from exc

def get_all_employees(employee_type=None, department_id=None):
    qs = ExtraInfo.objects.select_related('user', 'department')
    if employee_type:
        qs = qs.filter(user_type=employee_type)
    if department_id:
        qs = qs.filter(department_id=department_id)
    return qs

def get_employee_current_designation(employee_extra_info):
    held = HoldsDesignation.objects.filter(working=employee_extra_info).order_by('-held_at').first()
    return held.designation if held else None


def get_employee_current_designation_for_user(user):
    held = HoldsDesignation.objects.filter(working=user).order_by('-held_at').first()
    return held.designation if held else None


def get_employee_for_user(user):
    return ExtraInfo.objects.filter(user=user).select_related('user', 'department').first()


def get_leave_application_by_id_or_404(pk):
    try:
        return LeaveApplicationNew.objects.get(pk=pk)
    except LeaveApplicationNew.DoesNotExist as exc:
        raise Http404("Leave application not found") from exc


def get_ltc_application_by_id_or_404(pk):
    try:
        return LTCApplicationNew.objects.get(pk=pk)
    except LTCApplicationNew.DoesNotExist as exc:
        raise Http404("LTC application not found") from exc


def get_cpda_advance_by_id_or_404(pk):
    try:
        return CPDAAdvanceNew.objects.get(pk=pk)
    except CPDAAdvanceNew.DoesNotExist as exc:
        raise Http404("CPDA advance not found") from exc


def get_cpda_reimbursement_by_id_or_404(pk):
    try:
        return CPDAReimbursementNew.objects.get(pk=pk)
    except CPDAReimbursementNew.DoesNotExist as exc:
        raise Http404("CPDA reimbursement not found") from exc


def get_appraisal_form_by_id_or_404(pk):
    try:
        return AppraisalFormNew.objects.get(pk=pk)
    except AppraisalFormNew.DoesNotExist as exc:
        raise Http404("Appraisal form not found") from exc

# ==================== LEAVE SELECTORS ====================

def get_leave_balance_for_employee(employee_extra_info, leave_type, year=None):
    if year is None:
        year = date.today().year
    return EmployeeLeaveBalance.objects.select_related('leave_type').get(
        employee=employee_extra_info,
        leave_type=leave_type,
        year=year
    )


def get_leave_type_by_name(leave_type_name):
    return LeaveType.objects.filter(name__iexact=leave_type_name).first()


def get_leave_balances_for_employee(employee):
    return (
        EmployeeLeaveBalance.objects.filter(employee=employee)
        .select_related('leave_type')
        .order_by('leave_type_id', '-year', '-id')
    )


def get_latest_leave_balances_for_employee(employee):
    balances = []
    seen_leave_types = set()
    for balance in get_leave_balances_for_employee(employee):
        if balance.leave_type_id in seen_leave_types:
            continue
        seen_leave_types.add(balance.leave_type_id)
        balances.append(balance)
    return balances


def get_leave_balance_for_employee_year(employee, leave_type, year):
    return EmployeeLeaveBalance.objects.filter(
        employee=employee,
        leave_type=leave_type,
        year=year,
    ).first()


def get_latest_leave_balance_for_employee(employee, leave_type):
    return EmployeeLeaveBalance.objects.filter(
        employee=employee,
        leave_type=leave_type,
    ).order_by('-year').first()


def has_overlapping_leave(employee, start_date, end_date, exclude_id=None):
    qs = LeaveApplicationNew.objects.filter(
        employee=employee,
        approval_status__in=['PENDING', 'FORWARDED', 'APPROVED'],
        start_date__lte=end_date,
        end_date__gte=start_date,
    )
    if exclude_id is not None:
        qs = qs.exclude(id=exclude_id)
    return qs


def get_leave_applications_for_nominee(employee_id):
    return LeaveApplicationNew.objects.filter(
        handover_to=employee_id,
        nominee_status='PENDING',
    ).order_by('-applied_date')

def get_leave_applications(employee_extra_info, status=None, from_date=None, to_date=None):
    qs = LeaveApplicationNew.objects.filter(employee=employee_extra_info)
    if status:
        qs = qs.filter(approval_status=status)
    if from_date:
        qs = qs.filter(start_date__gte=from_date)
    if to_date:
        qs = qs.filter(end_date__lte=to_date)
    return qs.order_by('-applied_date')


def get_leave_applications_for_role_view(user, role_flags):
    if role_flags.get('is_hr_staff'):
        return LeaveApplicationNew.objects.all()
    if role_flags.get('is_director'):
        return LeaveApplicationNew.objects.filter(
            Q(
                approval_status='FORWARDED',
                current_approver_role__iexact='Director',
            )
            | Q(employee=user.extrainfo)
            | Q(
                cancel_status='REQUESTED',
                cancel_current_approver_role__iexact='Director',
            )
            | Q(
                extension_status='REQUESTED',
                extension_current_approver_role__iexact='Director',
            )
        )
    if role_flags.get('is_registrar'):
        return LeaveApplicationNew.objects.filter(
            Q(
                approval_status='FORWARDED',
                current_approver_role__iexact='Registrar',
            )
            | Q(employee=user.extrainfo)
            | Q(
                cancel_status='REQUESTED',
                cancel_current_approver_role__iexact='Registrar',
            )
            | Q(
                extension_status='REQUESTED',
                extension_current_approver_role__iexact='Registrar',
            )
        )
    if role_flags.get('is_hod'):
        return LeaveApplicationNew.objects.filter(
            department=user.extrainfo.department.name
        )
    return get_leave_applications(user.extrainfo)

def get_pending_responsibility_leaves(employee_extra_info, responsibility_type='academic'):
    if responsibility_type == 'academic':
        return LeaveApplicationNew.objects.filter(employee=employee_extra_info, approval_status='PENDING')
    return LeaveApplicationNew.objects.filter(employee=employee_extra_info, approval_status='PENDING')


def get_leave_applications_for_employee_and_status(employee_extra_info, status=None):
    qs = LeaveApplicationNew.objects.filter(employee=employee_extra_info)
    if status:
        qs = qs.filter(approval_status=status)
    return qs.order_by('-applied_date')

# ==================== ATTENDANCE SELECTORS ====================

def get_attendance_for_employee(employee_extra_info, from_date=None, to_date=None):
    qs = EmployeeAttendance.objects.filter(employee=employee_extra_info)
    if from_date:
        qs = qs.filter(date__gte=from_date)
    if to_date:
        qs = qs.filter(date__lte=to_date)
    return qs.order_by('date')

# ==================== APPRAISAL SELECTORS ====================

def get_appraisal_periods(is_active=None):
    qs = AppraisalPeriod.objects.all()
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    return qs


def get_appraisal_forms_for_role_view(user, role_flags):
    if role_flags.get('is_hr_staff'):
        return AppraisalFormNew.objects.all().order_by('-submitted_at')
    if role_flags.get('is_director'):
        return AppraisalFormNew.objects.filter(
            assigned_reviewer_role__iexact='DIRECTOR',
        ).filter(
            Q(assigned_reviewer__isnull=True)
            | Q(assigned_reviewer=user.extrainfo)
        ).filter(
            status__in=['PENDING', 'REVIEWED']
        ).order_by('-submitted_at')
    if role_flags.get('is_hod'):
        return AppraisalFormNew.objects.filter(
            assigned_reviewer_role__iexact='HOD',
            department=user.extrainfo.department.name,
        ).filter(
            Q(assigned_reviewer__isnull=True)
            | Q(assigned_reviewer=user.extrainfo)
        ).filter(
            status='PENDING'
        ).order_by('-submitted_at')
    return get_appraisal_forms(user.extrainfo)

def get_appraisals_for_employee(employee_extra_info, period_id=None):
    qs = PerformanceAppraisalNew.objects.filter(employee=employee_extra_info).select_related('period')
    if period_id:
        qs = qs.filter(period_id=period_id)
    return qs

# ==================== TRAINING SELECTORS ====================

def get_available_training_programs():
    today = date.today()
    return TrainingProgram.objects.filter(start_date__gte=today)

def get_nominations_for_employee(employee_extra_info):
    return TrainingNomination.objects.filter(employee=employee_extra_info).select_related('program')

# ==================== PROMOTION SELECTORS ====================

def get_promotion_applications(employee_extra_info=None):
    qs = PromotionApplication.objects.select_related('employee', 'current_designation', 'applied_designation')
    if employee_extra_info:
        qs = qs.filter(employee=employee_extra_info)
    return qs

# ==================== FACULTY WORKLOAD SELECTORS ====================

def get_faculty_workload(faculty_extra_info, semester=None, year=None):
    qs = FacultyWorkload.objects.filter(faculty=faculty_extra_info.faculty_profile)
    if semester:
        qs = qs.filter(semester=semester)
    if year:
        qs = qs.filter(year=year)
    return qs

# LTC
def get_ltc_applications(employee_extra_info, status=None):
    qs = LTCApplicationNew.objects.filter(employee=employee_extra_info)
    if status:
        qs = qs.filter(approval_status=status)
    return qs.order_by('-applied_date')


def get_ltc_applications_for_role_view(user, role_flags):
    if role_flags.get('is_hr_staff'):
        return LTCApplicationNew.objects.filter(approval_status__in=['PENDING', 'FORWARDED'])
    if role_flags.get('is_accountant'):
        return LTCApplicationNew.objects.filter(
            approval_status='FORWARDED',
            accountant_status__iexact='PENDING',
        )
    return get_ltc_applications(user.extrainfo)

# CPDA Advance
def get_cpda_advances(employee_extra_info, status=None):
    qs = CPDAAdvanceNew.objects.filter(employee=employee_extra_info)
    if status:
        qs = qs.filter(approval_status=status)
    return qs.order_by('-applied_date')


def get_cpda_advances_for_role_view(user, role_flags):
    if role_flags.get('is_director'):
        return CPDAAdvanceNew.objects.filter(
            approval_status='FORWARDED',
            accountant_processing_status__iexact='DIRECTOR_REVIEW',
        )
    if role_flags.get('is_hr_staff'):
        return CPDAAdvanceNew.objects.filter(approval_status='PENDING')
    if role_flags.get('is_accountant'):
        return CPDAAdvanceNew.objects.filter(
            approval_status='FORWARDED',
            accountant_processing_status__in=['PENDING'],
        )
    return get_cpda_advances(user.extrainfo)

# CPDA Reimbursement
def get_cpda_reimbursements(employee_extra_info, status=None):
    qs = CPDAReimbursementNew.objects.filter(employee=employee_extra_info)
    if status:
        qs = qs.filter(approval_status=status)
    return qs.order_by('-applied_date')

# Appraisal Form
def get_appraisal_forms(employee_extra_info, status=None):
    qs = AppraisalFormNew.objects.filter(employee=employee_extra_info)
    if status:
        qs = qs.filter(status=status)
    return qs.order_by('-submitted_at')


def get_reviewer_by_id(reviewer_id):
    if not reviewer_id:
        return None
    return ExtraInfo.objects.filter(id=reviewer_id).first()


def get_role_flags(user):
    return {
        'is_hr_staff': HoldsDesignation.objects.filter(
            working=user,
            designation__name__icontains='hr',
        ).exists() or (
            hasattr(user, 'extrainfo')
            and user.extrainfo.user_type == 'staff'
            and user.extrainfo.department
            and user.extrainfo.department.name == 'HR'
        ),
        'is_hod': HoldsDesignation.objects.filter(
            working=user,
            designation__name__icontains='hod',
        ).exists(),
        'is_director': HoldsDesignation.objects.filter(
            working=user,
            designation__name__icontains='director',
        ).exists(),
        'is_registrar': HoldsDesignation.objects.filter(
            working=user,
            designation__name__icontains='registrar',
        ).exists(),
        'is_accountant': HoldsDesignation.objects.filter(
            working=user,
            designation__name__icontains='accountant',
        ).exists(),
        'is_hr_admin': HoldsDesignation.objects.filter(
            working=user,
            designation__name__iregex=r'hr admin|hr administrator',
        ).exists(),
    }