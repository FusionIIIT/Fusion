from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation, DepartmentInfo
from notification.views import establishment_notif

from datetime import datetime
from .models import *
from .forms import *


def initial_checks(request):
    return {}


def is_admin(request):
    return request.user == Establishment_variables.objects.first().est_admin


def get_admin():
    return Establishment_variables.objects.first().est_admin


def is_eligible(request):
    return True


def is_fm(dictx):
    for key in dictx.keys():
        if 'fm_' in key:
            return True
    return False


def is_cpda(dictx):
    for key in dictx.keys():
        if 'cpda' in key:
            return True
    return False


def is_ltc(dictx):
    for key in dictx.keys():
        if 'ltc' in key:
            return True
    return False


# TODO THIS
def handle_fm_admin(request):
    if 'fm_new_employee' in request.POST:
        # print (request.POST)
        username = request.POST.get('username')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'The given user ALREADY exists')
            return

        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        if password != password2:
            messages.error(request, 'The given passwords do not match.')
            return

        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        user = User.objects.create(
            username = username,
            first_name = first_name,
            last_name = last_name,
            email = email
        )
        user.set_password(password)
        user.save()
        
        title = request.POST.get('title')
        gender = request.POST.get('gender')
        dob = request.POST.get('dob')
        address = request.POST.get('address')
        phone_no = request.POST.get('phone_no')
        dept = request.POST.get('department')
        department = DepartmentInfo.objects.filter(id=dept).first()
        # I'm using username as an id for Extra_info
        extra_info = ExtraInfo.objects.create(
            id = username,
            user = user,
            title = title,
            sex = gender,
            date_of_birth = dob,
            address = address,
            phone_no = phone_no,
            user_type = 'faculty',
            department = department,
        )
        faculty = Faculty.objects.create(
            id = extra_info
        )

        pf_number = request.POST.get('pf_number')
        date_of_joining = request.POST.get('date_of_joining')
        joining_payscale = request.POST.get('joining_payscale')
        isVac = request.POST.get('isVacational')
        if isVac == 'on':
            isVacational = True
        else:
            isVacational = False
        category = request.POST.get('category')
        desig = request.POST.get('designation')
        designation = Designation.objects.filter(id=desig).first()
        pan_number = request.POST.get('pan_number')
        aadhar_number = request.POST.get('aadhar_number')
        local_address = request.POST.get('local_address')
        marital_status = request.POST.get('marital_status')
        spouse_name = request.POST.get('spouse_name')
        children_info = request.POST.get('children_info')
        personal_email_id = request.POST.get('personal_email_id')

        faculty_info = Faculty_Info.objects.create(
            faculty_user = faculty,
            pf_number = pf_number,
            joining_date = date_of_joining,
            designation = designation,
            joining_payscale = joining_payscale,
            is_vacational = isVacational,
            category = category,
            pan_number = pan_number,
            aadhar_number = aadhar_number,
            local_address = local_address,
            marital_status = marital_status,
            spouse_name = spouse_name,
            children_info = children_info,
            personal_email_id = personal_email_id,
            is_archived = False
        )
        HoldsDesignation.objects.create(
            user = user,
            working = user,
            designation = designation,
            held_at = datetime.now()
        )
        establishment_notif(user, user, 'fm_new_faculty')
        messages.success(request, 'New Faculty user succesfully created')

    # elif 'fm_edit_faculty' in request.POST:

    # elif 'fm_delete_faculty' in request.POST:


