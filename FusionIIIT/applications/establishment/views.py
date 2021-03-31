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

from datetime import datetime
from .models import *
from .forms import *


def initial_checks(request):
    return {}


def is_admin(request):
    return request.user == Establishment_variables.objects.select_related('est_admin').first().est_admin


def is_eligible(request):
    return True

def is_hod(request):
    user_dsg = list(HoldsDesignation.objects.filter(user=request.user))
    designation = user_dsg[0].designation.name
    if("HOD" in designation):
        return True
    return False

def is_director(request):
     user_dsg = list(HoldsDesignation.objects.filter(user=request.user))
     designation = user_dsg[0].designation.name
     print(designation)
     if("Director" in designation):
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


def is_appraisal(dictx):
    for key in dictx.keys():
        if 'appraisal' in key:
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
            application = Cpda_application.objects.select_related('applicant').get(id=app_id)
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

        # print (app.assign_form.fields['status']._choices)


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

        # print (app.assign_form.fields['status']._choices)


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
        application.tracking_info.remarks = review_comment
        application.tracking_info.review_status = 'reviewed'
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


def handle_appraisal(request):
    if 'appraisal_request' in request.POST:
        applicant = request.user

        user_dsg = list(HoldsDesignation.objects.filter(user=request.user))
        designation = user_dsg[0].designation

        user_dep = list(ExtraInfo.objects.filter(user=request.user))
        discipline = user_dep[0].department

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
                faculty_comments = faculty_comments
        )


        # # CoursesInstructed
        # count = 1
        # while(1):
        #     semester = request.POST.get('Semester'+str(count))
        #     course_name = request.POST.get('Course-Name'+str(count))
        #     course_num = request.POST.get('Course Number'+str(count))
        #     lecture_hrs_wk = request.POST.get('Lecture (Hours/week)'+str(count))
        #     tutorial_hrs_wk = request.POST.get('Tutorial (Hours/week)'+str(count))
        #     lab_hrs_wk = request.POST.get('Lab (Hours/week)'+str(count))
        #     reg_students = request.POST.get('Number of Registered Students'+str(count))
        #     if(semester == None):
        #         break
        #
        #     course = CoursesInstructed.objects.create(
        #                 appraisal = application,
        #                 semester = semester,
        #                 course_name = course_name,
        #                 course_num = course_num,
        #                 lecture_hrs_wk = lecture_hrs_wk,
        #                 tutorial_hrs_wk = tutorial_hrs_wk,
        #                 lab_hrs_wk = lab_hrs_wk,
        #                 reg_students = reg_students,
        #                 co_instructor = None
        #     )
        #
        #     count += 1
        #
        #
        #     # NewCoursesOffered
        #     count = 1
        #     while(1):
        #         course_name = request.POST.get('Course-Name1.1.2'+str(count))
        #         course_num = request.POST.get('Course Number1.1.2'+str(count))
        #         UGorPG = request.POST.get('UG/PG1.1.2'+str(count))
        #         tutorial_hrs_wk = request.POST.get('Tutorial (Hours/week)1.1.2'+str(count))
        #         year = request.POST.get('YEAR1.1.2'+str(count))
        #         semester = request.POST.get('Semester1.1.2'+str(count))
        #         if(semester == None):
        #             break
        #
        #         new_course = NewCoursesOffered.objects.create(
        #                         appraisal = application,
        #                         course_name = course_name,
        #                         course_num = course_num,
        #                         ug_or_pg = UGorPG,
        #                         tutorial_hrs_wk = tutorial_hrs_wk,
        #                         year = year,
        #                         semester = semester
        #         )
        #
        #         count += 1
        #
        #
        #     # NewCourseMaterial
        #     count = 1
        #     while(1):
        #         course_name = request.POST.get('Course-Name' + '1.1.3' + str(count))
        #         course_num = request.POST.get('Course Number' + '1.1.3' + str(count))
        #         ug_or_pg = request.POST.get('UG/PG' + '1.1.3' + str(count))
        #         activity_type = request.POST.get('Type of Activity' + '1.1.3' + str(count))
        #         availiability = request.POST.get('Web/Public' + '1.1.3' + str(count))
        #         if(course_num == None):
        #             break
        #
        #         new_courses_material = NewCourseMaterial.objects.create(
        #                                 appraisal = application,
        #                                 course_name = course_name,
        #                                 course_num = course_num,
        #                                 ug_or_pg = ug_or_pg,
        #                                 activity_type = activity_type,
        #                                 availiability = availiability
        #         )
        #
        #         count += 1
        #
        #
        #     # ThesisResearchSupervision
        #     count = 1
        #     while(1):
        #         stud_name = request.POST.get('Name of Student (MTech/PhD)' + '2.1' + str(count))
        #         thesis_title = request.POST.get('Title Of Thesis / Thesis Topic' + '2.1' + str(count))
        #         year = request.POST.get('Year' + '2.1' + str(count))
        #         semester = request.POST.get('Semester' + '2.1' + str(count))
        #         status = request.POST.get('Status(Completed / Submitted / In progress)' + '2.1' + str(count))
        #         co_supervisors = request.POST.get('Co-Supervisors' + '2.1' + str(count))
        #         if(semester == None):
        #             break
        #
        #         new_thesis_research = ThesisResearchSupervision.objects.create(
        #                                 appraisal = application,
        #                                 stud_name = stud_name,
        #                                 thesis_title = thesis_title,
        #                                 year = year,
        #                                 semester = semester,
        #                                 status = status,
        #                                 co_supervisors = co_supervisors
        #         )
        #
        #         count += 1
        #
        #
        #     # SponsoredProjects
        #     count = 1
        #     while(1):
        #         project_title = request.POST.get('Title Of Project' + '2.2' + str(count))
        #         sponsoring_agency = request.POST.get('Sponsoring Agency / Organization' + '2.2' + str(count))
        #         funding = request.POST.get('Project Funding (Rs.)' + '2.2' + str(count))
        #         duration = request.POST.get('Project Duration' + '2.2' + str(count))
        #         co_investigators = request.POST.get('Co-investigators(if-any)' + '2.2' + str(count))
        #         status = request.POST.get('Status(Completed / Submitted / In progress)' + '2.2' + str(count))
        #         remarks = request.POST.get('Remarks' + '2.2' + str(count))
        #         if(funding == None):
        #             break
        #
        #         new_sponsored_projects = SponsoredProjects.objects.create(
        #                                     appraisal = application,
        #                                     project_title = project_title,
        #                                     sponsoring_agency = sponsoring_agency,
        #                                     funding = funding,
        #                                     duration = duration,
        #                                     co_investigators = co_investigators,
        #                                     status = status,
        #                                     remarks = remarks
        #         )
        #
        #         count += 1

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

        designation = Designation.objects.filter(name = 'Director')
        holds_designation = HoldsDesignation.objects.filter(designation = designation[0])
        director = holds_designation[0].user

        appraisal_request = AppraisalRequest.objects.create(
                appraisal = application,
                hod = hod,
                director = director
        )

        messages.success(request, 'Appraisal Request sent successfully!')


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

    if 'director_appraisal_review' in request.POST:
        app_id = int(request.POST.get('app_id'))
        review_comment = request.POST.get('remarks_director')
        result = request.POST.get('result')
        application = Appraisal.objects.get(id=app_id)
        application.status = result
        request_object = AppraisalRequest.objects.filter(appraisal = application)
        appraisal_track = request_object[0]
        appraisal_track.remark_director = review_comment
        appraisal_track.status_director = result
        appraisal_track.save()
        application.save()



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
    apps = Cpda_application.objects.select_related('applicant').filter(applicant=request.user).filter(status='approved')
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


