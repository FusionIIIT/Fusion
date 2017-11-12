from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.forms.formsets import formset_factory
from applications.leave.models import (LeaveType, Leave, ReplacementSegment,
                                       LeaveSegment, LeavesCount, LeaveRequest,
                                       LeaveMigration)
from applications.leave.forms import (EmployeeCommonForm, LeaveSegmentForm, StationLeaveForm,
                                      AdminReplacementForm, AcademicReplacementForm,
                                      BaseLeaveFormSet)


@login_required(login_url='/accounts/login')
def leave(request):

    leave_form_set = formset_factory(LeaveSegmentForm, formset=BaseLeaveFormSet)
    acad_form_set = formset_factory(AcademicReplacementForm)(form_kwargs={'user': request.user})
    admin_form_set = formset_factory(AdminReplacementForm)(form_kwargs={'user': request.user})

    context = {}
    return render(request, "leaveModule/leave.html", context)
