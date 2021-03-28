from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from django.db.models import Avg, Count, Min, Sum
from datetime import datetime,date
from .models import *
from .forms import *
import numpy as np

def initial_checks(request):
    return {}


def is_admin(request):
    return request.user == Establishment_variables.objects.select_related('est_admin').first().est_admin


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
    reviewer2 = request.POST.get('reviewer_id2')
    reviewer3 = request.POST.get('reviewer_id3')
    designation = request.POST.get('reviewer_design')
    designation2 = request.POST.get('reviewer_design2')
    designation3 = request.POST.get('reviewer_design3')
    remarks = request.POST.get('remarks')
    if status == 'requested' or status == 'adjustments_pending':
        if reviewer and reviewer2 and reviewer3 and designation and app_id:
            # assign the app to the reviewer
            reviewer_id = User.objects.get(username=reviewer)
            reviewer_id2 = User.objects.get(username=reviewer2)
            reviewer_id3 = User.objects.get(username=reviewer3)
            reviewer_design = Designation.objects.filter(name=designation)
            reviewer_design2 = Designation.objects.filter(name=designation2)
            reviewer_design3 = Designation.objects.filter(name=designation3)
            # check if the reviewer holds the given designation, if not show error
            if reviewer_design:
                reviewer_design = reviewer_design[0]
            if reviewer_design2:
                reviewer_design2 = reviewer_design2[0]
            if reviewer_design3:
                reviewer_design3 = reviewer_design3[0]
            # if reviewer_design != HoldsDesignation.objects.get(user=reviewer_id):
            #     messages.error(request, 'Reviewer doesn\'t holds the designation you specified!')
            # else:
            application = Cpda_application.objects.select_related('applicant').get(id=app_id)
            application.tracking_info.current_reviewer_id=1
            application.tracking_info.reviewer_id = reviewer_id
            application.tracking_info.reviewer_id2 = reviewer_id2
            application.tracking_info.reviewer_id3 = reviewer_id3
            application.tracking_info.reviewer_design = reviewer_design
            application.tracking_info.reviewer_design2 = reviewer_design2
            application.tracking_info.reviewer_design3 = reviewer_design3
            application.tracking_info.remarks = remarks
            application.tracking_info.remarks_rev1=""
            application.tracking_info.remarks_rev2=""
            application.tracking_info.remarks_rev3=""
            application.tracking_info.review_status = 'under_review'
            application.tracking_info.save()
            
            # add notif
            messages.success(request, 'Reviewer assigned successfully!')
            

        else:
            errors = "Please specify a reviewer and their designation."
            messages.error(request, errors)

    elif app_id:
        # update the status of app
        # verify that app_id is not changed, ie untampered
        application = Cpda_application.objects.select_related('applicant').get(id=app_id)
        application.status = status
        application.save()
        

        # add notif
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
                application = Ltc_application.objects.select_related('applicant').get(id=app_id)
                application.tracking_info.reviewer_id = reviewer_id
                application.tracking_info.reviewer_design = reviewer_design
                application.tracking_info.remarks = remarks
                application.tracking_info.review_status = 'under_review'
                application.tracking_info.save()
                
                # add notif
                messages.success(request, 'Reviewer assigned successfully!')

            else:
                errors = "Please specify a reviewer and their designation."
                messages.error(request, errors)

        elif app_id:
            # update the status of app
            # verify that app_id is not changed, ie untampered
            application = Ltc_application.objects.select_related('applicant').get(id=app_id)
            application.status = status
            application.save()
            # add notif
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

        eligible_user = Ltc_eligible_user.objects.select_related('user').get(user=user_id)
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
        if not Ltc_eligible_user.objects.select_related('user').filter(user=user_id).exists():
            messages.error(request, 'This user already isn\'t eligible for availing LTC')
            return

        eligible_user = Ltc_eligible_user.objects.select_related('user').get(user=user_id)
        eligible_user.delete()
        messages.success(request, 'User successfully removed from eligible LTC users')


