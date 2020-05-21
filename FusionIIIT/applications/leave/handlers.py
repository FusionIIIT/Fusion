from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.forms.formsets import formset_factory
from django.http import JsonResponse
from django.shortcuts import redirect, render, reverse
from django.core.exceptions import ValidationError
from .forms import (AcademicReplacementForm, AdminReplacementForm,
                    BaseLeaveFormSet, EmployeeCommonForm, LeaveSegmentForm,
                    StudentApplicationForm, AcademicReplacementFormOffline, AdminReplacementFormOffline,
                    BaseLeaveFormSetOffline, EmployeeCommonFormOffline, LeaveSegmentFormOffline )
from .helpers import (create_migrations, deduct_leave_balance,
                      get_pending_leave_requests, restore_leave_balance, get_designation)
from .models import (Leave, LeaveRequest, LeaveSegment,
                     LeaveType, ReplacementSegment, LeaveOffline, LeaveSegmentOffline, ReplacementSegmentOffline)
from applications.globals.models import HoldsDesignation
from notification.views import leave_module_notif
import datetime
from django.utils import timezone

LeaveFormSet = formset_factory(LeaveSegmentForm, extra=0, max_num=3, min_num=1,
                               formset=BaseLeaveFormSet)
AcadFormSet = formset_factory(AcademicReplacementForm, extra=0, max_num=3, min_num=1)
AdminFormSet = formset_factory(AdminReplacementForm, extra=0, max_num=3, min_num=1)
common_form = EmployeeCommonForm()

LeaveFormSetOffline = formset_factory(LeaveSegmentFormOffline,formset=BaseLeaveFormSetOffline, extra=0, max_num=3, min_num=1)
AcadFormSetOffline = formset_factory(AcademicReplacementFormOffline, extra=0, max_num=3, min_num=1)
AdminFormSetOffline = formset_factory(AdminReplacementFormOffline, extra=0, max_num=3, min_num=1)
common_form_offline = EmployeeCommonFormOffline()


def add_leave_segment(form, type_of_leaves):
    data = form.cleaned_data
    leave_type = type_of_leaves.get(id=data.get('leave_type'))
    leave_segment = LeaveSegment(
        leave_type=leave_type,
        start_date=data.get('start_date'),
        end_date=data.get('end_date'),
        start_half=data.get('start_half'),
        end_half=data.get('end_half'),
        document=data.get('document'),
        address=data.get('address') #changed
    )
    return leave_segment


def add_acad_rep_segment(form):
    data = form.cleaned_data
    rep_user = User.objects.get(username=data.get('acad_rep'))
    rep = ReplacementSegment(
        replacer=rep_user,
        replacement_type='academic',
        start_date=data.get('acad_start_date'),
        end_date=data.get('acad_end_date')
    )
    return rep


def add_admin_rep_segment(form):
    data = form.cleaned_data
    rep_user = User.objects.get(username=data.get('admin_rep'))
    rep = ReplacementSegment(
        replacer=rep_user,
        replacement_type='administrative',
        start_date=data.get('admin_start_date'),
        end_date=data.get('admin_end_date')
    )
    return rep


def add_leave_segment_offline(form, type_of_leaves):
    data = form.cleaned_data
    leave_type = type_of_leaves.get(id=data.get('leave_type'))
    leave_segment = LeaveSegmentOffline(
        leave_type=leave_type,
        start_date=data.get('start_date'),
        end_date=data.get('end_date'),
        start_half=data.get('start_half'),
        end_half=data.get('end_half'),
        document=data.get('document'),
        address=data.get('address') #changed
    )
    return leave_segment


def add_acad_rep_segment_offline(form):
    data = form.cleaned_data
    rep_user = User.objects.get(username=data.get('acad_rep'))
    rep = ReplacementSegmentOffline(
        replacer=rep_user,
        replacement_type='academic',
        start_date=data.get('acad_start_date'),
        end_date=data.get('acad_end_date')
    )
    return rep


