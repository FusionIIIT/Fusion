from django.shortcuts import render

from applications.leave.models import (LeaveType, Leave, ReplacementSegment,
                                       LeaveSegment, LeavesCount, LeaveRequest,
                                       LeaveMigration)
from applications.leave.forms import (EmployeeCommonForm, LeaveSegmentForm,
                                      AdminReplacementForm, AcademicReplacementForm,
                                      BaseLeaveFormSet)


def handle_faculty_leave_application(request):
    pass


def handle_staff_leave_application(request):
    pass


def handle_student_leave_application(request):
    pass
