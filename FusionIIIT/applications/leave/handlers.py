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
                    StudentApplicationFormUG, StudentApplicationFormPG, AcademicReplacementFormOffline, AdminReplacementFormOffline,
                    BaseLeaveFormSetOffline, EmployeeCommonFormOffline, LeaveSegmentFormOffline )
from .helpers import (create_migrations, deduct_leave_balance, deduct_leave_balance_student, get_leave_days,
                      get_pending_leave_requests, restore_leave_balance, get_designation)
from .models import (Leave, LeaveRequest, LeaveSegment,
                     LeaveType, ReplacementSegment, LeaveOffline, LeaveSegmentOffline, ReplacementSegmentOffline)
from applications.globals.models import HoldsDesignation
from notification.views import leave_module_notif
from django.utils import timezone
from applications.globals.models import (ExtraInfo)

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
    """
    Creates a new LeaveSegment object using form data and returns it.

    Parameters:
    - form: the LeaveSegmentForm object containing the form data
    - type_of_leaves: the queryset of available LeaveType objects

    Description:
    This function creates a new LeaveSegment object using the cleaned form data. It retrieves the selected
    LeaveType object from the provided queryset and uses the form data to create a new LeaveSegment object.
    The function then returns the created LeaveSegment object.

    Results:
    This function returns a new LeaveSegment object created using the form data. The object includes the
    selected LeaveType, start date, end date, start half, end half, document, and address information.
    """
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
    """
    Creates a new ReplacementSegment object for academic replacement using form data and returns it.

    Parameters:
    - form: the AcademicReplacementSegmentForm object containing the form data

    Description:
    This function creates a new ReplacementSegment object for academic replacement using the cleaned form data.
    It retrieves the selected academic representative's user object and uses the form data to create a new
    ReplacementSegment object. The function then returns the created ReplacementSegment object.

    Results:
    This function returns a new ReplacementSegment object created using the form data. The object includes the
    replacer user object, replacement type 'academic', start date, and end date information.
    """
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
    """
    Creates a new ReplacementSegment object for administrative replacement using form data and returns it.

    Parameters:
    - form: the AdminReplacementSegmentForm object containing the form data

    Description:
    This function creates a new ReplacementSegment object for administrative replacement using the cleaned form data.
    It retrieves the selected administrative representative's user object and uses the form data to create a new
    ReplacementSegment object. The function then returns the created ReplacementSegment object.

    Results:
    This function returns a new ReplacementSegment object created using the form data. The object includes the
    replacer user object, replacement type 'administrative', start date, and end date information.
    """
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
    """
    Creates a new LeaveSegmentOffline object using form data and returns it.

    Parameters:
    - form: the LeaveSegmentOfflineForm object containing the form data
    - type_of_leaves: the queryset of available LeaveType objects

    Description:
    This function creates a new LeaveSegmentOffline object using the cleaned form data. It retrieves the selected
    LeaveType object from the provided queryset and uses the form data to create a new LeaveSegmentOffline object.
    The function then returns the created LeaveSegmentOffline object.

    Results:
    This function returns a new LeaveSegmentOffline object created using the form data. The object includes the
    selected LeaveType, start date, end date, start half, end half, document, and address information.
    """
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
    """
    Creates a new ReplacementSegmentOffline object for academic replacement using form data and returns it.

    Parameters:
    - form: the AcademicReplacementSegmentOfflineForm object containing the form data

    Description:
    This function creates a new ReplacementSegmentOffline object for academic replacement using the cleaned form data.
    It retrieves the selected academic representative's user object and uses the form data to create a new
    ReplacementSegmentOffline object. The function then returns the created ReplacementSegmentOffline object.

    Results:
    This function returns a new ReplacementSegmentOffline object created using the form data. The object includes the
    replacer user object, replacement type 'academic', start date, and end date information.
    """
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
    """
    Creates a new ReplacementSegmentOffline object for administrative replacement using form data and returns it.

    Parameters:
    - form: the AdminReplacementSegmentOfflineForm object containing the form data

    Description:
    This function creates a new ReplacementSegmentOffline object for administrative replacement using the cleaned form
    data. It retrieves the selected administrative representative's user object and uses the form data to create a new
    ReplacementSegmentOffline object. The function then returns the created ReplacementSegmentOffline object.

    Results:
    This function returns a new ReplacementSegmentOffline object created using the form data. The object includes the
    replacer user object, replacement type 'administrative', start date, and end date information.
    """
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
    """
    Handle faculty leave application by validating and creating Leave, LeaveSegment,
    and ReplacementSegment objects.

    Args:
        request (HttpRequest): HTTP request object representing the faculty leave application.

    Returns:
        HttpResponse: HTTP response object representing the success/failure of the faculty leave application.

    Raises:
        N/A

    Required Modules:
        django.db.transaction
        django.shortcuts.redirect
        django.shortcuts.render
        django.urls.reverse
        django.contrib.messages.add_message

    """
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
    """
    View function to handle staff leave application.
    It renders the leave.html template for GET request and handles the leave application
    submission for POST request.
    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The HTTP response object.

    Raises:
        None
    """
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
    """
    Handle student leave application.
    """

    form = None
    if request.user.extrainfo.u_type == 'ug':
        form = StudentApplicationFormUG(request.POST, request.FILES, user=request.user)
    else:
        form = StudentApplicationFormPG(request.POST, request.FILES, user=request.user)

    user_designation = get_designation(request.user)

    if form.is_valid():
        data = form.cleaned_data
        leave = Leave.objects.create(
            applicant=request.user,
            purpose=data.get('purpose'),
            extra_info=data.get('leave_info'),
        )
        leave.save()

        leave_type = LeaveType.objects.get(name=data.get('leave_type'))

        leave_type.save()

        LeaveSegment.objects.create(
            leave=leave,
            leave_type=leave_type,
            document=data.get('document'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date')
        )

        count = (data.get('end_date') -data.get('start_date')).days + 1

        dep_id = request.user.extrainfo.department_id
        hod_id = ExtraInfo.objects.get(department_id=dep_id, user_type="hod").user_id

        hod = User.objects.get(id=hod_id)

        LeaveRequest.objects.create(
            leave=leave,
            requested_from=hod
        )
        deduct_leave_balance_student(leave_type, count, request.user)
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
    """
    Method name: send_faculty_leave_form(request)

    Parameters:
        request: HttpRequest object representing the current request.
    Short description:
        Renders the 'leave.html' template with context data containing various form sets, leave balance, leave requests, and leave applications for a faculty member.

    Results:
        Returns an HttpResponse object that renders the 'leave.html' template with context data containing various form sets, leave balance, leave requests, and leave applications for a faculty member.
    """
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
        'user_leave_applications_offline': user_leave_applications_offline,
        'form': StudentApplicationFormPG(initial={}, user=request.user)
    }

    return render(request, 'leaveModule/leave.html', context)


