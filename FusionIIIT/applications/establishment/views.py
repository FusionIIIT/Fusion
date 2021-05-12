from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from applications.academic_information.models import Curriculum_Instructor
from applications.eis.models import (emp_consultancy_projects,emp_research_projects,
                                        emp_mtechphd_thesis,emp_patents,emp_techtransfer,
                                            emp_published_books,emp_confrence_organised,
                                            emp_achievement,emp_event_organized)
from django.db.models import Avg, Count, Min, Sum,Q
from datetime import datetime,date
from .models import *
from .forms import *
import numpy as np
from dateutil.relativedelta import relativedelta

def initial_checks(request):
    return {}


def is_admin(request):
    """
        function to check if the user has designation "admin".
    """
    return request.user == Establishment_variables.objects.select_related('est_admin').first().est_admin


def is_eligible(request):
    return True

def is_hod(request):
    """
        function to check if the user has designation "HOD".
    """
    user_dsg = list(HoldsDesignation.objects.filter(user=request.user))
    if(len(user_dsg)==0):
        return False
    for i in range(len(user_dsg)):
        designation = user_dsg[i].designation.name
        if("HOD" in designation):
            return True
    return False

def is_registrar(request):
    """
        function to check if the user has designation "Registrar".
    """
    user_dsg = list(HoldsDesignation.objects.filter(user=request.user))
    if(len(user_dsg)==0):
        return False
    desg = [des.designation.name for des in user_dsg]
    for d in desg:
        if("Registrar" in d):
            return True
    return False

def is_director(request):
    """
        function to check if the user has designation "Director".
    """
    user_dsg = list(HoldsDesignation.objects.filter(user=request.user))
    if(len(user_dsg)==0):
        return False
    desg = [des.designation.name for des in user_dsg]
    for d in desg:
        if("Director" in d):
            return True
    return False

def is_cpda(dictx):
    """
        function to check if the application is CPDA.
    """
    for key in dictx.keys():
        if 'cpda' in key:
            return True
    return False


def is_ltc(dictx):
    """
        function to check if the application is LTC.
    """
    for key in dictx.keys():
        if 'ltc' in key:
            return True
    return False


def is_appraisal(dictx):
    """
        function to check if the application is Appraisal.
    """
    for key in dictx.keys():
        if 'appraisal' in key:
            return True
    return False

def handle_cpda_admin(request):
    """
        Function handles the request of assigning/re-assigning reviewers of CPDA Application.
    """
    app_id = request.POST.get('app_id')
    status = request.POST.get('status')
    status_accept=request.POST.get('accept_status')
    reviewer = request.POST.get('reviewer_id')
    designation = request.POST.get('reviewer_design')
    remarks = request.POST.get('remarks')
    print(status)
    if status is None:
        status=status_accept
    if(status == ''):
        messages.error(request,"Please fill Status!!")
        return
    if status == 'requested' or status == 'adjustments_pending' and status !='':
        if reviewer and designation and app_id:
            # assign the applicaiton to the reviewers
            reviewer_id = User.objects.get(username=reviewer)
            reviewer_design = Designation.objects.filter(name=designation)
            # Getting reviewer designation
            if reviewer_design:
                reviewer_design = reviewer_design[0]
            
            application = Cpda_application.objects.select_related('applicant').get(id=app_id)
            application.tracking_info.current_reviewer_id=1
            application.tracking_info.reviewer_id = reviewer_id
            application.tracking_info.reviewer_design = reviewer_design
            # treat remarks_Rev3 as concatenated rev designation string
            if(application.tracking_info.remarks_rev3 is None):
                application.tracking_info.remarks_rev3=str(reviewer_design)+"#$*&"
            else:
                application.tracking_info.remarks_rev3=application.tracking_info.remarks_rev3+str(reviewer_design)+"#$*&"
            application.tracking_info.remarks = remarks
            #application.tracking_info.remarks_rev1="Not reviewed yet"
            application.tracking_info.review_status = 'under_review'
            application.status=status
            application.tracking_info.save()

            # notify
            messages.success(request, 'Reviewer assigned successfully!')


        else:
            errors = "Please specify a reviewer and their designation."
            # notify error
            messages.error(request, errors)

    elif app_id:
        # update the status of app
        application = Cpda_application.objects.select_related('applicant').get(id=app_id)
        application.tracking_info.remarks = remarks
        if(status=='approve' or status=='reject'):
            application.status= 'finished'
        else:
            application.status = status
        
        application.save()

        # notify
        messages.success(request, 'Status updated successfully!')


