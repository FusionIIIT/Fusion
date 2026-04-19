from datetime import date
from django.db.models import Q
from applications.globals.models import ExtraInfo, HoldsDesignation
from .models import (
    EmployeeLeaveBalance, LeaveApplicationNew, EmployeeAttendance, FacultyWorkload, 
    PerformanceAppraisalNew, AppraisalPeriod, TrainingProgram, TrainingNomination, 
    PromotionApplication, LTCApplicationNew, CPDAAdvanceNew, CPDAReimbursementNew, 
    AppraisalFormNew
)

# ==================== EMPLOYEE SELECTORS ====================

def get_employee_by_id(employee_id):
    return ExtraInfo.objects.select_related('user', 'department').get(id=employee_id)

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

# ==================== LEAVE SELECTORS ====================

def get_leave_balance_for_employee(employee_extra_info, leave_type, year=None):
    if year is None:
        year = date.today().year
    return EmployeeLeaveBalance.objects.select_related('leave_type').get(
        employee=employee_extra_info,
        leave_type=leave_type,
        year=year
    )

def get_leave_applications(employee_extra_info, status=None, from_date=None, to_date=None):
    qs = LeaveApplicationNew.objects.filter(employee=employee_extra_info)
    if status:
        qs = qs.filter(approval_status=status)
    if from_date:
        qs = qs.filter(start_date__gte=from_date)
    if to_date:
        qs = qs.filter(end_date__lte=to_date)
    return qs.order_by('-applied_date')

def get_pending_responsibility_leaves(employee_extra_info, responsibility_type='academic'):
    if responsibility_type == 'academic':
        return LeaveApplicationNew.objects.filter(employee=employee_extra_info, approval_status='PENDING')
    return LeaveApplicationNew.objects.filter(employee=employee_extra_info, approval_status='PENDING')

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

# CPDA Advance
def get_cpda_advances(employee_extra_info, status=None):
    qs = CPDAAdvanceNew.objects.filter(employee=employee_extra_info)
    if status:
        qs = qs.filter(approval_status=status)
    return qs.order_by('-applied_date')

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