def send_staff_leave_form(request):
    """
    The send_staff_leave_form function accepts a request object and generates a context dictionary containing information related to staff leave requests. The context dictionary is then rendered using the leaveModule/leave.html template and returned as an HTTP response.

    Parameters:
        request: An HTTP request object.

    Returns:
        An HTTP response object containing the leaveModule/leave.html template rendered with the context dictionary.

    Short Description:
        This function generates a context dictionary containing information related to staff leave requests and renders it using the leaveModule/leave.html template.
    Note:
        The function assumes that the LeaveFormSet, AdminFormSet, and common_form objects are defined and imported from other modules.
    """
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
    """
    Method : send_student_leave_form(request)
    Sends the leave application form to the student user along with their leave balance and any
    previous leave applications made by the user.

    Parameters:
        - request: HttpRequest object representing the incoming request

    Returns:
        - HttpResponse object representing the rendered leave application page with all the necessary context data.
    """
    leave_balance = request.user.leave_balance.all()
    user_leave_applications = Leave.objects.filter(applicant=request.user).order_by('-timestamp')
    form = None
    user_designation = get_designation(request.user)
    user_type = request.user.extrainfo.u_type

    if user_type == 'ug':
        form = StudentApplicationFormUG(initial={}, user=request.user)
    else:
        form = StudentApplicationFormPG(initial={}, user=request.user)

    context = {
        'leave_balance': leave_balance,
        'user_leave_applications': user_leave_applications,
        'designation': user_designation,
        'form': form,
        'u_type': user_type
    }

    return render(request, 'leaveModule/leave.html', context)