def handle_ltc_admin(request):
    """
        Function handles the request of assigning/re-assigning reviewers of LTC Application.
    """
    if 'ltc_assign_form' in request.POST:
        app_id = request.POST.get('app_id')
        status = request.POST.get('status')
        status_accept=request.POST.get('accept_status')
        reviewer = request.POST.get('reviewer_id')
        designation = request.POST.get('reviewer_design')
        remarks = request.POST.get('remarks')
        if status is None:
            status=status_accept
        if(status ==''):
            messages.error(request,'Please fill status!!')
            return
        if status == 'requested' :
            if reviewer and designation and app_id and status != '':
                # assign the app to the reviewer
                reviewer_id = User.objects.get(username=reviewer)
                reviewer_design = Designation.objects.filter(name=designation)
                # Getting reviewer designation
                if reviewer_design:
                    reviewer_design = reviewer_design[0]
                application = Ltc_application.objects.select_related('applicant').get(id=app_id)
                application.tracking_info.reviewer_id = reviewer_id
                if(application.tracking_info.designations is None):
                    application.tracking_info.designations = str(reviewer_design)+"#$*&"
                else:
                    application.tracking_info.designations = str(application.tracking_info.designations)+str(reviewer_design)+"#$*&"
                application.tracking_info.admin_remarks = remarks
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
            application.tracking_info.admin_remarks = remarks
            eligible_ltc_user=Ltc_eligible_user.objects.get(user=application.applicant)
            if(application.is_hometown_or_elsewhere=='hometown'):
                eligible_ltc_user.hometown_ltc_availed+=1
            if(application.is_hometown_or_elsewhere=='elsewhere' ):
                eligible_ltc_user.elsewhere_ltc_availed+=1

            eligible_ltc_user.save()
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
    """
        Function retrieves the admin information and related unreviewed,approved and archived CPDA applications.
    """
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
            temp = Assign_Form(initial={'assign_status': 'requested','app_id': app.id})
            temp.fields["status"]._choices = [
                ('requested', 'Requested'),
                ('approved', 'Approved'),
                ('rejected', 'Rejected')
            ]
            temp.fields["assign_status"]._choices = [
                ('requested', 'Requested'),
                ('approved', 'Approved'),
                ('rejected', 'Rejected')
            ]
            temp.fields["accept_status"]._choices = [
                ('requested', 'Requested'),
                ('approved', 'Approved'),
                ('rejected', 'Rejected')
            ]

        # if status is adjustments_pending:to_assign/reviewed
        else:
            temp = Assign_Form(initial={'assign_status': 'adjustments_pending', 'app_id': app.id})
            temp.fields["status"]._choices = [
                ('adjustments_pending', 'Adjustments Pending'),
                ('approve', 'Approved')
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

    reviewer_remarks={}
    for app in pending_apps:
        rev_list=[]
        if(app.tracking_info.remarks_rev2 is None ):
            break
        remarks=app.tracking_info.remarks_rev2.split('#$*&')
        desig=app.tracking_info.remarks_rev3.split('#$*&')
        for i in range(len(remarks)):
            if(remarks[i]!=''):
                rev_list.append([desig[i],remarks[i]])
        reviewer_remarks[app.tracking_info.application]=rev_list
    response = {
        'admin': True,
        'cpda_pending_apps': pending_apps,
        'cpda_under_review_apps': under_review_apps,
        'cpda_approved_apps': approved_apps,
        'cpda_archived_apps': archived_apps,
        'remarks_list':reviewer_remarks
    }
    return response

def generate_ltc_admin_lists(request):
    """
        Function retrieves the admin information and related unreviewed,approved and archived LTC applications.
    """
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

    availed = (Ltc_availed.objects.filter(ltc__status='requested'))
    to_avail = (Ltc_to_avail.objects.filter(ltc__status='requested'))
    depend = (Dependent.objects.filter(ltc__status='requested'))
    availed_pending = []
    to_avail_pending = []
    depend_pending = []
    availed_under_review = []
    to_avail_under_review = []
    depend_under_review = []

    for app in availed:
        if app.ltc.tracking_info.review_status == 'under_review':
            availed_under_review.append(app)
        else:
            availed_pending.append(app)

    for app in to_avail:
        if app.ltc.tracking_info.review_status == 'under_review':
            to_avail_under_review.append(app)
        else:
            to_avail_pending.append(app)

    for app in depend:
        if app.ltc.tracking_info.review_status == 'under_review':
            depend_under_review.append(app)
        else:
            depend_pending.append(app)

    # combine assign_form object into unreviewed_app object respectively
    for app in unreviewed_apps:
        temp = Assign_Form(initial={'assign_status': 'requested','app_id': app.id})
        temp.fields["status"]._choices = [
            ('requested', 'Requested'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ]
        temp.fields["assign_status"]._choices = [
                ('requested', 'Requested'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ]
        temp.fields["accept_status"]._choices = [
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

    availed_archive = (Ltc_availed.objects.exclude(ltc__status='requested'))
    to_avail_archive = (Ltc_to_avail.objects.exclude(ltc__status='requested'))
    depend_archive = (Dependent.objects.exclude(ltc__status='requested'))

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
    reviewer_remarks={}
    for app in pending_apps:
        rev_list=[]
        if(app.tracking_info.remarks is None):
            break
        remarks=app.tracking_info.remarks.split('#$*&')
        desig=app.tracking_info.designations.split('#$*&')
        for i in range(len(remarks)):
            if(remarks[i]!=''):
                rev_list.append([desig[i],remarks[i]])
        reviewer_remarks[app.tracking_info.application]=rev_list
    print(reviewer_remarks)
    response = {
        'admin': True,
        'ltc_eligible_users': current_eligible_users,
        'ltc_new_eligible_user_form': new_ltc_eligible_user,
        'ltc_pending_apps': pending_apps,
        'ltc_under_review_apps': under_review_apps,
        'ltc_archived_apps': archived_apps,
        'ltc_availed_pending': availed_pending,
        'ltc_to_avail_pending': to_avail_pending,
        'dependent_pending': depend_pending,
        'ltc_availed_under_review': availed_under_review,
        'ltc_to_avail_under_review': to_avail_under_review,
        'dependent_under_review': depend_under_review,
        'ltc_availed_archive': availed_archive,
        'ltc_to_avail_archive': to_avail_archive,
        'dependent_archive': depend_archive,
        'remarks_list':reviewer_remarks
    }
    return response


def handle_cpda_eligible(request):
    """
        Function handles cpda functionalities- CPDA request,adjustments,review and rejection of CPDA applications.
    """
    if 'cpda_request' in request.POST:

        applicant = request.user
        pf_number=1
        if(emp_consultancy_projects.objects.filter(user=request.user).first() is not None):
            pf_number = emp_consultancy_projects.objects.filter(user=request.user).first().pf_no
        else:
            messages.error(request,"Please fill EIS Forms first.")
            return 
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
        application.tracking_info.remarks_rev1 = review_comment
        if(application.tracking_info.remarks_rev2 is None):
            application.tracking_info.remarks_rev2 =str(review_comment)+"#$*&"
        else:
            application.tracking_info.remarks_rev2 =application.tracking_info.remarks_rev2+str(review_comment)+"#$*&"
        application.tracking_info.review_status = 'reviewed'
        application.tracking_info.current_reviewer_id +=1
        application.tracking_info.save()
        # add notif here
        messages.success(request, 'Review submitted successfully!')

    elif 'cpda_reject' in request.POST:
        app_id = request.POST.get('app_id')
        # verify that app_id is not changed, ie untampered
        review_comment = request.POST.get('remarks')
        application = Cpda_application.objects.get(id=app_id)
        application.tracking_info.remarks_rev1 = review_comment +"(Rejected)"
        if(application.tracking_info.remarks_rev2 is None):
            application.tracking_info.remarks_rev2 =str(review_comment)+"(Rejected)"+"#$*&"
        else:
            application.tracking_info.remarks_rev2 =application.tracking_info.remarks_rev2+str(review_comment)+"(Rejected)"+"#$*&"
        application.tracking_info.review_status = 'reviewed'
        application.tracking_info.save()
        # add notif here
        messages.success(request, 'Review submitted successfully!')


def handle_ltc_eligible(request):
    """
        Function handles LTC functionalities- LTC request and review of LTC applications.
    """
    if 'ltc_request' in request.POST:
        applicant = request.user
        pf_number=1
        if(emp_consultancy_projects.objects.filter(user=request.user).first() is not None):
            pf_number = emp_consultancy_projects.objects.filter(user=request.user).first().pf_no
        else:
            messages.error(request,"Please fill EIS Forms first.")
            return 

        basic_pay = request.POST.get('basic_pay')
        leave_start = request.POST.get('leave_start')
        leave_end = request.POST.get('leave_end')
        family_departure_date = request.POST.get('family_departure_date')
        leave_nature = request.POST.get('leave_nature')
        purpose = request.POST.get('purpose')
        leave_type = request.POST.get('leave_type')
        address_during_leave = request.POST.get('address_during_leave')
        phone_number = request.POST.get('phone_number')
        travel_mode = request.POST.get('travel_mode')


        requested_advance = request.POST.get('requested_advance')

        status = 'requested'
        timestamp = datetime.now()

        eligible_ltc_user=Ltc_eligible_user.objects.get(user=applicant)
        ret = relativedelta(datetime.today().date(), eligible_ltc_user.date_of_joining)
        ret=ret.years + ret.months/12 + ret.days/365
        
        
        application = Ltc_application.objects.create(
            # save all
            applicant=applicant,
            pf_number=pf_number,
            basic_pay = basic_pay,
            leave_start = leave_start,
            leave_end = leave_end,
            family_departure_date = family_departure_date,
            leave_nature = leave_nature,
            purpose = purpose,
            is_hometown_or_elsewhere = leave_type,
            address_during_leave = address_during_leave,
            phone_number = phone_number,
            travel_mode = travel_mode,
            requested_advance = requested_advance,
            request_timestamp=timestamp,
            status=status
        )
        # ltc_availed
        count = 1
        while(1):
                name = request.POST.get('Name1'+str(count))
                age = request.POST.get('Age1'+str(count))
                if(name == None):
                    break
                ltc_availed = Ltc_availed.objects.create(
                                ltc = application,
                                name = name,
                                age = age
                )

                count += 1
        # ltc_to_avail
        count = 1
        while(1):
                name = request.POST.get('Name2'+str(count))
                age = request.POST.get('Age2'+str(count))
                if(name == None):
                    break
                ltc_to_avail = Ltc_to_avail.objects.create(
                                ltc = application,
                                name = name,
                                age = age
                )

                count += 1

        # Dependents
        count = 1
        while(1):
                name = request.POST.get('Name3'+str(count))
                age = request.POST.get('Age3'+str(count))
                depend = request.POST.get('Why fully dependent'+str(count))
                if(name == None):
                    break
                dependent = Dependent.objects.create(
                                ltc = application,
                                name = name,
                                age = age,
                                depend = depend
                )

                count += 1


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
        if(application.tracking_info.remarks is None):
            application.tracking_info.remarks =str(review_comment)+"#$*&"
        else:
            application.tracking_info.remarks = str(application.tracking_info.remarks)+str(review_comment)+"#$*&"
        application.tracking_info.review_status = 'reviewed'
        application.tracking_info.save()
        # add notif here
        messages.success(request, 'Review submitted successfully!')



def handle_appraisal(request):
    """
        This function is used to handle various requests in the
        Appraisal module.
        request: HttpRequest object that contains metadata of
                 Appraisal requests.
    """
    # Condition to handle the Appraisal Request generated from
    # the faculty end by submitting a form.
    if 'appraisal_request' in request.POST:
        applicant = request.user
        # Query to find the designation of the user
        user_dsg = list(HoldsDesignation.objects.filter(user=request.user))
        designation = user_dsg[0].designation
        # Query to find the department/discipline of the user
        user_dep = list(ExtraInfo.objects.filter(user=request.user))
        discipline = user_dep[0].department
        # handling form data
        knowledge_field = request.POST.get('specific_field_knowledge')
        research_interest = request.POST.get('current_research_interest')
        status = 'requested'
        timestamp = datetime.now()
        other_research_element = request.POST.get('other_research_element')
        publications = request.POST.get('publications')
        conferences_meeting_attended = request.POST.get('conferences_meeting_attended')
        conferences_meeting_organized = request.POST.get('conferences_meeting_organized')
        admin_assign = request.POST.get('admin_assign')
        sevice_to_ins = request.POST.get('sevice_to_ins')
        extra_info = request.POST.get('extra_info')
        faculty_comments = request.POST.get('faculty_comments')
        start_date = date.fromisoformat(request.POST.get('start_date'))
        end_date   = date.fromisoformat(request.POST.get('end_date'))
        # Creating Appraisal Object
        application = Appraisal.objects.create(
                applicant = applicant,
                designation = designation,
                discipline = discipline,
                knowledge_field = knowledge_field,
                research_interest = research_interest,
                status = status,
                timestamp = timestamp,
                other_research_element = other_research_element,
                publications = publications,
                conferences_meeting_attended = conferences_meeting_attended,
                conferences_meeting_organized = conferences_meeting_organized,
                admin_assign = admin_assign,
                sevice_to_ins = sevice_to_ins,
                extra_info = extra_info,
                faculty_comments = faculty_comments,
                start_date = start_date,
                end_date = end_date
        )
        # NewCoursesOffered
        count = 1
        while(1):
            course_name = request.POST.get('Course-Name1.1.2'+str(count))
            course_num = request.POST.get('Course Number1.1.2'+str(count))
            UGorPG = request.POST.get('UG/PG1.1.2'+str(count))
            tutorial_hrs_wk = request.POST.get('Tutorial (Hours/week)1.1.2'+str(count))
            year = request.POST.get('YEAR1.1.2'+str(count))
            semester = request.POST.get('Semester1.1.2'+str(count))
            if(semester == None):
                break
            new_course = NewCoursesOffered.objects.create(
                            appraisal = application,
                            course_name = course_name,
                            course_num = course_num,
                            ug_or_pg = UGorPG,
                            tutorial_hrs_wk = tutorial_hrs_wk,
                            year = year,
                            semester = semester
            )
    
            count += 1
    
    
        # NewCourseMaterial
        count = 1
        while(1):
            course_name = request.POST.get('Course-Name' + '1.1.3' + str(count))
            course_num = request.POST.get('Course Number' + '1.1.3' + str(count))
            ug_or_pg = request.POST.get('UG/PG' + '1.1.3' + str(count))
            activity_type = request.POST.get('Type of Activity' + '1.1.3' + str(count))
            availiability = request.POST.get('Web/Public' + '1.1.3' + str(count))
            if(course_num == None):
                break
    
            new_courses_material = NewCourseMaterial.objects.create(
                                    appraisal = application,
                                    course_name = course_name,
                                    course_num = course_num,
                                    ug_or_pg = ug_or_pg,
                                    activity_type = activity_type,
                                    availiability = availiability
            )
    
            count += 1
        
        # Finding the user with designation "HOD" of the department to which the applicant belongs.
        user_info = ExtraInfo.objects.filter(user = applicant)
        user_info = user_info[0]
        designation = None
        if(user_info.department.name == 'CSE'):
            designation = Designation.objects.filter(name = 'CSE HOD')
        elif(user_info.department.name == 'ECE'):
            designation = Designation.objects.filter(name = 'HOD (ECE)')
        elif(user_info.department.name == 'ME'):
            designation = Designation.objects.filter(name = 'HOD (ME)')
        elif(user_info.department.name == 'Design'):
            designation = Designation.objects.filter(name = 'HOD (Design)')
        else:
            designation = Designation.objects.filter(name = 'HOD (NS)')
        holds_designation = HoldsDesignation.objects.filter(designation = designation[0])
        hod = holds_designation[0].user
        # Finding the user with designation "Director"
        designation = Designation.objects.filter(name = 'Director')
        holds_designation = HoldsDesignation.objects.filter(designation = designation[0])
        director = holds_designation[0].user
        # Creating AppraisalRequest Object to track the application
        appraisal_request = AppraisalRequest.objects.create(
                appraisal = application,
                hod = hod,
                director = director
        )
        messages.success(request, 'Appraisal Request sent successfully!')
        return application
    # Condition to handle the Appraisal Review Request generated from
    # the HOD end by reviewing a application.
    if 'hod_appraisal_review' in request.POST:
        app_id = int(request.POST.get('app_id'))
        review_comment = request.POST.get('remarks_hod')
        result = request.POST.get('result')
        application = Appraisal.objects.get(id=app_id)
        request_object = AppraisalRequest.objects.filter(appraisal = application)
        appraisal_track = request_object[0]
        appraisal_track.remark_hod = review_comment
        appraisal_track.status_hod = result
        appraisal_track.save()
        messages.success(request, 'Review submitted successfully!')
    # Condition to handle the Appraisal Review Request generated from
    # the Director end by reviewing a application.
    if 'director_appraisal_review' in request.POST:
        app_id = int(request.POST.get('app_id'))
        review_comment = request.POST.get('remarks_director')
        result = request.POST.get('result')
        application = Appraisal.objects.select_related('applicant').get(id=app_id)
        application.status = "Processed"
        request_object = AppraisalRequest.objects.select_related('appraisal').filter(appraisal = application)
        appraisal_track = request_object[0]
        appraisal_track.remark_director = review_comment
        appraisal_track.status_director = result
        appraisal_track.save()
        application.save()



def generate_cpda_eligible_lists(request):
    """
        Function retrieves the eligible user information and related unreviewed,approved and archived CPDA applications.
    """
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
                    .filter(Q(tracking_info__reviewer_id=request.user))
                    .exclude(status='rejected')
                    .exclude(status='finished')
                    .exclude(status='approved')
                    .filter(tracking_info__review_status='under_review')
                    .order_by('-request_timestamp'))

    reviewed_apps= (Cpda_application.objects.select_related('applicant')
                    .filter(Q(tracking_info__reviewer_id=request.user))
                    .order_by('-request_timestamp'))
    reviewer=False
    if(reviewed_apps is not None):
        reviewer=True
    
    for app in to_review_apps:
        app.reviewform = Review_Form(initial={'app_id': app.id})

    pf_number=1234
    if(emp_consultancy_projects.objects.filter(user=request.user).first() is not None):
        pf_number = emp_consultancy_projects.objects.filter(user=request.user).first().pf_no
    form = Cpda_Form(initial={'pf_number':pf_number})
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
    block_period=str(2019+int((np.ceil((today_date.year-2018)/3)-1))*3)+"-"+ str(2018+int(np.ceil((today_date.year-2018)/3))*3)

    #hod=is_hod(request)
    #registrar=is_registrar(request)
    #director=is_director(request)
    
    response = {
        'reviewer':True,
        'cpda_form': form,
        'cpda_billforms': bill_forms,
        'cpda_active_apps': active_apps,
        'cpda_archive_apps': archive_apps,
        'cpda_to_review_apps': to_review_apps,
        'total_advance_by_user':advance_taken,
        'remaining_advance': advance_avail,
        'block_period': block_period,
        'cpda_reviewed_apps': reviewed_apps,
        'pf':pf_number
    }
    return response


def generate_ltc_eligible_lists(request):
    """
        Function retrieves the eligible user information and related unreviewed,approved and archived LTC applications.
    """
    ltc_info = {}
    ltc_queryset = Ltc_eligible_user.objects.select_related('user').filter(user=request.user)
    ltc_info['eligible'] = ltc_queryset.exists()
    less_than_1_year=False

    if ltc_info['eligible']:
        ltc_info['years_of_job'] = ltc_queryset.first().get_years_of_job()
        ltc_info['total_ltc_remaining'] = ltc_queryset.first().total_ltc_remaining()
        ltc_info['hometown_ltc_remaining'] = ltc_queryset.first().hometown_ltc_remaining()
        ltc_info['elsewhere_ltc_remaining'] = ltc_queryset.first().elsewhere_ltc_remaining()


        if(float(ltc_info['years_of_job'])<1):
            ltc_info['eligible']=False
            less_than_1_year=True
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

        availed_active = (Ltc_availed.objects.filter(ltc__applicant=request.user).filter(ltc__status='requested'))
        to_avail_active = (Ltc_to_avail.objects.filter(ltc__applicant=request.user).filter(ltc__status='requested'))
        depend_active = (Dependent.objects.filter(ltc__applicant=request.user).filter(ltc__status='requested'))
        availed_archived = (Ltc_availed.objects.filter(ltc__applicant=request.user).exclude(ltc__status='requested'))
        to_avail_archived = (Ltc_to_avail.objects.filter(ltc__applicant=request.user).exclude(ltc__status='requested'))
        depend_archived = (Dependent.objects.filter(ltc__applicant=request.user).exclude(ltc__status='requested'))
        pf_number=1234
        if(emp_consultancy_projects.objects.filter(user=request.user).first() is not None):
            pf_number = emp_consultancy_projects.objects.filter(user=request.user).first().pf_no
        form = Ltc_Form(initial={'pf_number':pf_number})
    pf_number=1234
    to_review_apps = (Ltc_application.objects
                    .filter(tracking_info__reviewer_id=request.user)
                    .filter(status='requested')
                    .filter(tracking_info__review_status='under_review')
                    .order_by('-request_timestamp'))

    availed_review = (Ltc_availed.objects.filter(ltc__tracking_info__reviewer_id=request.user).filter(ltc__status='requested').filter(ltc__tracking_info__review_status='under_review'))
    to_avail_review = (Ltc_to_avail.objects.filter(ltc__tracking_info__reviewer_id=request.user).filter(ltc__status='requested').filter(ltc__tracking_info__review_status='under_review'))
    depend_review = (Dependent.objects.filter(ltc__tracking_info__reviewer_id=request.user).filter(ltc__status='requested').filter(ltc__tracking_info__review_status='under_review'))
    for app in to_review_apps:
        app.reviewform = Review_Form(initial={'app_id': app.id})
    #if not present
    
    response = {
        'ltc_info': ltc_info,
        'ltc_to_review_apps': to_review_apps,
        'ltc_availed_review': availed_review,
        'ltc_to_avail_review': to_avail_review,
        'dependent_review': depend_review,
        'lessthan1year': less_than_1_year,
        'pf':pf_number
    }
    
    if ltc_info['eligible']:
        response.update({
            'ltc_form': form,
            'ltc_active_apps': active_apps,
            'ltc_archive_apps': archive_apps,
            'ltc_availed_active': availed_active,
            'ltc_to_avail_active': to_avail_active,
            'dependent_active': depend_active,
            'ltc_availed_archived': availed_archived,
            'ltc_to_avail_archived': to_avail_archived,
            'dependent_archived': depend_archived
        })
    return response


def generate_appraisal_lists(request):
    """
        Generating JSON object to get data from the front-end.
    """
    response = {}
    user_courses = []
    course_objects = Curriculum_Instructor.objects.all()
    for course in course_objects:
        if(course.instructor_id.user == request.user):
            user_courses.append(course)
    consultancy_projects = emp_consultancy_projects.objects.filter(user = request.user)
    research_projects = emp_research_projects.objects.filter(user = request.user)
    thesis = emp_mtechphd_thesis.objects.filter(user = request.user)
    patents = emp_patents.objects.filter(user = request.user)
    tech_transfer = emp_techtransfer.objects.filter(user = request.user)
    publications = emp_published_books.objects.filter(user = request.user)
    conferences = emp_confrence_organised.objects.filter(user = request.user)
    achievments = emp_achievement.objects.filter(user = request.user)
    events = emp_event_organized.objects.filter(user = request.user)
    active_apps = (Appraisal.objects.select_related('applicant').filter(applicant=request.user).exclude(status='Processed').order_by('-timestamp'))
    archive_apps = Appraisal.objects.select_related('applicant').filter(applicant=request.user).exclude(status='requested').order_by('-timestamp')
    request_active = (AppraisalRequest.objects.select_related('appraisal').filter(appraisal__applicant=request.user).filter(appraisal__status='requested'))
    request_archived = (AppraisalRequest.objects.select_related('appraisal').filter(appraisal__applicant=request.user).exclude(appraisal__status='requested'))
    new_courses_offered = NewCoursesOffered.objects.filter(appraisal__applicant=request.user)
    new_courses_material = NewCourseMaterial.objects.filter(appraisal__applicant=request.user)
    response.update({
            'user_courses': user_courses,
            'consultancy_projects': consultancy_projects,
            'research_projects': research_projects,
            'thesis': thesis,
            'patents': patents,
            'tech_transfer': tech_transfer,
            'publications': publications,
            'conferences': conferences,
            'achievments': achievments,
            'events': events,
            'appraisal_active_apps':active_apps,
            'appraisal_archive_apps':archive_apps,
            'appraisal_requests_active':request_active,
            'appraisal_requests_archived':request_archived,
            'new_courses_offered': new_courses_offered,
            'new_courses_material': new_courses_material,
            'start_date': False,
            'end_date': False
    })
    return response


def generate_appraisal_lists_hod(request):
    """
        Generating JSON object to get data from the front-end for user
        with designation "HOD".
    """
    response = {}
    review_apps_hod = AppraisalRequest.objects.select_related('appraisal').filter(hod = request.user).filter(status_hod = 'pending')
    reviewed_apps_hod = AppraisalRequest.objects.select_related('appraisal').filter(hod = request.user).exclude(status_hod = 'pending')
    course_objects_all = Curriculum_Instructor.objects.all()
    consultancy_projects_all = emp_consultancy_projects.objects.all()
    research_projects_all = emp_research_projects.objects.all()
    thesis_all = emp_mtechphd_thesis.objects.all()
    events_all = emp_event_organized.objects.all()
    patents_all = emp_patents.objects.all()
    tech_transfer_all = emp_techtransfer.objects.all()
    publications_all = emp_published_books.objects.all()
    conferences_all = emp_confrence_organised.objects.all()
    achievments_all = emp_achievement.objects.all()
    appraisal_all = Appraisal.objects.select_related('applicant').all()
    new_courses_offered_all = NewCoursesOffered.objects.all()
    new_courses_material_all = NewCourseMaterial.objects.all()
    response.update({
        'hod': True,
        'reviewed_apps_hod': reviewed_apps_hod,
        'course_objects_all': course_objects_all,
        'review_apps_hod': review_apps_hod,
        'thesis_all': thesis_all,
        'events_all': events_all,
        'patents_all': patents_all,
        'tech_transfer_all': tech_transfer_all,
        'publications_all': publications_all,
        'conferences_all': conferences_all,
        'achievments_all': achievments_all,
        'consultancy_projects_all': consultancy_projects_all,
        'research_projects_all': research_projects_all,
        'appraisal_all': appraisal_all,
        'new_courses_offered_all': new_courses_offered_all,
        'new_courses_material_all': new_courses_material_all
    })
    return response


def generate_appraisal_lists_director(request):
    """
        Generating JSON object to get data from the front-end for user
        with designation "Director".
    """
    response = {}
    review_apps_director = AppraisalRequest.objects.select_related('appraisal').filter(director = request.user).filter(status_director = 'pending').exclude(status_hod = 'pending')
    reviewed_apps_director = AppraisalRequest.objects.select_related('appraisal').filter(director = request.user).exclude(status_director = 'pending')
    course_objects_all = Curriculum_Instructor.objects.all()
    consultancy_projects_all = emp_consultancy_projects.objects.all()
    research_projects_all = emp_research_projects.objects.all()
    thesis_all = emp_mtechphd_thesis.objects.all()
    events_all = emp_event_organized.objects.all()
    patents_all = emp_patents.objects.all()
    tech_transfer_all = emp_techtransfer.objects.all()
    publications_all = emp_published_books.objects.all()
    conferences_all = emp_confrence_organised.objects.all()
    achievments_all = emp_achievement.objects.all()
    appraisal_all = Appraisal.objects.select_related('applicant').all()
    new_courses_offered_all = NewCoursesOffered.objects.all()
    new_courses_material_all = NewCourseMaterial.objects.all()
    response.update({
        'director': True,
        'course_objects_all': course_objects_all,
        'review_apps_director': review_apps_director,
        'reviewed_apps_director': reviewed_apps_director,
        'thesis_all': thesis_all,
        'events_all': events_all,
        'patents_all': patents_all,
        'tech_transfer_all': tech_transfer_all,
        'publications_all': publications_all,
        'conferences_all': conferences_all,
        'achievments_all': achievments_all,
        'consultancy_projects_all': consultancy_projects_all,
        'research_projects_all': research_projects_all,
        'appraisal_all': appraisal_all,
        'new_courses_offered_all': new_courses_offered_all,
        'new_courses_material_all': new_courses_material_all
    })
    return response

def generate_appraisal_lists_admin(request):
    """
        Generating JSON object to get data from the front-end for user
        with designation "Admin".
    """
    response = {}
    appraisal_requests = AppraisalRequest.objects.exclude(status_director = 'pending').exclude(status_hod = 'pending')
    course_objects_all = Curriculum_Instructor.objects.all()
    consultancy_projects_all = emp_consultancy_projects.objects.all()
    research_projects_all = emp_research_projects.objects.all()
    thesis_all = emp_mtechphd_thesis.objects.all()
    events_all = emp_event_organized.objects.all()
    patents_all = emp_patents.objects.all()
    tech_transfer_all = emp_techtransfer.objects.all()
    publications_all = emp_published_books.objects.all()
    conferences_all = emp_confrence_organised.objects.all()
    achievments_all = emp_achievement.objects.all()
    appraisal_all = Appraisal.objects.select_related('applicant').all()
    new_courses_offered_all = NewCoursesOffered.objects.all()
    new_courses_material_all = NewCourseMaterial.objects.all()
    for em in appraisal_requests:
        print(em)
    response.update({
        'admin': True,
        'course_objects_all': course_objects_all,
        'appraisal_requests': appraisal_requests,
        'thesis_all': thesis_all,
        'events_all': events_all,
        'patents_all': patents_all,
        'tech_transfer_all': tech_transfer_all,
        'publications_all': publications_all,
        'conferences_all': conferences_all,
        'achievments_all': achievments_all,
        'consultancy_projects_all': consultancy_projects_all,
        'research_projects_all': research_projects_all,
        'appraisal_all': appraisal_all,
        'new_courses_offered_all': new_courses_offered_all,
        'new_courses_material_all': new_courses_material_all
    })
    return response
def update_appraisal_lists(request):
    start = request.POST.get('start_date')
    start_date = date.fromisoformat(start)
    end = request.POST.get('end_date')
    end_date = date.fromisoformat(end)
    
    response = {}
    achievments = emp_achievement.objects.filter(user = request.user)
    achievments_date = []
    for obj in achievments:
        if(start_date <= obj.achievment_date <= end_date):
            achievments_date.append(obj)
    consultancy_projects = emp_consultancy_projects.objects.filter(user = request.user)
    consultancy_projects_date = []
    for obj in consultancy_projects:
        if(start_date <= obj.start_date <= end_date or start_date <= obj.end_date <= end_date):
            consultancy_projects_date.append(obj)
    research_projects = emp_research_projects.objects.filter(user = request.user)
    research_projects_date = []
    for obj in research_projects:
        if(start_date <= obj.start_date <= end_date
                or start_date <= obj.finish_date <= end_date
                or start_date <= obj.date_submission <= end_date):
            research_projects_date.append(obj)
    thesis = emp_mtechphd_thesis.objects.filter(user = request.user)
    thesis_date = []
    for obj in thesis:
        if(start_date <= obj.start_date <= end_date or start_date <= obj.end_date <= end_date):
            thesis_date.append(obj)
    patents = emp_patents.objects.filter(user = request.user)
    patents_date = []
    for obj in patents:
        if(start_date <= obj.start_date <= end_date or start_date <= obj.end_date <= end_date):
            patents_date.append(obj)
    tech_transfer = emp_techtransfer.objects.filter(user = request.user)
    tech_transfer_date = []
    for obj in tech_transfer:
        if(start_date <= obj.start_date <= end_date or start_date <= obj.end_date <= end_date):
            tech_transfer_date.append(obj)
    publications = emp_published_books.objects.filter(user = request.user)
    publications_date = []
    for obj in publications:
        if(start_date <= obj.publication_date <= end_date):
            publications_date.append(obj)
    conferences = emp_confrence_organised.objects.filter(user = request.user)
    conferences_date = []
    for obj in conferences:
        if(start_date <= obj.start_date <= end_date or start_date <= obj.end_date <= end_date):
            conferences_date.append(obj)
    
    events = emp_event_organized.objects.filter(user = request.user)
    events_date = []
    for obj in events:
        if(start_date <= obj.start_date <= end_date or start_date <= obj.end_date <= end_date):
            events_date.append(obj)
    response.update({
            'achievments': achievments_date,
            'consultancy_projects': consultancy_projects_date,
            'research_projects': research_projects_date,
            'thesis': thesis_date,
            'patents': patents_date,
            'tech_transfer': tech_transfer_date,
            'publications': publications_date,
            'conferences': conferences_date,
            'events': events_date,
            'start_date': start,
            'end_date': end
    })
    return response

@login_required(login_url='/accounts/login')
def establishment(request):
    """
        Renders HR1 home page.
    """
    return render(request, 'establishment/hr1.html')


@login_required(login_url='/accounts/login')
def cpda(request):
    """
        Function handles generation and submission of CPDA form.
    """
    response = {}
    # Check if establishment variables exist, if not create some fields or ask for them
    response.update(initial_checks(request))
    # Submission of CPDA Form
    if is_admin(request) and request.method == "POST":
            handle_cpda_admin(request)
        
    if is_eligible(request) and request.method == "POST":
            handle_cpda_eligible(request)

    # Genration of CPDA Form
    if is_admin(request):
        response.update(generate_cpda_admin_lists(request))

    if is_eligible(request):
        response.update(generate_cpda_eligible_lists(request))

    response.update({'cpda':True,'ltc':False,'appraisal':False,'leave':False}) 
      
    return render(request, 'establishment/hr1_form.html', response)

@login_required(login_url='/accounts/login')
def ltc(request):
    """
        Function handles generation and submission of LTC form.
    """
    response = {}
    # Check if establishment variables exist, if not create some fields or ask for them
    response.update(initial_checks(request))

    # Submission of LTC Form
    if is_admin(request) and request.method == "POST":
        handle_ltc_admin(request)

    if is_eligible(request) and request.method == "POST":
        handle_ltc_eligible(request)
    
    # Genration of LTC Form
    if is_admin(request):
        response.update(generate_ltc_admin_lists(request))

    if is_eligible(request):
        response.update(generate_ltc_eligible_lists(request))

    response.update({'cpda':False,'ltc':True,'appraisal':False,'leave':False})
    return render(request, 'establishment/hr1_form.html', response)

@login_required(login_url='/accounts/login')
def appraisal(request):
    """
        Function handles generation and submission of Appraisal form.
    """
    response = {}
    # Check if establishment variables exist, if not create some fields or ask for them
    app = None
    response.update(initial_checks(request))
    if is_eligible(request) and request.method == "POST":
        app = handle_appraisal(request)
    if is_eligible(request):
        response.update(generate_appraisal_lists(request))
    if is_eligible(request) and request.method == "POST" and 'filter_eis_details' in request.POST:
        response.update(update_appraisal_lists(request))
    # If user has designation "HOD"
    if is_hod(request):
        response.update(generate_appraisal_lists_hod(request))
    # If user has designation "Director"
    if is_director(request):
        response.update(generate_appraisal_lists_director(request))

    if is_admin(request):
        response.update(generate_appraisal_lists_admin(request))
    response.update({'cpda':False,'ltc':False,'appraisal':True,'leave':False})
    
    return render(request, 'establishment/hr1_form.html', response)