def add_admin_rep_segment_offline(form):
    data = form.cleaned_data
    rep_user = User.objects.get(username=data.get('admin_rep'))
    rep = ReplacementSegmentOffline(
        replacer=rep_user,
        replacement_type='administrative',
        start_date=data.get('admin_start_date'),
        end_date=data.get('admin_end_date')
    )
    return rep


@transaction.atomic
def handle_faculty_leave_application(request):
    leave_form_set = LeaveFormSet(request.POST, request.FILES, prefix='leave_form',
                                  user=request.user)
    academic_form_set = AcadFormSet(request.POST, prefix='acad_form',
                                    form_kwargs={'user': request.user})
    admin_form_set = AdminFormSet(request.POST, prefix='admin_form',
                                  form_kwargs={'user': request.user})
    common_form = EmployeeCommonForm(request.POST)
    user_designation = get_designation(request.user)

    leave_valid = leave_form_set.is_valid()
    acad_valid = academic_form_set.is_valid()
    admin_valid = admin_form_set.is_valid()
    common_valid = common_form.is_valid()

    if leave_valid and acad_valid and admin_valid and common_valid:
        leave = Leave(
            applicant=request.user
        )
        segments = list()
        type_of_leaves = LeaveType.objects.all()
        replacements = list()

        for form in leave_form_set:
            leave_segment = add_leave_segment(form, type_of_leaves)
            segments.append(leave_segment)

        for form in academic_form_set:
            rep = add_acad_rep_segment(form)
            replacements.append(rep)

        for form in admin_form_set:
            rep = add_admin_rep_segment(form)
            replacements.append(rep)


        data = common_form.cleaned_data
        leave.purpose = data.get('purpose')
        #leave.is_station = data.get('is_station')
        leave.extra_info = data.get('leave_info')
        leave.save()
        rep_req=[]
        for segment in segments:
            segment.leave = leave
        for replacement in replacements:
            replacement.leave = leave
            rep_req.append(replacement.replacer)
        LeaveSegment.objects.bulk_create(segments)
        ReplacementSegment.objects.bulk_create(replacements)
        deduct_leave_balance(leave,False)
        leave_module_notif(request.user, request.user, 'leave_applied')
        leave_module_notif(request.user, rep_req, 'replacement_request')
        messages.add_message(request, messages.SUCCESS, 'Successfully Submitted !')
        return redirect(reverse('leave:leave'))

    rep_segments = request.user.rep_requests.filter(status='pending')
    leave_requests = get_pending_leave_requests(request.user)
    leave_balance = request.user.leave_balance.all()
    user_leave_applications = Leave.objects.filter(applicant=request.user).order_by('-timestamp')
    processed_requests = request.user.all_leave_requests.filter(~Q(status='pending'))
    user_leave_applications_offline = LeaveOffline.objects.filter(applicant=request.user).order_by('-timestamp')
    context = {
        'processed_requests': processed_requests,
        'leave_form_set': leave_form_set,
        'acad_form_set': academic_form_set,
        'admin_form_set': admin_form_set,
        'common_form': common_form,
        'forms': True,
        'rep_segments': rep_segments,
        'leave_balance': leave_balance,
        'leave_requests': leave_requests,
        'designation': user_designation,
        'user_leave_applications': user_leave_applications,
        'user_leave_applications_offline': user_leave_applications_offline
    }

    return render(request, 'leaveModule/leave.html', context)