def handle_cpda_admin(request):
    app_id = request.POST.get('app_id')
    status = request.POST.get('status')
    reviewer = request.POST.get('reviewer_id')
    designation = request.POST.get('reviewer_design')
    remarks = request.POST.get('remarks')
    if status == 'requested' or status == 'adjustments_pending':
        if reviewer and designation and app_id:
            # assign the app to the reviewer
            reviewer_id = User.objects.get(username=reviewer)
            reviewer_design = Designation.objects.filter(name=designation)

            # check if the reviewer holds the given designation, if not show error
            if reviewer_design:
                reviewer_design = reviewer_design[0]
            # if reviewer_design != HoldsDesignation.objects.get(user=reviewer_id):
            #     messages.error(request, 'Reviewer doesn\'t holds the designation you specified!')
            # else:
            application = Cpda_application.objects.get(id=app_id)
            application.tracking_info.reviewer_id = reviewer_id
            application.tracking_info.reviewer_design = reviewer_design
            application.tracking_info.remarks = remarks
            application.tracking_info.review_status = 'under_review'
            application.tracking_info.save()
            
            # The reviewer is notified about the pending review
            establishment_notif(request.user, reviewer_id, 'cpda_review_pending')
            messages.success(request, 'Reviewer assigned successfully!')
            # print (reviewer_design, ' ||| ', reviewer_id)

        else:
            errors = "Please specify a reviewer and their designation."
            messages.error(request, errors)

    elif app_id:
        # update the status of app
        # verify that app_id is not changed, ie untampered
        application = Cpda_application.objects.get(id=app_id)
        application.status = status;
        application.save()
        # print (application)

        # Send notification to the cpda applicant
        if status == 'approved':
            establishment_notif(request.user, application.applicant, 'cpda_request_approved')
        elif status == 'rejected':
            establishment_notif(request.user, application.applicant, 'cpda_request_rejected')
        elif status == 'finished':
            establishment_notif(request.user, application.applicant, 'cpda_adjustment_finished')
        messages.success(request, 'Status updated successfully!')


