from django.shortcuts import render
from django.contrib import messages
from django.forms.formsets import formset_factory
from applications.leave.models import (LeaveType, Leave, ReplacementSegment,
                                       LeaveSegment, LeavesCount, LeaveRequest,
                                       LeaveMigration)
from applications.leave.forms import (EmployeeCommonForm, LeaveSegmentForm,
                                      AdminReplacementForm, AcademicReplacementForm,
                                      BaseLeaveFormSet)


LeaveFormSet = formset_factory(LeaveSegmentForm, extra=0, max_num=3, min_num=1,
                               formset=BaseLeaveFormSet)
AcadFormSet = formset_factory(AcademicReplacementForm, extra=0, max_num=3, min_num=1)
AdminFormSet = formset_factory(AdminReplacementForm, extra=0, max_num=3, min_num=1)
common_form = EmployeeCommonForm()


def handle_faculty_leave_application(request):
    leave_form_set = LeaveFormSet(request.POST, request.FILES, prefix='leave_form',
                                  user=request.user)
    academic_form_set = AcadFormSet(request.POST, prefix='acad_form',
                                    form_kwargs={'user': request.user})
    admin_form_set = AdminFormSet(request.POST, prefix='admin_form',
                                  form_kwargs={'user': request.user})
    common_form = EmployeeCommonForm(request.POST)

    if leave_form_set.is_valid() and academic_form_set.is_valid() and \
       admin_form_set.is_valid() and common_form.is_valid():

        # TODO: Remove this pass
        messages.add_message(request, messages.SUCCESS, 'Successfully Submitted !')
        return redirect(reverse('leave:leave'))
        leave = Leave(
            applicant=request.user
        )
        segments = list()
        type_of_leaves = LeaveType.objects.all()
        replacements = list()

        for form in leave_form_set:
            data = form.cleaned_data
            leave_type = type_of_leaves.get(id=data.get('leave_type'))
            leave_segment = LeaveSegment(
                leave=leave,
                leave_type=leave_type,
                start_date=data.get('start_date'),
                end_date=data.get('end_date'),
                start_half=data.get('start_half'),
                end_half=data.get('end_half'),
                document=data.get('document')
            )
            segments.append(leave_segment)

        for form in acad_form_set:
            data = form.cleaned_data
            rep_user = User.objects.get(username=data.get('acad_rep'))
            rep = ReplacementSegment(
                leave=leave,
                replacer=rep_user,
                replacement_type='academic'
            )
            replacements.append(rep)

        for form in admin_form_set:
            data = form.cleaned_data
            rep_user = User.objects.get(username=data.get('admin_rep'))
            rep = ReplacementSegment(
                leave=leave,
                replacer=rep_user,
                replacement_type='administrative'
            )
            replacements.append(rep)

        data = common_form.cleaned_data
        leave.purpose = data.get('purpose')
        leave.is_station = data.get('is_station')
        leave.save()
        LeaveSegment.objects.bulk_create(segments)
        ReplacementSegment.objects.bulk_create(replacements)

        messages.add_message(request, messages.SUCCESS, 'Successfully Submitted !')
        return redirect(reverse('leave:leave'))

    context = {
        'leave_form_set': leave_form_set,
        'acad_form_set': academic_form_set,
        'admin_form_set': admin_form_set,
        'common_form': common_form,
        'forms': True,
    }

    return render(request, 'leaveModule/leave.html', context)

    context = {
        'leave_form_set': leave_form_set,
        'acad_form_set': acad_form_set,
        'admin_form_set': admin_form_set,
        'common_form': common_form,
    }

    return render(request, 'leaveModule/leave.html', context)


def handle_staff_leave_application(request):
    leave_form_set = LeaveFormSet(request.POST, prefix='leave_form', user=request.user)
    admin_form_set = AdminFormSet(request.POST, prefix='admin_form',
                                  form_kwargs={'user': request.user})
    common_form = EmployeeCommonForm(request.POST)

    if leave_form_set.is_valid() and \
       admin_form_set.is_valid() and common_form.is_valid():

        pass


def handle_student_leave_application(request):
    pass


def send_faculty_leave_form(request):
    context = {
        'leave_form_set': LeaveFormSet(prefix='leave_form', user=request.user),
        'acad_form_set': AcadFormSet(prefix='acad_form', form_kwargs={'user': request.user}),
        'admin_form_set': AdminFormSet(prefix='admin_form', form_kwargs={'user': request.user}),
        'common_form': common_form,
        'forms': True,
    }

    return render(request, 'leaveModule/leave.html', context)


def send_staff_leave_form(request):
    context = {
        'leave_form_set': LeaveFormSet(prefix='leave_form', user=request.user),
        'acad_form_set': None,
        'admin_form_set': AdminFormSet(prefix='admin_form', form_kwargs={'user': request.user}),
        'common_form': common_form,
        'forms': True
    }

    return render(request, 'leaveModule/leave.html', context)


def send_student_leave_form(request):
    pass