@transaction.atomic
def intermediary_processing(request, leave_request):
    """
    Function: `intermediary_processing(request, leave_request)`

    Parameters:

        request: HttpRequest object representing the current request
        leave_request: LeaveRequest object representing the leave request being processed

    Description:
        This function handles the processing of a leave request by an intermediary authority. It retrieves the status and remark submitted with the request, updates the leave request object with the remark, and performs the appropriate action based on the status. If the status is 'forward', the leave request is marked as forwarded and a new leave request is created for the next authority. If the status is not 'forward', the leave request is marked as rejected and the corresponding leave object is updated with the 'rejected' status and remark. The function also sends notifications to the applicant and updates the leave balance if necessary.

    Returns:
        A JsonResponse object containing a status flag and a message indicating the success or failure of the processing.
    """
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
    """
    authority_processing(request, leave_request)
    Parameters:
        - request: HTTP request object
        - leave_request: LeaveRequest object

    Short description:
        This function handles the processing of a leave request by the Leave Sanctioning Authority.

    Results:
        This function updates the status and remark of the given leave_request object based on the action taken by the Leave Sanctioning Authority. If the leave request is accepted, it updates the status of the associated leave object, creates a migration object, and sends a notification to the applicant. If the leave request is forwarded, it creates a new LeaveRequest object for the next level of authority and sends a notification to the applicant and officer. If the leave request is rejected, it updates the status of the associated leave object, restores the leave balance, and sends a notification to the applicant.
    """
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
    """
    Method name: officer_processing(request, leave_request)

    Parameters:
        - request: HttpRequest object representing the current request
        - leave_request: LeaveRequest object representing the leave request being processed
        
    Short description:
        This function is responsible for processing a leave request by a Leave Sanctioning Officer. It updates the status and remark of the leave request and leave objects, and sends notification to the applicant.

    Results:
        The function generates a JSON response with status and message indicating whether the leave request was successfully accepted or rejected.
    """
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
    """
    Processes staff/faculty leave requests and replacement requests by updating the relevant database objects.
    If a replacement request is accepted, and all other replacements have been accepted, the function creates a LeaveRequest object for the appropriate authority to approve the leave request. If a replacement request is rejected, the leave request associated with it is also rejected, and any other pending replacement requests are automatically rejected. If the original request was submitted by an authority, it is forwarded to the next level of authority for approval.

    :param request: The HTTP request object.

    :return: A JSON response indicating the success of the operation.
    """
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
    """
    Function :  process_student_application(request)
    Processes a student leave application by either accepting or rejecting it, based on the input parameters.
    Args:
        request (HttpRequest): The HTTP request object containing the input parameters.

    Returns:
        A JsonResponse object containing the status and message indicating whether the leave request was successfully 
        accepted or rejected, or an error message if the user is not authorized to process the request.
    """
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
    """
    Function Name: delete_leave_application

    Parameters:
        request: HTTP request object containing data for the leave application to be deleted

    Description:
        This function handles the cancellation of a leave application by a user. The function checks if the leave exists, belongs to the user and has not been rejected, and that the start date of the leave is not past. If these conditions are met, any accepted replacement segments or leave requests associated with the leave are cancelled, and the leave is deleted. Notifications are sent to any affected users. If the conditions are not met, an error response is sent.

    Returns:
        response: A JSON response containing a status message indicating whether the leave was successfully cancelled or not.
    """
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
    """
    Function Name : `handle_offline_leave_application(request)`
    Parameter list:

        `request`: an HTTP request object representing the current request.

    Short description:

        The function handles the submission of an offline leave application by a staff or faculty member. It performs form validation, creates leave and replacement segments, deducts leave balance, sends a notification, and redirects to the leave manager page.

    Results/queries:

        The function creates a new instance of LeaveOffline and saves it to the database, along with its corresponding LeaveSegmentOffline and ReplacementSegmentOffline instances. It also deducts the leave balance of the applicant, sends a notification to the leave module, and redirects to the leave manager page. If the form is not valid, it displays an error message and renders the form page again with the input data. If the user is a staff member, the academic form set is not needed and is not validated. The function returns an HTTP response object.
    """
    
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
    """
    Function definition: send_offline_leave_form(request)

    Parameter list:
        - request: The HTTP request sent by the client.

    Short description:
        This function generates a context dictionary with formsets and a common form to be rendered in the 'leaveModule/test.html' template.

    Results:
        The function returns a rendered HTTP response with the 'leaveModule/test.html' template, which displays formsets and a common form.
    """
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