def handle_ltc_admin(request):
    if 'ltc_assign_form' in request.POST:
        app_id = request.POST.get('app_id')
        status = request.POST.get('status')
        reviewer = request.POST.get('reviewer_id')
        designation = request.POST.get('reviewer_design')
        remarks = request.POST.get('remarks')
        if status == 'requested':
            if reviewer and designation and app_id:
                # assign the app to the reviewer
                reviewer_id = User.objects.get(username=reviewer)
                reviewer_design = Designation.objects.filter(name=designation)

                # check if the reviewer holds the given designation, if not show error
                if reviewer_design:
                    reviewer_design = reviewer_design[0]
                # if reviewer_design != HoldsDesignation.objects.get(user=reviewer_id):
                #     messages.error(request, 'Reviewer doesn\'t holds the designation you specified!')
                # else:
                application = Ltc_application.objects.get(id=app_id)
                application.tracking_info.reviewer_id = reviewer_id
                application.tracking_info.reviewer_design = reviewer_design
                application.tracking_info.remarks = remarks
                application.tracking_info.review_status = 'under_review'
                application.tracking_info.save()
                
                # The reviewer is notified about the pending review
                establishment_notif(request.user, reviewer_id, 'ltc_review_pending')
                messages.success(request, 'Reviewer assigned successfully!')
                # print (reviewer_design, ' ||| ', reviewer_id)

            else:
                errors = "Please specify a reviewer and their designation."
                messages.error(request, errors)

        elif app_id:
            # update the status of app
            # verify that app_id is not changed, ie untampered
            application = Ltc_application.objects.get(id=app_id)
            application.status = status;
            application.save()
            # Send notification to the cpda applicant
            if status == 'approved':
                establishment_notif(request.user, application.applicant, 'ltc_request_approved')
            elif status == 'rejected':
                establishment_notif(request.user, application.applicant, 'ltc_request_rejected')
            messages.success(request, 'Status updated successfully!')

    elif 'ltc_new_eligible_user' in request.POST:
        username = request.POST.get('username')
        if not User.objects.filter(username=username).exists():
            messages.error(request, 'The given user does not exist')
            return

        user_id = User.objects.get(username=username)
        if Ltc_eligible_user.objects.filter(user=user_id).exists():
            messages.error(request, 'This user is already eligible for availing LTC')
            return

        joining_date = request.POST.get('joining_date')
        current_block_size = request.POST.get('current_block_size')
        total_ltc_allowed = request.POST.get('total_ltc_allowed')
        hometown_ltc_allowed = request.POST.get('hometown_ltc_allowed')
        elsewhere_ltc_allowed = request.POST.get('elsewhere_ltc_allowed')
        hometown_ltc_availed = request.POST.get('hometown_ltc_availed')
        elsewhere_ltc_availed = request.POST.get('elsewhere_ltc_availed')

        eligible_user = Ltc_eligible_user.objects.create(
            user = user_id,
            date_of_joining = joining_date,
            current_block_size = current_block_size,
            total_ltc_allowed = total_ltc_allowed,
            hometown_ltc_allowed = hometown_ltc_allowed,
            elsewhere_ltc_allowed = elsewhere_ltc_allowed,
            hometown_ltc_availed = hometown_ltc_availed,
            elsewhere_ltc_availed = elsewhere_ltc_availed
        )
        messages.success(request, 'New LTC eligible user succesfully created')

    elif 'ltc_edit_eligible_user' in request.POST:
        username = request.POST.get('username')
        if not User.objects.filter(username=username).exists():
            messages.error(request, 'The given user does not exist')
            return

        user_id = User.objects.get(username=username)
        joining_date = request.POST.get('joining_date')
        current_block_size = request.POST.get('current_block_size')
        total_ltc_allowed = request.POST.get('total_ltc_allowed')
        hometown_ltc_allowed = request.POST.get('hometown_ltc_allowed')
        elsewhere_ltc_allowed = request.POST.get('elsewhere_ltc_allowed')
        hometown_ltc_availed = request.POST.get('hometown_ltc_availed')
        elsewhere_ltc_availed = request.POST.get('elsewhere_ltc_availed')

        eligible_user = Ltc_eligible_user.objects.get(user=user_id)
        eligible_user.date_of_joining = joining_date
        eligible_user.current_block_size = current_block_size
        eligible_user.total_ltc_allowed = total_ltc_allowed
        eligible_user.hometown_ltc_allowed = hometown_ltc_allowed
        eligible_user.elsewhere_ltc_allowed = elsewhere_ltc_allowed
        eligible_user.hometown_ltc_availed = hometown_ltc_availed
        eligible_user.elsewhere_ltc_availed = elsewhere_ltc_availed
        eligible_user.save()
        messages.success(request, 'Eligible LTC user details successfully updated.')

    elif 'ltc_delete_eligible_user' in request.POST:
        username = request.POST.get('username')
        if not User.objects.filter(username=username).exists():
            messages.error(request, 'The given user does not exist')
            return

        user_id = User.objects.get(username=username)
        if not Ltc_eligible_user.objects.filter(user=user_id).exists():
            messages.error(request, 'This user already isn\'t eligible for availing LTC')
            return

        eligible_user = Ltc_eligible_user.objects.get(user=user_id)
        eligible_user.delete()
        messages.success(request, 'User successfully removed from eligible LTC users')


# TODO THIS
def generate_fm_admin_lists(request):
    new_employee_form = Employee_Registration_Form()
    response = {
        'admin': True,
        'fm_add_employee_form' : new_employee_form
    }
    return response


def generate_cpda_admin_lists(request):

    # only requested and adjustment_pending
    unreviewed_apps = (Cpda_application.objects
                .exclude(status='rejected')
                .exclude(status='finished')
                .exclude(status='approved')
                .order_by('-request_timestamp'))
    pending_apps = []
    under_review_apps = []
    for app in unreviewed_apps:
        if app.tracking_info.review_status == 'under_review':
            under_review_apps.append(app)
        else:
            pending_apps.append(app)

    # combine assign_form object into unreviewed_app object respectively
    for app in unreviewed_apps:
        # if status is requested:to_assign/reviewed
        if app.status == 'requested':
            temp = Assign_Form(initial={'status': 'requested', 'app_id': app.id})
            temp.fields["status"]._choices = [
                ('requested', 'Requested'),
                ('approved', 'Approved'),
                ('rejected', 'Rejected')
            ]
        # if status is adjustments_pending:to_assign/reviewed
        else:
            temp = Assign_Form(initial={'status': 'adjustments_pending', 'app_id': app.id})
            temp.fields["status"]._choices = [
                ('adjustments_pending', 'Adjustments Pending'),
                ('finished', 'Finished')
            ]
        app.assign_form = temp
        # print (app.assign_form.fields['status']._choices)
        
    # only approved
    approved_apps = (Cpda_application.objects
                    .filter(status='approved')
                    .order_by('-request_timestamp'))

    # only rejected and finished
    archived_apps = (Cpda_application.objects
                    .exclude(status='approved')
                    .exclude(status='requested')
                    .exclude(status='adjustments_pending')
                    .order_by('-request_timestamp'))

    response = {
        'admin': True,
        'cpda_pending_apps': pending_apps,
        'cpda_under_review_apps': under_review_apps,
        'cpda_approved_apps': approved_apps,
        'cpda_archived_apps': archived_apps
    }
    return response


