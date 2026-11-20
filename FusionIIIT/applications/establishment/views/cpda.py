from datetime import datetime, date
import numpy as np
from django.shortcuts import get_object_or_404, render
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Avg, Count, Min, Sum, Q
from django.http import HttpResponse, HttpResponseRedirect
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from applications.eis.models import emp_consultancy_projects
from applications.establishment.models import (
    Cpda_application, Cpda_tracking, CpdaBalance, Cpda_bill,
    Establishment_variables
)
from applications.establishment.forms import Cpda_Form, Cpda_Bills_Form, Assign_Form, Review_Form
from .permissions import is_admin, is_eligible, is_hod, is_director, is_faculty, is_staff

@transaction.atomic
def handle_cpda_admin(request):
    """
        Function handles the request of assigning/re-assigning reviewers of CPDA Application.
    """
    if 'cpda_assign_form' in request.POST:
        try:
            app_id = request.POST.get('app_id')
            remarks = request.POST.get('remarks')        
            application = Cpda_application.objects.select_related('applicant').get(id=app_id)
            application.tracking_info.current_reviewer_id+=1
            application.tracking_info.remarks_rev2 = remarks
            application.tracking_info.review_status = 'under_review'
            application.tracking_info.save()
            messages.success(request, 'Application verification successful!')
        except Exception as e:
            messages.error(request, e)


def generate_cpda_hod_admin_lists(request):
    """
        Function retrieves the admin information and related unreviewed,approved and archived CPDA applications.
    """
    try:
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
    except Exception as e:
            messages.error(request,e)


def generate_cpda_admin_lists(request):
    """
        Function retrieves the admin information and related unreviewed,approved and archived CPDA applications.
    """
    try:
        to_review_apps = (Cpda_application.objects
                        .select_related('applicant')
                        .filter((Q(tracking_info__reviewer_id=request.user)&Q(tracking_info__current_reviewer_id=1)) 
                        | (Q(tracking_info__reviewer_id2=request.user) & Q(tracking_info__current_reviewer_id=2)) 
                        | (Q(tracking_info__reviewer_id3=request.user)&Q(tracking_info__current_reviewer_id=3)))
                        .exclude(status='rejected')
                        .exclude(status='finished')
                        .exclude(status='approved')
                        .filter(tracking_info__review_status='under_review')
                        .order_by('-request_timestamp'))
    
        reviewed_apps= (Cpda_application.objects.select_related('applicant')
                        .filter(Q(tracking_info__reviewer_id=request.user,tracking_info__current_reviewer_id__gte=2) |
                                Q(tracking_info__reviewer_id2=request.user,tracking_info__current_reviewer_id__gte=3) |
                                Q(tracking_info__reviewer_id3=request.user,tracking_info__current_reviewer_id__gte=4))
                        .order_by('-request_timestamp'))
        
        for app in to_review_apps:
            app.reviewform = Review_Form(initial={'app_id': app.id})
            

            
        bill_forms = {}
        apps = Cpda_application.objects.select_related('applicant').filter(applicant=request.user).filter(status='approved')
        for app in apps:
            bill_forms[app.id] = Cpda_Bills_Form(initial={'app_id': app.id})

        response = {
            'admin':True,
            'cpda_billforms': bill_forms,
            'cpda_to_review_apps': to_review_apps,
            'cpda_reviewed_apps': reviewed_apps,
        }
        return response
    except Exception as e:
            messages.error(request,e)


