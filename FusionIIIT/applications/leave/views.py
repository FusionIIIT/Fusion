from django.contrib.auth.decorators import login_required
from django.forms.formsets import formset_factory
from django.shortcuts import render

# from applications.leave.models import (LeaveType, Leave, ReplacementSegment,
#                                        LeaveSegment, LeavesCount, LeaveRequest,
#                                        LeaveMigration)
from applications.leave.forms import (AcademicReplacementForm,
                                      AdminReplacementForm, BaseLeaveFormSet,
                                      EmployeeCommonForm, LeaveSegmentForm)


@login_required(login_url='/accounts/login')
def leave(request):

    LeaveFormSet = formset_factory(LeaveSegmentForm, extra=0, max_num=3, min_num=1,
                                   formset=BaseLeaveFormSet)
    AcadFormSet = formset_factory(AcademicReplacementForm, extra=0, max_num=3, min_num=1)
    AdminFormSet = formset_factory(AdminReplacementForm, extra=0, max_num=3, min_num=1)
    common_form = EmployeeCommonForm()

    context = {}

    user_type = request.user.extrainfo.user_type

    if request.method == 'POST':

        leave_form_set = LeaveFormSet(request.POST, prefix='leave_form')
        academic_form_set = AcadFormSet(request.POST, prefix='acad_form',
                                        form_kwargs={'user': request.user})
        admin_form_set = AdminFormSet(request.POST, prefix='admin_form',
                                      form_kwargs={'user': request.user})
        common_form = EmployeeCommonForm(request.POST)

        if leave_form_set.is_valid() and academic_form_set.is_valid() \
           and admin_form_set.is_valid() and common_form.is_valid():

            print('hey worked')

    else:
        context = {
            'leave_form_set': LeaveFormSet(prefix='leave_form'),
            'acad_form_set': AcadFormSet(prefix='acad_form', form_kwargs={'user': request.user}),
            'admin_form_set': AdminFormSet(prefix='admin_form', form_kwargs={'user': request.user}),
            'common_form': common_form,
        }

        if user_type == 'staff':
            context.update()

    return render(request, "leaveModule/leave.html", context)