def generate_ltc_admin_lists(request):

    # only requested and adjustment_pending
    unreviewed_apps = (Ltc_application.objects
                .filter(status='requested')
                .order_by('-request_timestamp'))
    pending_apps = []
    under_review_apps = []
    for app in unreviewed_apps:
        if app.tracking_info.review_status == 'under_review':
            under_review_apps.append(app)
        else:
            pending_apps.append(app)

    # combine assign_form object into unreviewed_app object respectively
    for app in unreviewed_apps:
        temp = Assign_Form(initial={'status': 'requested', 'app_id': app.id})
        temp.fields["status"]._choices = [
            ('requested', 'Requested'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ]
        app.assign_form = temp
        # print (app.assign_form.fields['status']._choices)
        
    # approved and rejected
    archived_apps = (Ltc_application.objects
                    .exclude(status='requested')
                    .order_by('-request_timestamp'))

    current_eligible_users = Ltc_eligible_user.objects.order_by('user')
    for user in current_eligible_users:
        temp = Ltc_Eligible_Form(initial={
            'username': user.user,
            'joining_date': user.date_of_joining,
            'current_block_size': user.current_block_size,
            'total_ltc_allowed': user.total_ltc_allowed,
            'hometown_ltc_allowed': user.hometown_ltc_allowed,
            'elsewhere_ltc_allowed': user.elsewhere_ltc_allowed,
            'hometown_ltc_availed': user.hometown_ltc_availed,
            'elsewhere_ltc_availed': user.elsewhere_ltc_availed
        })
        # temp.fields['username'].widget.attrs['readonly'] = True
        user.edit_form = temp

    new_ltc_eligible_user =  Ltc_Eligible_Form()

    response = {
        'admin': True,
        'ltc_eligible_users': current_eligible_users,
        'ltc_new_eligible_user_form': new_ltc_eligible_user,
        'ltc_pending_apps': pending_apps,
        'ltc_under_review_apps': under_review_apps,
        'ltc_archived_apps': archived_apps
    }
    return response


def handle_cpda_eligible(request):
    if 'cpda_request' in request.POST:
        print(" *** CPDA request submit *** ")
        applicant = request.user
        pf_number = request.POST.get('pf_number')
        purpose = request.POST.get('purpose')
        advance = request.POST.get('requested_advance')
        status = 'requested'
        timestamp = datetime.now()
        application = Cpda_application.objects.create(
            applicant=applicant,
            pf_number=pf_number,
            purpose=purpose,
            requested_advance=advance,
            request_timestamp=timestamp,
            status=status
        )
        # next 3 lines are working magically, DON'T TOUCH THEM
        track = Cpda_tracking.objects.create(
            application = application,
            review_status = 'to_assign'
        )
        # print (application.tracking_info.application)

        # Send notification to admin that new cpda application is created
        establishment_notif(request.user, get_admin(), 'cpda_application_submit')
        messages.success(request, 'Request sent successfully!')

    elif 'cpda_adjust' in request.POST:
        # add multiple files
        # get application object here DONE
        app_id = request.POST.get('app_id')
        # verify that app_id is not changed, ie untampered
        application = Cpda_application.objects.get(id=app_id)
        upload_file = request.FILES.get('bills')
        adjustment_amount = request.POST.get('adjustment_amount')
        bills_amount = request.POST.get('total_bills_amount')

        Cpda_bill.objects.create(
            application_id = app_id,
            bill = upload_file
        )                           

        bills_attached = 1                
        timestamp = datetime.now()

        application.bills_attached = bills_attached
        application.total_bills_amount = bills_amount
        application.adjustment_amount = adjustment_amount
        application.adjustment_timestamp = timestamp
        application.status = 'adjustments_pending'
        application.save()

        # get tracking info of a particular application
        application.tracking_info.review_status = 'to_assign'
        application.tracking_info.save()

        # Send notification to admin that new cpda bills are submitted
        establishment_notif(request.user, get_admin(), 'cpda_bills_submit')
        messages.success(request, 'Bills submitted successfully!')
        
    elif 'cpda_review' in request.POST:
        print(" *** CPDA Review submit *** ")
        app_id = request.POST.get('app_id')
        # verify that app_id is not changed, ie untampered
        review_comment = request.POST.get('remarks')
        application = Cpda_application.objects.get(id=app_id)
        application.tracking_info.remarks = review_comment
        application.tracking_info.review_status = 'reviewed'
        application.tracking_info.save()
        # Send notification to admin that new cpdaapplication is created
        establishment_notif(request.user, get_admin(), 'cpda_review_submit')
        messages.success(request, 'Review submitted successfully!')


def handle_ltc_eligible(request):
    if 'ltc_request' in request.POST:
        print(" *** LTC request submit *** ")
        applicant = request.user

        pf_number = request.POST.get('pf_number') 
        basic_pay = request.POST.get('basic_pay') 

        is_leave_req = request.POST.get('is_leave_req') 
        leave_start = request.POST.get('leave_start') 
        leave_end = request.POST.get('leave_end') 
        family_departure_date = request.POST.get('family_departure_date') 
        leave_nature = request.POST.get('leave_nature') 
        purpose = request.POST.get('purpose') 
        leave_type = request.POST.get('leave_type') 
        address_during_leave = request.POST.get('address_during_leave') 
        phone_number = request.POST.get('phone_number') 
        travel_mode = request.POST.get('travel_mode') 

        ltc_availed = request.POST.get('ltc_availed') 
        ltc_to_avail = request.POST.get('ltc_to_avail') 
        dependents = request.POST.get('dependents') 
        requested_advance = request.POST.get('requested_advance') 

        status = 'requested'
        timestamp = datetime.now()
        application = Ltc_application.objects.create(
            # save all
            applicant=applicant,
            pf_number=pf_number,
            basic_pay = basic_pay,
            is_leave_required = is_leave_req,
            leave_start = leave_start,
            leave_end = leave_end,
            family_departure_date = family_departure_date,
            leave_nature = leave_nature,
            purpose = purpose,
            is_hometown_or_elsewhere = leave_type,
            address_during_leave = address_during_leave,
            phone_number = phone_number,
            travel_mode = travel_mode,
            ltc_availed = ltc_availed,
            ltc_to_avail = ltc_to_avail,
            dependents = dependents,
            requested_advance = requested_advance,
            request_timestamp=timestamp,
            status=status
        )
        # next 3 lines are working magically, DON'T TOUCH THEM
        track = Ltc_tracking.objects.create(
            application = application,
            review_status = 'to_assign'
        )
        # print (application.tracking_info.application)

        # Send notification to admin that new cpda bills are submitted
        establishment_notif(request.user, get_admin(), 'ltc_application_submit')
        messages.success(request, 'Request sent successfully!')

    if 'ltc_review' in request.POST:
        print(" *** LTC Review submit *** ")
        app_id = request.POST.get('app_id')
        # verify that app_id is not changed, ie untampered
        review_comment = request.POST.get('remarks')
        application = Ltc_application.objects.get(id=app_id)
        application.tracking_info.remarks = review_comment
        application.tracking_info.review_status = 'reviewed'
        application.tracking_info.save()

        # Send notification to admin that new cpda bills are submitted
        establishment_notif(request.user, get_admin(), 'ltc_review_submit')
        messages.success(request, 'Review submitted successfully!')


def generate_cpda_eligible_lists(request):
    active_apps = (Cpda_application.objects
                    .filter(applicant=request.user)
                    .exclude(status='rejected')
                    .exclude(status='finished')
                    .order_by('-request_timestamp'))

    archive_apps = (Cpda_application.objects
                    .filter(applicant=request.user)
                    .exclude(status='requested')
                    .exclude(status='approved')
                    .exclude(status='adjustments_pending')
                    .order_by('-request_timestamp'))
    to_review_apps = (Cpda_application.objects
                    .filter(tracking_info__reviewer_id=request.user)
                    .exclude(status='rejected')
                    .exclude(status='finished')
                    .exclude(status='approved')
                    .filter(tracking_info__review_status='under_review')
                    .order_by('-request_timestamp'))
    for app in to_review_apps:
        app.reviewform = Review_Form(initial={'app_id': app.id})

    form = Cpda_Form()
    bill_forms = {}
    apps = Cpda_application.objects.filter(applicant=request.user).filter(status='approved')
    for app in apps:
        bill_forms[app.id] = Cpda_Bills_Form(initial={'app_id': app.id})

    response = {
        'cpda_form': form,
        'cpda_billforms': bill_forms,
        'cpda_active_apps': active_apps,
        'cpda_archive_apps': archive_apps,
        'cpda_to_review_apps': to_review_apps
    }
    return response


def generate_ltc_eligible_lists(request):
    ltc_info = {}
    ltc_queryset = Ltc_eligible_user.objects.filter(user=request.user)
    ltc_info['eligible'] = ltc_queryset.exists()

    if ltc_info['eligible']:
        ltc_info['years_of_job'] = ltc_queryset.first().get_years_of_job()
        ltc_info['total_ltc_remaining'] = ltc_queryset.first().total_ltc_remaining()
        ltc_info['hometown_ltc_remaining'] = ltc_queryset.first().hometown_ltc_remaining()
        ltc_info['elsewhere_ltc_remaining'] = ltc_queryset.first().elsewhere_ltc_remaining()
        # print (ltc_info)

        active_apps = (Ltc_application.objects
                        .filter(applicant=request.user)
                        .filter(status='requested')
                        .order_by('-request_timestamp'))

        archive_apps = (Ltc_application.objects
                        .filter(applicant=request.user)
                        .exclude(status='requested')
                        .order_by('-request_timestamp'))
        form = Ltc_Form()

    to_review_apps = (Ltc_application.objects
                    .filter(tracking_info__reviewer_id=request.user)
                    .filter(status='requested')
                    .filter(tracking_info__review_status='under_review')
                    .order_by('-request_timestamp'))
    for app in to_review_apps:
        app.reviewform = Review_Form(initial={'app_id': app.id})

    response = {
        'ltc_info': ltc_info,
        'ltc_to_review_apps': to_review_apps
    }
    if ltc_info['eligible']:
        response.update({
            'ltc_form': form,
            'ltc_active_apps': active_apps,
            'ltc_archive_apps': archive_apps
        })
    return response


@login_required(login_url='/accounts/login')
def establishment(request):
    response = {}
    # Check if establishment variables exist, if not create some fields or ask for them
    response.update(initial_checks(request))    

    if is_admin(request) and request.method == "POST": 
        if is_fm(request.POST):
            handle_fm_admin(request)
        if is_cpda(request.POST):
            handle_cpda_admin(request)
        if is_ltc(request.POST):
            handle_ltc_admin(request)

    if is_eligible(request) and request.method == "POST":
        if is_cpda(request.POST):
            handle_cpda_eligible(request)
        if is_ltc(request.POST):
            handle_ltc_eligible(request)

    ############################################################################

    if is_admin(request):
        response.update(generate_fm_admin_lists(request))
        response.update(generate_cpda_admin_lists(request))
        response.update(generate_ltc_admin_lists(request))
        return render(request, 'establishment/establishment.html', response)
    
    if is_eligible(request):
        response.update(generate_cpda_eligible_lists(request))
        response.update(generate_ltc_eligible_lists(request))
    
    return render(request, 'establishment/establishment.html', response)