def generate_appraisal_lists(request):

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

    active_apps = Appraisal.objects.filter(applicant=request.user).exclude(status='rejected').exclude(status='accepted').order_by('-timestamp')
    archive_apps = Appraisal.objects.filter(applicant=request.user).exclude(status='requested').order_by('-timestamp')

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
            'appraisal_archive_apps':archive_apps
    })

    return response


def generate_appraisal_lists_hod(request):

    response = {}
    review_apps_hod = AppraisalRequest.objects.filter(hod = request.user).exclude(status_hod = 'rejected').exclude(status_hod = 'accepted')
    archived_apps_hod = AppraisalRequest.objects.filter(hod = request.user).exclude(status_hod = 'pending')
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

    response.update({
        'archived_apps_hod': archived_apps_hod,
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
        'research_projects_all': research_projects_all
    })
    return response


def generate_appraisal_lists_director(request):
    response = {}
    review_apps_director = AppraisalRequest.objects.filter(director = request.user).exclude(status_hod = 'rejected').exclude(status_hod = 'pending').exclude(status_director = 'rejected').exclude(status_director = 'accepted')
    archived_apps_director = AppraisalRequest.objects.filter(director = request.user).exclude(status_director = 'pending')
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

    response.update({
        'course_objects_all': course_objects_all,
        'review_apps_director': review_apps_director,
        'archived_apps_director': archived_apps_director,
        'thesis_all': thesis_all,
        'events_all': events_all,
        'patents_all': patents_all,
        'tech_transfer_all': tech_transfer_all,
        'publications_all': publications_all,
        'conferences_all': conferences_all,
        'achievments_all': achievments_all,
        'consultancy_projects_all': consultancy_projects_all,
        'research_projects_all': research_projects_all
    })

    return response



@login_required(login_url='/accounts/login')
def establishment(request):
    response = {}
    # Check if establishment variables exist, if not create some fields or ask for them
    response.update(initial_checks(request))
    # print(request.user.username)
    if is_admin(request) and request.method == "POST":
        if is_cpda(request.POST):
            handle_cpda_admin(request)
        if is_ltc(request.POST):
            handle_ltc_admin(request)


    if is_eligible(request) and request.method == "POST":
        if is_cpda(request.POST):
            handle_cpda_eligible(request)
        elif is_ltc(request.POST):
            handle_ltc_eligible(request)
        elif(is_appraisal(request.POST)):
            handle_appraisal(request)
    #
    # ############################################################################
    #
    if is_admin(request):
        response.update(generate_cpda_admin_lists(request))
        response.update(generate_ltc_admin_lists(request))
        return render(request, 'establishment/establishment.html', response)

    if is_eligible(request):
        response.update(generate_cpda_eligible_lists(request))
        response.update(generate_ltc_eligible_lists(request))
        response.update(generate_appraisal_lists(request))

    if is_hod(request):
        response.update(generate_appraisal_lists_hod(request))

    if is_director(request):
        response.update(generate_appraisal_lists_director(request))

    return render(request, 'establishment/establishment.html', response)