def generate_cpda_admin_lists(request):

    # only requested and adjustment_pending
    unreviewed_apps = (Cpda_application.objects
                .select_related('applicant')
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
        
        
    # only approved
    approved_apps = (Cpda_application.objects
                    .select_related('applicant')
                    .filter(status='approved')
                    .order_by('-request_timestamp'))

    # only rejected and finished
    archived_apps = (Cpda_application.objects
                    .select_related('applicant')
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
                .select_related('applicant')
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
        
    # approved and rejected
    archived_apps = (Ltc_application.objects
                    .select_related('applicant')
                    .exclude(status='requested')
                    .order_by('-request_timestamp'))

    current_eligible_users = Ltc_eligible_user.objects.select_related('user').order_by('user')
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
        applicant = request.user
        pf_number = request.POST.get('pf_number')
        purpose = request.POST.get('purpose')
        advance = request.POST.get('advance')
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

        # add notif here
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
        # add notif here
        messages.success(request, 'Bills submitted successfully!')
        
    elif 'cpda_review' in request.POST:
        app_id = request.POST.get('app_id')
        # verify that app_id is not changed, ie untampered
        review_comment = request.POST.get('remarks')
        application = Cpda_application.objects.get(id=app_id)
        if(application.tracking_info.current_reviewer_id==1):
            application.tracking_info.remarks_rev1 = review_comment
        elif(application.tracking_info.current_reviewer_id==2):
            application.tracking_info.remarks_rev2 = review_comment
        else:
            application.tracking_info.remarks_rev3 = review_comment
        if(application.tracking_info.current_reviewer_id==3):
            application.tracking_info.review_status = 'reviewed'
        application.tracking_info.current_reviewer_id +=1
        application.tracking_info.save()
        # add notif here
        messages.success(request, 'Review submitted successfully!')


def handle_ltc_eligible(request):
    if 'ltc_request' in request.POST:
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
        # add notif here
        messages.success(request, 'Request sent successfully!')

    if 'ltc_review' in request.POST:
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
                    .select_related('applicant')
                    .filter(applicant=request.user)
                    .exclude(status='rejected')
                    .exclude(status='finished')
                    .order_by('-request_timestamp'))

    archive_apps = (Cpda_application.objects
                    .select_related('applicant')
                    .filter(applicant=request.user)
                    .exclude(status='requested')
                    .exclude(status='approved')
                    .exclude(status='adjustments_pending')
                    .order_by('-request_timestamp'))
    to_review_apps = (Cpda_application.objects
                    .select_related('applicant')
                    .filter(tracking_info__reviewer_id=request.user).filter(tracking_info__current_reviewer_id=1)
                    .exclude(status='rejected')
                    .exclude(status='finished')
                    .exclude(status='approved')
                    .filter(tracking_info__review_status='under_review')
                    .order_by('-request_timestamp'))
    if not to_review_apps:
        to_review_apps = (Cpda_application.objects.select_related('applicant')
                        .filter(tracking_info__reviewer_id2=request.user).filter(tracking_info__current_reviewer_id=2)
                        .exclude(status='rejected')
                        .exclude(status='finished')
                        .exclude(status='approved')
                        .filter(tracking_info__review_status='under_review')
                        .order_by('-request_timestamp'))
    if not to_review_apps:
        to_review_apps = (Cpda_application.objects.select_related('applicant')
                        .filter(tracking_info__reviewer_id3=request.user).filter(tracking_info__current_reviewer_id=3)
                        .exclude(status='rejected')
                        .exclude(status='finished')
                        .exclude(status='approved')
                        .filter(tracking_info__review_status='under_review')
                        .order_by('-request_timestamp'))
    for app in to_review_apps:
        app.reviewform = Review_Form(initial={'app_id': app.id})

    form = Cpda_Form()
    bill_forms = {}
    apps = Cpda_application.objects.select_related('applicant').filter(applicant=request.user).filter(status='approved')
    for app in apps:
        bill_forms[app.id] = Cpda_Bills_Form(initial={'app_id': app.id})

    advance_took = (Cpda_application.objects
                    .select_related('applicant')
                    .filter(applicant=request.user)
                    .exclude(status='requested')
                    .aggregate(total_advance=Sum('requested_advance')))
    
    if advance_took['total_advance']:
        advance_taken=advance_took['total_advance']
        advance_avail=300000-advance_took['total_advance']
    else:
        advance_taken=0
        advance_avail=300000
    today_date=date.today()
    block_period=str(2018+int((np.ceil((today_date.year-2018)/3)-1))*3)+"-"+ str(2018+int(np.ceil((today_date.year-2018)/3))*3)
    response = {
        'cpda_form': form,
        'cpda_billforms': bill_forms,
        'cpda_active_apps': active_apps,
        'cpda_archive_apps': archive_apps,
        'cpda_to_review_apps': to_review_apps,
        'total_advance_by_user':advance_taken,
        'remaining_advance': advance_avail,
        'block_period': block_period
    }
    return response


def generate_ltc_eligible_lists(request):
    ltc_info = {}
    ltc_queryset = Ltc_eligible_user.objects.select_related('user').filter(user=request.user)
    ltc_info['eligible'] = ltc_queryset.exists()

    if ltc_info['eligible']:
        ltc_info['years_of_job'] = ltc_queryset.first().get_years_of_job()
        ltc_info['total_ltc_remaining'] = ltc_queryset.first().total_ltc_remaining()
        ltc_info['hometown_ltc_remaining'] = ltc_queryset.first().hometown_ltc_remaining()
        ltc_info['elsewhere_ltc_remaining'] = ltc_queryset.first().elsewhere_ltc_remaining()

        active_apps = (Ltc_application.objects
                        .select_related('applicant')
                        .filter(applicant=request.user)
                        .filter(status='requested')
                        .order_by('-request_timestamp'))

        archive_apps = (Ltc_application.objects
                        .select_related('applicant')
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
