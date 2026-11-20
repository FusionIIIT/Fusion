from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from django.shortcuts import get_object_or_404, render
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Avg, Count, Min, Sum, Q
from django.http import HttpResponse, HttpResponseRedirect
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation
from applications.eis.models import emp_consultancy_projects
from applications.establishment.models import (
    Ltc_application, Ltc_tracking, Ltc_eligible_user,
    Ltc_availed, Ltc_to_avail, Dependent, Constants
)
from applications.establishment.forms import Ltc_Form, Assign_Form, Review_Form, Ltc_Eligible_Form
from .permissions import is_admin, is_eligible, is_hod, is_director, is_faculty, is_staff

@transaction.atomic
def handle_ltc_admin(request):
    """
        Function handles the request of assigning/re-assigning reviewers of LTC Application.
    """
    
    if 'ltc_assign_form' in request.POST:
        try:
            app_id = request.POST.get('app_id')
            remarks = request.POST.get('remarks')
            # assign the app to the reviewer
            # finding Director safely
            dir_desig = Designation.objects.filter(name='Director').first()
            dir_holding = HoldsDesignation.objects.filter(designation=dir_desig).first() if dir_desig else None
            director = dir_holding.user if dir_holding else None
            # Getting reviewer designation
            application = Ltc_application.objects.select_related('applicant').get(id=app_id)
            application.tracking_info.reviewer_id = director
            application.tracking_info.reviewer_design = dir_desig
            application.tracking_info.admin_remarks = remarks
            application.tracking_info.review_status = 'under_review'
            application.tracking_info.save()
            application.save()
            # add notif
            messages.success(request, ' Review Submitted successfully!')
        except Exception as e:
            messages.error(request,e)

    # elif app_id:
    #     # update the status of app
    #     # verify that app_id is not changed, ie untampered
    #     application = Ltc_application.objects.select_related('applicant').get(id=app_id)
    #     application.status = status
    #     application.tracking_info.admin_remarks = remarks
    #     eligible_ltc_user=Ltc_eligible_user.objects.get(user=application.applicant)
    #     if(application.is_hometown_or_elsewhere=='hometown'):
    #         eligible_ltc_user.hometown_ltc_availed+=1
    #     if(application.is_hometown_or_elsewhere=='elsewhere' ):
    #         eligible_ltc_user.elsewhere_ltc_availed+=1

    #     eligible_ltc_user.save()
    #     application.save()
    #     # add notif
    #     messages.success(request, 'Status updated successfully!')
    
    
    elif 'ltc_new_eligible_user' in request.POST:
        try:
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
        except Exception as e:
            messages.error(request,e)

    elif 'ltc_edit_eligible_user' in request.POST:
        try:
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
        except Exception as e:
            messages.error(request,e)

    elif 'ltc_delete_eligible_user' in request.POST:
        try:
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
        except Exception as e:
            messages.error(request,e)


def generate_ltc_admin_lists(request):
    """
        Function retrieves the admin information and related unreviewed,approved and archived LTC applications.
    """
    try:
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
        # availed_review = (Ltc_availed.objects.filter(ltc__tracking_info__reviewer_id=request.user).filter(ltc__status='requested').filter(ltc__tracking_info__review_status='under_review'))
        to_avail = (Ltc_to_avail.objects.filter(ltc__status='requested'))
        # to_avail_review = (Ltc_to_avail.objects.filter(ltc__tracking_info__reviewer_id=request.user).filter(ltc__status='requested').filter(ltc__tracking_info__review_status='under_review'))
        depend = (Dependent.objects.filter(ltc__status='requested'))
        # depend_review = (Dependent.objects.filter(ltc__tracking_info__reviewer_id=request.user).filter(ltc__status='requested').filter(ltc__tracking_info__review_status='under_review'))
        availed_pending = []
        to_avail_pending = []
        depend_pending = []
        availed_under_review = []
        to_avail_under_review = []
        depend_under_review = []
        # for i in availed:
        #     print(i.name, i.age, i.ltc.id)
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
            'remarks_list':reviewer_remarks,
            'ltc_availed_review1': availed,
            'ltc_to_avail_review1': to_avail,
            'dependent_review1': depend,
        }
        return response
    except Exception as e:
            messages.error(request,e)    


@transaction.atomic
def handle_ltc_eligible(request):
    """
        Function handles LTC functionalities- LTC request and review of LTC applications.
    """
    if 'ltc_request' in request.POST:
        try:
            applicant = request.user
            pf_number=1
            if(emp_consultancy_projects.objects.filter(user=request.user).first() is not None):
                pf_number = emp_consultancy_projects.objects.filter(user=request.user).first().pf_no
            else:
                messages.error(request,"Please fill EIS Forms(Consultancy Project) first.")
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

        except Exception as e:
            messages.error(request,e)
        
    if 'ltc_review_approve' in request.POST:
        try:
            app_id = request.POST.get('app_id')
            # verify that app_id is not changed, ie untampered
            review_comment = request.POST.get('remarks')
            application = Ltc_application.objects.get(id=app_id)
            application.status='approved'
            application.tracking_info.remarks = review_comment
            application.tracking_info.review_status = 'reviewed'
            application.tracking_info.save()
            application.save()
            # add notif here
            messages.success(request, 'Review submitted successfully!')
            
        except Exception as e:
            messages.error(request,e)
    
    elif 'ltc_review_reject' in request.POST:
        try:
            app_id = request.POST.get('app_id')
            # verify that app_id is not changed, ie untampered
            review_comment = request.POST.get('remarks')
            application = Ltc_application.objects.get(id=app_id)
            application.status='rejected'
            application.tracking_info.remarks = review_comment
            application.tracking_info.review_status = 'reviewed'
            application.tracking_info.save()
            application.save()
            # add notif here
            messages.success(request, 'Review submitted successfully!')
        except Exception as e:
            messages.error(request,e)


def generate_ltc_eligible_lists(request):
    """
        Function retrieves the eligible user information and related unreviewed,approved and archived LTC applications.
    """
    try:
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


        dir=is_director(request)

        response = {
            'director':dir,
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
    except Exception as e:
            messages.error(request,e)    
