from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.forms.formsets import formset_factory
from applications.leave.models import (LeaveType, Leave, ReplacementSegment,
                                       LeaveSegment, LeavesCount, LeaveRequest,
                                       LeaveMigration)
from applications.leave.forms import (EmployeeCommonForm, LeaveSegmentForm,
                                      AdminReplacementForm, AcademicReplacementForm,
                                      BaseLeaveFormSet)


@login_required(login_url='/accounts/login')
def leave(request):

    LeaveFormSet = formset_factory(LeaveSegmentForm, formset=BaseLeaveFormSet)
    AcadFormSet = formset_factory(AcademicReplacementForm)# (form_kwargs={'user': request.user})
    AdminFormSet = formset_factory(AdminReplacementForm)# (form_kwargs={'user': request.user})
    common_form = EmployeeCommonForm()

    context = {}

    user_type = request.user.extrainfo.user_type

    if request.method == 'POST':
        kwargs = {'user' : request.user}
        kwargs.update(request.POST)
        leave_form_set = LeaveFormSet(kwargs)
        academic_form_set = AcadFormSet(kwargs)
        admin_form_set = AdminFormSet(kwargs)
        common_form = EmployeeCommonForm(request.POST)

        if leave_form_set.is_valid() and academic_form_set.is_valid() \
            and admin_form_set.is_valid() and common_form.is_valid():

            pass

    else:
        context = {
            'leave_form_set': LeaveFormSet(initial={}),
            'acad_form_set': AcadFormSet(form_kwargs={'user': request.user}),
            'admin_form_set': AdminFormSet(form_kwargs={'user': request.user}),
            'common_form': common_form,
        }

        if user_type == 'staff':
            context.update()


    return render(request, "leaveModule/leave.html", context)