def handle_staff_leave_application(request):
    leave_form_set = LeaveFormSet(request.POST, request.FILES, prefix='leave_form',
                                  user=request.user)
    admin_form_set = AdminFormSet(request.POST, prefix='admin_form',
                                  form_kwargs={'user': request.user})
    common_form = EmployeeCommonForm(request.POST)
    user_designation = get_designation(request.user)


    leave_valid = leave_form_set.is_valid()
    admin_valid = admin_form_set.is_valid()
    common_valid = common_form.is_valid()

    if leave_valid and admin_valid and common_valid:
        leave = Leave(
            applicant=request.user,
        )
        segments = list()
        type_of_leaves = LeaveType.objects.all()
        replacements = list()

        for form in leave_form_set:
            leave_segment = add_leave_segment(form, type_of_leaves)
            segments.append(leave_segment)

        for form in admin_form_set:
            rep = add_admin_rep_segment(form)
            replacements.append(rep)

        data = common_form.cleaned_data
        leave.purpose = data.get('purpose')
        #leave.is_station = data.get('is_station')
        leave.extra_info = data.get('leave_info')
        leave.save()
        rep_req = []
        for segment in segments:
            segment.leave = leave
        for replacement in replacements:
            replacement.leave = leave
            rep_req.append(replacement.replacer)
        LeaveSegment.objects.bulk_create(segments)
        ReplacementSegment.objects.bulk_create(replacements)

        deduct_leave_balance(leave,False)
        leave_module_notif(request.user, request.user, 'leave_applied')
        leave_module_notif(request.user, rep_req, 'replacement_request')
        messages.add_message(request, messages.SUCCESS, 'Successfully Submitted !')
        return redirect(reverse('leave:leave'))

    leave_requests = get_pending_leave_requests(request.user)
    rep_segments = request.user.rep_requests.filter(status='pending')
    leave_balance = request.user.leave_balance.all()
    user_leave_applications = Leave.objects.filter(applicant=request.user).order_by('-timestamp')
    processed_requests = request.user.all_leave_requests.filter(~Q(status='pending'))
    user_leave_applications_offline = LeaveOffline.objects.filter(applicant=request.user).order_by('-timestamp')
    context = {
        'processed_requests': processed_requests,
        'leave_form_set': leave_form_set,
        'acad_form_set': None,
        'admin_form_set': admin_form_set,
        'common_form': common_form,
        'forms': True,
        'rep_segments': rep_segments,
        'leave_balance': leave_balance,
        'leave_requests': leave_requests,
        'designation': user_designation,
        'user_leave_applications': user_leave_applications,
        'user_leave_applications_offline': user_leave_applications_offline
    }

    return render(request, 'leaveModule/leave.html', context)


