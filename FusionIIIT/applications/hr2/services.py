"""
HR2 Module Services - Stub Implementation

This is a stub implementation that allows the module to import without errors.
Full implementations will use actual Django models from models.py.
"""

from datetime import date
from django.core.exceptions import ValidationError

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