@transaction.atomic
def handle_cpda_eligible(request):
    """
        Function handles cpda functionalities- CPDA request,adjustments,review and rejection of CPDA applications.
    """
    if 'cpda_request' in request.POST:
        try:
            applicant = request.user
            # pf_number=1
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
            # finding HOD according to department of eligible
            user_info = ExtraInfo.objects.filter(user=applicant).select_related('department').first()
            hod_map = {
                'CSE': 'CSE HOD',
                'ECE': 'HOD (ECE)',
                'ME': 'HOD (ME)',
                'Design': 'HOD (Design)',
            }
            dept_name = user_info.department.name if user_info and user_info.department else ''
            target_hod_name = hod_map.get(dept_name, 'HOD (NS)')
            hod_desig = Designation.objects.filter(name=target_hod_name).first()
            hod_holding = HoldsDesignation.objects.filter(designation=hod_desig).first() if hod_desig else None
            hod = hod_holding.user if hod_holding else None

            # finding HR Admin
            est_var = Establishment_variables.objects.select_related('est_admin').first()
            hr_admin = est_var.est_admin if est_var else None
            hr_admin_design = Designation.objects.filter(name='hradmin').first()

            # finding Director
            dir_desig = Designation.objects.filter(name='Director').first()
            dir_holding = HoldsDesignation.objects.filter(designation=dir_desig).first() if dir_desig else None
            director = dir_holding.user if dir_holding else None

            
            # next 3 lines are working magically, DON'T TOUCH THEM
            track = Cpda_tracking.objects.create(
                application = application,
                review_status = 'under_review',
                reviewer_id=hod,
                reviewer_id2=hr_admin,
                reviewer_id3=director,
                current_reviewer_id=1,
                remarks_rev1='Not reviewed yet',
                remarks_rev2='Not reviewed yet',
                remarks_rev3='Not reviewed yet',
                reviewer_design=hod_desig,
                reviewer_design2=hr_admin_design,
                reviewer_design3=dir_desig
                )
            # add notif here
            messages.success(request, 'Request sent successfully!')
        except Exception as e:
            messages.error(request,e)

    elif 'cpda_adjust' in request.POST:
        try:
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
            application.tracking_info.current_reviewer_id=1
            application.tracking_info.remarks_rev1="Not Reviewed yet"
            application.tracking_info.remarks_rev2="Not Reviewed yet"
            application.tracking_info.remarks_rev3="Not Reviewed yet"
            application.status = 'adjustments_pending'
            application.tracking_info.bill=upload_file
            application.save()

            # get tracking info of a particular application
            application.tracking_info.review_status = 'under_review'
            application.tracking_info.save()
            # add notif here
            messages.success(request, 'Bills submitted successfully!')
        except Exception as e:
            messages.error(request,e)

    elif 'cpda_review' in request.POST:
        try:
            app_id = request.POST.get('app_id')
            # verify that app_id is not changed, ie untampered
            review_comment = request.POST.get('remarks')
            application = Cpda_application.objects.get(id=app_id)
            cpda_bal=CpdaBalance.objects.get(user=application.applicant)
            
            if(application.tracking_info.current_reviewer_id==1):
                application.tracking_info.remarks_rev1 = review_comment
            elif(application.tracking_info.current_reviewer_id==2):
                application.tracking_info.remarks_rev2 = review_comment
            else:
                application.tracking_info.remarks_rev3 = review_comment

            if(application.tracking_info.current_reviewer_id==3):
                application.tracking_info.review_status = 'reviewed'
                if(application.status=='adjustments_pending'):
                    application.status='finished'
                    if((application.total_bills_amount- application.requested_advance)>0):
                        cpda_bal.cpda_balance=cpda_bal.cpda_balance-(application.total_bills_amount-application.requested_advance)
                    else:
                        cpda_bal.cpda_balance=cpda_bal.cpda_balance+(application.total_bills_amount-application.requested_advance)
                else:
                    cpda_bal.cpda_balance=cpda_bal.cpda_balance-application.requested_advance
                    application.status='approved'
            application.tracking_info.current_reviewer_id +=1
            application.tracking_info.save()
            application.save()
            cpda_bal.save()
            # add notif here
            messages.success(request, 'Review submitted successfully!')
        except Exception as e:
            messages.error(request,e)

    elif 'cpda_reject' in request.POST:
        try:
            app_id = request.POST.get('app_id')
            # verify that app_id is not changed, ie untampered
            review_comment = request.POST.get('remarks')
            application = Cpda_application.objects.get(id=app_id)
            if(application.tracking_info.current_reviewer_id==1):
                application.tracking_info.remarks_rev1 = review_comment +"(Rejected)"
            elif(application.tracking_info.current_reviewer_id==2):
                application.tracking_info.remarks_rev2 = review_comment +"(Rejected)"
            else:
                application.tracking_info.remarks_rev3 = review_comment +"(Rejected)"
            application.tracking_info.review_status = 'reviewed'
            application.tracking_info.save()
            # add notif here
            messages.success(request, 'Review submitted successfully!')
        except Exception as e:
            messages.error(request,e)


def generate_cpda_eligible_lists(request):
    """
        Function retrieves the eligible user information and related unreviewed,approved and archived CPDA applications.
    """
    try:
        active_apps = (Cpda_application.objects
                        .select_related('applicant')
                        .filter(applicant=request.user)
                        .exclude(status='rejected')
                        .exclude(status='approved')
                        .exclude(status='finished')
                        .order_by('-request_timestamp'))

        archive_apps = (Cpda_application.objects
                        .select_related('applicant')
                        .filter(applicant=request.user)
                        .exclude(status='requested')
                        .exclude(status='adjustments_pending')
                        .order_by('-request_timestamp'))

        to_review_apps = (Cpda_application.objects
                        .select_related('applicant')
                        .filter((Q(tracking_info__reviewer_id=request.user)&Q(tracking_info__current_reviewer_id=1)) 
                        | (Q(tracking_info__reviewer_id2=request.user) & Q(tracking_info__current_reviewer_id=2)) 
                        | (Q(tracking_info__reviewer_id3=request.user)&Q(tracking_info__current_reviewer_id=3)))
                        .exclude(status='rejected')
                        .exclude(status='finished')
                        .exclude(status='approved')
                        .filter(tracking_info__review_status='under_review')
                        .order_by('-request_timestamp'))
        reviewed_apps= (Cpda_application.objects.select_related('applicant')
                        .filter(Q(tracking_info__reviewer_id=request.user,tracking_info__current_reviewer_id__gte=2) |
                                Q(tracking_info__reviewer_id2=request.user,tracking_info__current_reviewer_id__gte=3) |
                                Q(tracking_info__reviewer_id3=request.user,tracking_info__current_reviewer_id__gte=4))
                        .order_by('-request_timestamp'))
        
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

        try:
            cpda_balance=CpdaBalance.objects.get(user=request.user)
            advance_avail=cpda_balance.cpda_balance
            advance_taken=300000-advance_avail
        except:
            cpda_bal=CpdaBalance.objects.create(user=request.user)
            advance_avail=300000
            advance_taken=0

        today_date=date.today()
        block_period=str(2019+int((np.ceil((today_date.year-2018)/3)-1))*3)+"-"+ str(2018+int(np.ceil((today_date.year-2018)/3))*3)
        hod=is_hod(request)
        #registrar=is_registrar(request)
        director=is_director(request)
        reviewer=False
        if(hod or director):
            reviewer=True
        response = {
            'director':director,
            'reviewer':reviewer,
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
    except Exception as e:
            messages.error(request,e)    