@transaction.atomic
def handle_student_leave_application(request):

    form = StudentApplicationForm(request.POST, request.FILES, user=request.user)
    user_designation = get_designation(request.user)

    if form.is_valid():
        data = form.cleaned_data
        leave = Leave.objects.create(
            applicant=request.user,
            purpose=data.get('purpose'),
            extra_info=data.get('leave_info'),
        )

        leave_type = LeaveType.objects.get(name=data.get('leave_type'))

        LeaveSegment.objects.create(
            leave=leave,
            leave_type=leave_type,
            document=data.get('document'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date')
        )
        requested_from = request.user.leave_admins.authority.designees.first().user
        LeaveRequest.objects.create(
            leave=leave,
            requested_from=requested_from
        )
        deduct_leave_balance(leave,False)
        messages.add_message(request, messages.SUCCESS, 'Successfully Submitted !')
        return redirect('leave:leave')

    leave_balance = request.user.leave_balance.all()
    user_leave_applications = Leave.objects.filter(applicant=request.user).order_by('-timestamp')
    context = {
        'leave_balance': leave_balance,
        'user_leave_applications': user_leave_applications,
        'designation': user_designation,
        'form': form,
    }
    return render(request, 'leaveModule/leave.html', context)


def send_faculty_leave_form(request):
    rep_segments = request.user.rep_requests.filter(status='pending')
    leave_requests = get_pending_leave_requests(request.user)
    leave_balance = request.user.leave_balance.all()
    user_leave_applications = Leave.objects.filter(applicant=request.user).order_by('-timestamp')
    processed_requests = request.user.all_leave_requests.filter(~Q(status='pending'))
    user_designation = get_designation(request.user)
    user_leave_applications_offline = LeaveOffline.objects.filter(applicant=request.user).order_by('-timestamp')
    
    context = {
        'processed_requests': processed_requests,
        'leave_form_set': LeaveFormSet(prefix='leave_form', user=request.user),
        'acad_form_set': AcadFormSet(prefix='acad_form', form_kwargs={'user': request.user}),
        'admin_form_set': AdminFormSet(prefix='admin_form', form_kwargs={'user': request.user}),
        'common_form': common_form,
        'forms': True,
        'rep_segments': rep_segments,
        'leave_balance': leave_balance,
        'leave_requests': leave_requests,
        'designation': user_designation,
        'user_leave_applications': user_leave_applications,
        'user_leave_applications_offline': user_leave_applications_offline
    }

    return render(request, 'leaveModule/leave.html', context)


def send_staff_leave_form(request):
    rep_segments = request.user.rep_requests.filter(status='pending')
    leave_balance = request.user.leave_balance.all()
    leave_requests = get_pending_leave_requests(request.user)
    user_leave_applications = Leave.objects.filter(applicant=request.user).order_by('-timestamp')
    processed_requests = request.user.all_leave_requests.filter(~Q(status='pending'))
    user_designation = get_designation(request.user)
    user_leave_applications_offline = LeaveOffline.objects.filter(applicant=request.user).order_by('-timestamp')

    context = {
        'processed_requests': processed_requests,
        'leave_form_set': LeaveFormSet(prefix='leave_form', user=request.user),
        'acad_form_set': None,
        'admin_form_set': AdminFormSet(prefix='admin_form', form_kwargs={'user': request.user}),
        'common_form': common_form,
        'forms': True,
        'rep_segments': rep_segments,
        'leave_balance': leave_balance,
        'leave_requests': leave_requests,
        'designation': user_designation,
        'user_leave_applications': user_leave_applications,
        'user_leave_applications_offline': user_leave_applications_offline
    }

    return render(request, 'leaveModule/leave.html', context)


def send_student_leave_form(request):
    leave_balance = request.user.leave_balance.all()
    user_leave_applications = Leave.objects.filter(applicant=request.user).order_by('-timestamp')
    form = StudentApplicationForm(initial={}, user=request.user)
    user_designation = get_designation(request.user)
    context = {
        'leave_balance': leave_balance,
        'user_leave_applications': user_leave_applications,
        'designation': user_designation,
        'form': form,
    }

    return render(request, 'leaveModule/leave.html', context)


@transaction.atomic
def intermediary_processing(request, leave_request):
    status = request.POST.get('status')
    remark = request.POST.get('remark')
    leave_request.remark = remark
    leave = leave_request.leave
    if status == 'forward':
        leave_request.status = 'forwarded'
        leave_request.save()
        leave_module_notif(request.user, leave_request.leave.applicant, 'leave_forwarded')
        authority = leave.applicant.leave_admins.authority.designees.first().user
        LeaveRequest.objects.create(
            leave=leave_request.leave,
            requested_from=authority,
            permission='sanc_auth',
        )
        message = 'Successfully Forwarded'
    else:
        leave_request.status = 'rejected'
        leave_request.save()
        leave.status = 'rejected'
        leave.remark = 'Intermediary Rejected'
        leave.save()
        leave_module_notif(request.user, leave_request.leave.applicant, 'leave_rejected')
        message = 'Successfully Rejected'
        restore_leave_balance(leave)

    return JsonResponse({'status': 'success', 'message': message})


@transaction.atomic
def authority_processing(request, leave_request):
    status = request.POST.get('status')
    remark = request.POST.get('remark')
    leave_request.remark = remark
    leave = leave_request.leave

    if status == 'accept':
        leave_request.status = 'accepted'
        leave_request.save()

        leave.status = 'accepted'
        leave.save()
        create_migrations(leave)
        message = 'Successfully Accepted'
        leave_module_notif(request.user, leave_request.leave.applicant, 'leave_accepted')

    elif status == 'forward':
        leave_request.status = 'forwarded'
        leave_request.save()
        leave_module_notif(request.user, leave_request.leave.applicant, 'leave_forwarded')
        officer = leave.applicant.leave_admins.officer.designees.first().user
        leave_module_notif(leave_request.leave.applicant, officer, 'leave_request')
        LeaveRequest.objects.create(
            leave=leave,
            requested_from=officer,
            permission='sanc_off'
        )
        message = 'Successfully Forwarded'

    else:
        leave_request.status = 'rejected'
        leave_request.save()

        leave.status = 'rejected'
        leave.remark = 'Rejected by Leave Sanctioning Authority'
        leave.save()
        leave_module_notif(request.user, leave_request.leave.applicant, 'leave_rejected')
        restore_leave_balance(leave)
        message = 'Successfully Rejected'

    return JsonResponse({'status': 'success', 'message': message})


@transaction.atomic
def officer_processing(request, leave_request):
    status = request.POST.get('status')
    remark = request.POST.get('remark')
    leave_request.remark = remark
    leave = leave_request.leave

    if status == 'accept':
        leave_request.status = 'accepted'
        leave.status = 'accepted'
        message = 'Successfully Accepted'
        leave.save()
        leave_module_notif(request.user, leave_request.leave.applicant, 'leave_accepted')
        create_migrations(leave)
    else:
        leave_request.status = 'rejected'
        leave.status = 'rejected'
        leave.remark = 'Rejected by Leave Sanctioning Officer'
        leave.save()
        leave_module_notif(request.user, leave_request.leave.applicant, 'leave_rejected')
        message = 'Successfully Rejected'

    leave_request.save()
    # leave.save()
    return JsonResponse({'status': 'success', 'message': message})


@transaction.atomic
def process_staff_faculty_application(request):
    is_replacement_request = request.POST.get('rep')
    status = request.POST.get('status')
    id = request.POST.get('id')

    if is_replacement_request:

        with transaction.atomic():
            # TODO: Handle the Object not found error
            rep_request = ReplacementSegment.objects.get(id=id)
            if status == 'accept':
                # return JsonResponse({'status': 'success', 'message': 'Successfully Accepted'})
                rep_request.status = 'accepted'
                rep_request.remark = request.POST.get('remark')
                rep_request.save()
                leave_module_notif(request.user, rep_request.leave.applicant, 'request_accepted')
                if rep_request.leave.relacements_accepted():
                    """leave_intermediary = HoldsDesignation.objects.get(
                                                    designation__name='Leave Intermediary').user
                    LeaveRequest.objects.create(
                        requested_from=leave_intermediary,
                        leave=rep_request.leave,
                        permission='intermediary'
                    )"""
                    authority = rep_request.leave.applicant.leave_admins.authority.designees.first().user
                    leave_module_notif(rep_request.leave.applicant, authority, 'leave_request')
                    LeaveRequest.objects.create(
                        leave=rep_request.leave,
                        requested_from=authority,
                        permission='sanc_auth',
                    )
                return JsonResponse({'status': 'success', 'message': 'Successfully Accepted'})

            else:
                rep_request.status = 'rejected'
                rep_request.remark = request.POST.get('remark')
                rep_request.save()
                leave = rep_request.leave
                leave.status = 'rejected'
                leave.remark = 'Replacement Request rejected.'
                leave.save()
                leave_module_notif(request.user, rep_request.leave.applicant, 'request_declined')
                leave.replace_segments.filter(status='pending') \
                                      .update(status='auto rejected')
                restore_leave_balance(leave)
                return JsonResponse({'status': 'success', 'message': 'Successfully Rejected'})

    else:
        leave_request = LeaveRequest.objects.get(id=id)
        #if leave_request.permission == 'intermediary':
        #    return intermediary_processing(request, leave_request)

        if leave_request.permission == 'sanc_auth':
            return authority_processing(request, leave_request)

        else:
            return officer_processing(request, leave_request)


@transaction.atomic
def process_student_application(request):
    leave_request = LeaveRequest.objects.get(id=request.POST.get('id'))
    if request.user == leave_request.requested_from:
        status = request.POST.get('status')

        if status == 'accept':
            leave_request.status = 'accepted'
            leave_request.remark = 'No remark'
            leave_request.save()
            leave_request.leave.status = 'accepted'
            leave_request.leave.save()
            response = JsonResponse({'status': 'success', 'message': 'Successfully Accepted'})

        else:
            leave_request.status = 'rejected'
            leave_request.remark = request.POST.get('remark')
            leave_request.save()
            leave_request.leave.status = 'rejected'
            leave_request.leave.save()
            restore_leave_balance(leave_request.leave)
            response = JsonResponse({'status': 'success', 'message': 'Successfully Rejected'})

    else:
        response = JsonResponse({'status': 'failure', 'message': 'Unauthorized'}, status=401)

    return response


def delete_leave_application(request):
    leave_id = request.POST.get('id')
    leave = request.user.all_leaves.filter(id=leave_id).first()
    leave_start_date = LeaveSegment.objects.filter(leave=leave).first().start_date
    print(leave.status)
    if leave and leave.applicant == request.user and leave.status != 'rejected' and timezone.now().date() <= leave_start_date:
        rep_requests = ReplacementSegment.objects.filter(leave = leave)
        leave_requests = LeaveRequest.objects.filter(leave = leave)
        for i in rep_requests:
            if i.status == 'accepted':
                #notification to replacement user that  user has cancelled the leave
                print("It is working! Yeah")
                leave_module_notif(request.user, i.replacer, 'replacement_cancel', str(i.start_date))

        for i in leave_requests:
            if i.status == 'accepted':
                #notification to replacement user that  user has cancelled the leave
                print("It is working! Yeah")
                leave_module_notif(request.user, i.requested_from, 'leave_withdrawn', str(leave.timestamp.date()))

        restore_leave_balance(leave)
        leave.delete()
        #notification to user that he has cancelled the leave
        
        response = JsonResponse({'status': 'success', 'message': 'Successfully Cancelled'})
    else:
        response = JsonResponse({'status': 'failed', 'message': 'Cancellation Failed'}, status=400)

    return response

@transaction.atomic
def handle_offline_leave_application(request):

    
    try:
        leave_form_set = LeaveFormSetOffline(request.POST, request.FILES, prefix='leave_form_offline')
        academic_form_set = AcadFormSetOffline(request.POST, prefix='acad_form_offline')
        admin_form_set = AdminFormSetOffline(request.POST, prefix='admin_form_offline')
    except ValidationError:
        leave_form_set = None
        academic_form_set = None
        admin_form_set = None

    common_form = EmployeeCommonFormOffline(request.POST)
    leave_valid = leave_form_set.is_valid()
    #acad_valid = academic_form_set.is_valid()
    admin_valid = admin_form_set.is_valid()
    common_valid = common_form.is_valid()

    leave_user = ""
    type_of_user = "staff"
    data=""
    if common_valid:
        data = common_form.cleaned_data
        leave_user = User.objects.get(username = data.get('leave_user_select'))
        type_of_user = leave_user.extrainfo.user_type

    print("\n\n\n"+type_of_user+"\n\n\n")
    if leave_valid and admin_valid and common_valid and type_of_user=="faculty":
        #data = common_form.cleaned_data
        if academic_form_set.is_valid():
            leave = LeaveOffline(
                applicant=leave_user
            )
            segments_offline = list()
            type_of_leaves = LeaveType.objects.all()
            replacements = list()
            for form in leave_form_set:
                leave_segment = add_leave_segment_offline(form, type_of_leaves)
                segments_offline.append(leave_segment)

            for form in academic_form_set:
                rep = add_acad_rep_segment_offline(form)
                replacements.append(rep)

            for form in admin_form_set:
                rep = add_admin_rep_segment_offline(form)
                replacements.append(rep)


            leave.purpose = data.get('purpose')
            #leave.is_station = data.get('is_station')
            leave.application_date = data.get('application_date')
            leave.leave_user_select = leave_user
            #leave_user = User.objects.get(username = data.get('leave_user_select'))
            leave.save()
            for segment in segments_offline:
                segment.leave = leave
            for replacement in replacements:
                replacement.leave = leave
            LeaveSegmentOffline.objects.bulk_create(segments_offline)
            ReplacementSegmentOffline.objects.bulk_create(replacements)
            deduct_leave_balance(leave,True)
            leave_module_notif(request.user, leave_user, 'offline_leave')

            messages.add_message(request, messages.SUCCESS, 'Successfully Submitted !')
            return redirect(reverse('leave:leavemanager'))

    elif leave_valid and admin_valid and common_valid and type_of_user=="staff":
        #data = common_form.cleaned_data
        leave = LeaveOffline(
            applicant=leave_user
        )
        segments_offline = list()
        type_of_leaves = LeaveType.objects.all()
        replacements = list()
        for form in leave_form_set:
            leave_segment = add_leave_segment_offline(form, type_of_leaves)
            segments_offline.append(leave_segment)

        for form in admin_form_set:
            rep = add_admin_rep_segment_offline(form)
            replacements.append(rep)


        leave.purpose = data.get('purpose')
        #leave.is_station = data.get('is_station')
        leave.application_date = data.get('application_date')
        leave.leave_user_select = leave_user
        #leave_user = User.objects.get(username = data.get('leave_user_select'))
        leave.save()
        for segment in segments_offline:
            segment.leave = leave
        for replacement in replacements:
            replacement.leave = leave
        LeaveSegmentOffline.objects.bulk_create(segments_offline)
        ReplacementSegmentOffline.objects.bulk_create(replacements)
        deduct_leave_balance(leave,True)
        leave_module_notif(request.user, leave_user, 'offline_leave')

        messages.add_message(request, messages.SUCCESS, 'Successfully Submitted !')
        return redirect(reverse('leave:leavemanager'))

    
    #rep_segments = leave_user.rep_requests_offline.all()
    #leave_requests = get_pending_leave_requests(leave_user)
    #leave_balance = leave_user.leave_balance.all()
    user_leave_applications = LeaveOffline.objects.filter(applicant=leave_user).order_by('-timestamp')
    #processed_requests = request.user.all_leave_requests.filter(~Q(status='pending'))
    if type_of_user=="faculty":
        context = {
           
            'leave_form_offline_set': leave_form_set,
            'acad_form_offline_set': academic_form_set,
            'admin_form_offline_set': admin_form_set,
            'common_offline_form': common_form,
            'forms': True,
            'user_leave_applications_offline': user_leave_applications
        }

        return render(request, 'leaveModule/test.html', context)
    elif type_of_user=="staff":
        context = {
           
            'leave_form_offline_set': leave_form_set,
            'admin_form_offline_set': admin_form_set,
            'common_offline_form': common_form,
            'forms': True,
            'user_leave_applications_offline': user_leave_applications
        }

        return render(request, 'leaveModule/test.html', context)


def send_offline_leave_form(request):
    #rep_segments = request.user.rep_requests_offline.all()
    #leave_balance = request.user.leave_balance.all()
    #user_leave_applications = LeaveOffline.objects.filter(applicant=request.user).order_by('-timestamp')
    
    context = {
        'leave_form_set': LeaveFormSetOffline(prefix='leave_form_offline'),
        'acad_form_set': AcadFormSetOffline(prefix='acad_form_offline'),
        'admin_form_set': AdminFormSetOffline(prefix='admin_form_offline'),
        'common_form': common_form_offline,
        'forms': True
    }

    return render(request, 'leaveModule/test.html', context)
