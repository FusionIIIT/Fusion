from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation

from datetime import datetime
from .models import *
from .forms import *


def initial_checks(request):
    return {}


def is_admin(request):
    return request.user == Establishment_variables.objects.first().est_admin


def is_eligible(request):
    return True


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
            
            # add notif
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

        # add notif
        messages.success(request, 'Status updated successfully!')


def handle_ltc_admin(request):
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
            
            # add notif
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
        # add notif
        messages.success(request, 'Status updated successfully!')


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
    archived_apps = (Cpda_application.objects
                    .exclude(status='requested')
                    .order_by('-request_timestamp'))

    response = {
        'admin': True,
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

        # add notif here
        messages.success(request, 'Request sent successfully!')

    if 'cpda_adjust' in request.POST:
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
        # add notif here
        messages.success(request, 'Bills submitted successfully!')
        
    if 'cpda_review' in request.POST:
        print(" *** CPDA Review submit *** ")
        app_id = request.POST.get('app_id')
        # verify that app_id is not changed, ie untampered
        review_comment = request.POST.get('remarks')
        application = Cpda_application.objects.get(id=app_id)
        application.tracking_info.remarks = review_comment
        application.tracking_info.review_status = 'reviewed'
        application.tracking_info.save()
        # add notif here
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
        # add notif here
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
        # add notif here
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
    active_apps = (Ltc_application.objects
                    .filter(applicant=request.user)
                    .filter(status='requested')
                    .order_by('-request_timestamp'))

    archive_apps = (Ltc_application.objects
                    .filter(applicant=request.user)
                    .exclude(status='requested')
                    .order_by('-request_timestamp'))
    to_review_apps = (Ltc_application.objects
                    .filter(tracking_info__reviewer_id=request.user)
                    .filter(status='requested')
                    .filter(tracking_info__review_status='under_review')
                    .order_by('-request_timestamp'))
    for app in to_review_apps:
        app.reviewform = Review_Form(initial={'app_id': app.id})

    form = Ltc_Form()
    response = {
        'ltc_form': form,
        'ltc_active_apps': active_apps,
        'ltc_archive_apps': archive_apps,
        'ltc_to_review_apps': to_review_apps
    }
    return response


@login_required(login_url='/accounts/login')
def establishment(request):
    response = {}
    # Check if establishment variables exist, if not create some fields or ask for them
    response = initial_checks(request)

    if is_admin(request) and request.method == "POST": 
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
        response.update(generate_cpda_admin_lists(request))
        response.update(generate_ltc_admin_lists(request))
        return render(request, 'establishment/establishment.html', response)
    
    if is_eligible(request):
        response.update(generate_cpda_eligible_lists(request))
        response.update(generate_ltc_eligible_lists(request))
    
    return render(request, 'establishment/establishment.html', response)
