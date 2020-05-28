import os
import shutil
import datetime
import decimal
import zipfile
import xlwt

from cgi import escape
from datetime import date
from io import BytesIO
from wsgiref.util import FileWrapper
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.cache import cache
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template, render_to_string
from django.utils import timezone
from django.utils.encoding import smart_str
from xhtml2pdf import pisa
from django.core import serializers
from applications.academic_information.models import Student
from notification.views import placement_cell_notif
from applications.globals.models import (DepartmentInfo, ExtraInfo,
                                        HoldsDesignation)
from .forms import (AddAchievement, AddChairmanVisit, AddCourse, AddEducation,
                    AddExperience, AddReference, AddPatent, AddProfile, AddProject,
                    AddPublication, AddSchedule, AddSkill, ManageHigherRecord,
                    ManagePbiRecord, ManagePlacementRecord, SearchHigherRecord,
                    SearchPbiRecord, SearchPlacementRecord,
                    SearchStudentRecord, SendInvite)

from .models import (Achievement, ChairmanVisit, Course, Education, Experience, Conference,
                     Has, NotifyStudent, Patent, PlacementRecord, Extracurricular, Reference,
                     PlacementSchedule, PlacementStatus, Project, Publication,
                     Skill, StudentPlacement, StudentRecord, Role, CompanyDetails,)
'''
    @variables:
            user - logged in user
            profile - variable for extrainfo
            studentrecord - storing all fetched student record from database
            years - yearwise record of student placement
            records - all the record of placement record table
            tcse - all record of cse
            tece - all record of ece
            tme - all record of me
            tadd - all record of student
            form respective form object
            stuname - student name obtained from the form
            ctc - salary offered obtained from the form
            cname - company name obtained from the form
            rollno - roll no of student obtained from the form
            year - year of placement obtained from the form
            s - extra info data of the student obtained from the form
            p - placement data of the student obtained from the form
            placementrecord - placement record of the student obtained from the form
            pbirecord - pbi data of the student obtained from the form
            test_type - type of higher study test obtained from the form
            uname - name of universty obtained from the form
            test_score - score in the test obtained from the form
            higherrecord - higher study record of the student obtained from the form
            current - current user on a particular designation
            status - status of the sent invitation by placement cell regarding placement/pbi
            institute - institute for previous education obtained from the form
            degree - degree for previous education obtained from the form
            grade - grade for previous education obtained from the form
            stream - stream for previous education obtained from the form
            sdate - start date for previous education obtained from the form
            edate - end date for previous education obtained from the form
            education_obj - object variable of Education table
            about_me - about me data obtained from the form
            age - age data obtained from the form
            address - address obtained from the form
            contact - contact obtained from the form
            pic - picture obtained from the form
            skill - skill of the user obtained from the form
            skill_rating - rating of respective skill obtained from the form
            has_obj - object variable of Has table
            achievement - achievement of user obtained from the form
            achievement_type - type of achievement obtained from the form
            description - description of respective achievement obtained from the form
            issuer - certifier of respective achievement obtained from the form
            date_earned - date of the respective achievement obtained from the form
            achievement_obj - object variable of Achievement table
            publication_title - title of the publication obtained from the form
            description - description of respective publication obtained from the form
            publisher - publisher of respective publication obtained from the form
            publication_date - date of respective publication obtained from the form
            publication_obj - object variable of Publication table
            patent_name - name of patent obtained from the form
            description - description of respective patent obtained from the form
            patent_office - office of respective patent obtained from the form
            patent_date - date of respective patent obtained from the form
            patent_obj - object variable of Patent table
            course_name - name of the course obtained from the form
            description description of respective course obtained from the form
            license_no - license_no of respective course obtained from the form
            sdate - start date of respective course obtained from the form
            edate - end date of respective course obtained from the form
            course_obj - object variable of Course table
            project_name - name of project obtained from the form
            project_status - status of respective project obtained from the form
            summary - summery of the respective project obtained from the form
            project_link - link of the respective project obtained from the form
            sdate - start date of respective project obtained from the form
            edate - end date of respective project obtained from the form
            project_obj - object variable of Project table
            title - title of any kind of experience obtained from the form
            status - status of the respective experience obtained from the form
            company - company from which respective experience is gained as obtained from the form
            location - location of the respective experience obtained from the form
            description - description of respective experience obtained from the form
            sdate - start date of respective experience obtained from the form
            edate - end date of respective experience obtained from the form
            experience_obj - object variable of Experience table
            context - to sent the relevant context for html rendering
            company_name - name of visiting comapany obtained from the form
            location -location of visiting company obtained from the form
            description - description of respective company obtained from the form
            visiting_date - visiting date of respective company obtained from the form
            visit_obj -object variable of ChairmanVisit table
            notify - object of NotifyStudent table
            schedule - object variable of PlacementSchedule table
            q1 - all data of Has table
            q3 - all data of Student table
            st - all data of Student table
            spid - id of student to be debar
            sr - record from StudentPlacement of student having id=spid
            achievementcheck - checking for achievent to be shown in cv
            educationcheck - checking for education to be shown in cv
            publicationcheck - checking for publication to be shown in cv
            patentcheck - checking for patent to be shown in cv
            internshipcheck - checking for internship to be shown in cv
            projectcheck - checking for project to be shown in cv
            coursecheck - checking for course to be shown in cv
            skillcheck - checking for skill to be shown in cv
'''


def get_reference_list(request):
    if request.method == 'POST':
        # arr = request.POST.getlist('arr[]')
        # print(arr)
        # print(type(arr))
        user = request.user
        profile = get_object_or_404(ExtraInfo, Q(user=user))
        student = get_object_or_404(Student, Q(id=profile.id))
        print(student)
        reference_objects = Reference.objects.filter(unique_id=student)
        reference_objects = serializers.serialize('json', list(reference_objects))

        context = {
            'reference_objs': reference_objects
        }
        return JsonResponse(context)


# Ajax for the company name dropdown for CompanyName when filling AddSchedule
def company_name_dropdown(request):
    if request.method == 'POST':
        current_value = request.POST.get('current_value')
        company_names = CompanyDetails.objects.filter(Q(company_name__startswith=current_value))
        company_name = []
        for name in company_names:
            company_name.append(name.company_name)

        context = {
            'company_names': company_name
        }

        return JsonResponse(context)


# Ajax for all the roles in the dropdown
def checking_roles(request):
    if request.method == 'POST':
        current_value = request.POST.get('current_value')
        all_roles = Role.objects.filter(Q(role__startswith=current_value))
        role_name = []
        for role in all_roles:
            role_name.append(role.role)
        return JsonResponse({'all_roles': role_name})


@login_required
def placement(request):
    '''
    function include the functionality of first tab of UI
    for student, placement officer & placement chairman

    placement officer & placement chairman
        - can add schedule
        - can delete schedule
    student
        - accepted or declined schedule

    '''
    user = request.user
    profile = get_object_or_404(ExtraInfo, Q(user=user))
    schedule_tab = 1
    placementstatus = ''


    form5 = AddSchedule(initial={})
    current1 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement chairman"))
    current2 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement officer"))
    current = HoldsDesignation.objects.filter(Q(working=user, designation__name="student"))

    # If the user is Student
    if current:
        student = get_object_or_404(Student, Q(id=profile.id))

        # Student view for showing accepted or declined schedule
        if request.method == 'POST':
            if 'studentapprovesubmit' in request.POST:
                status = PlacementStatus.objects.filter(
                    pk=request.POST['studentapprovesubmit']).update(
                    invitation='ACCEPTED',
                    timestamp=timezone.now())
            if 'studentdeclinesubmit' in request.POST:
                status = PlacementStatus.objects.filter(
                    Q(pk=request.POST['studentdeclinesubmit'])).update(
                    invitation='REJECTED',
                    timestamp=timezone.now())

            if 'educationsubmit' in request.POST:
                form = AddEducation(request.POST)
                if form.is_valid():
                    institute = form.cleaned_data['institute']
                    degree = form.cleaned_data['degree']
                    grade = form.cleaned_data['grade']
                    stream = form.cleaned_data['stream']
                    sdate = form.cleaned_data['sdate']
                    edate = form.cleaned_data['edate']
                    education_obj = Education.objects.create(
                        unique_id=student, degree=degree,
                        grade=grade, institute=institute,
                        stream=stream, sdate=sdate, edate=edate)
                    education_obj.save()
            if 'profilesubmit' in request.POST:
                about_me = request.POST.get('about')
                age = request.POST.get('age')
                address = request.POST.get('address')
                contact = request.POST.get('contact')
                pic = request.POST.get('pic')
                # futu = request.POST.get('futu')
                # print(studentplacement_obj.future_aspect)
                # print('fut=', fut)
                # print('futu=', futu)
                # if studentplacement_obj.future_aspect == "HIGHER STUDIES":
                #     if futu == 2:
                #         studentplacement_obj.future_aspect = "PLACEMENT"
                # elif studentplacement_obj.future_aspect == "PLACEMENT":
                #     if futu == None:
                #         studentplacement_obj.future_aspect = "HIGHER STUDIES"
                extrainfo_obj = ExtraInfo.objects.get(user=user)
                extrainfo_obj.about_me = about_me
                extrainfo_obj.age = age
                extrainfo_obj.address = address
                extrainfo_obj.phone_no = contact
                extrainfo_obj.profile_picture = pic
                extrainfo_obj.save()
                profile = get_object_or_404(ExtraInfo, Q(user=user))
            if 'skillsubmit' in request.POST:
                form = AddSkill(request.POST)
                if form.is_valid():
                    skill = form.cleaned_data['skill']
                    skill_rating = form.cleaned_data['skill_rating']
                    has_obj = Has.objects.create(unique_id=student,
                                                 skill_id=Skill.objects.get(skill=skill),
                                                 skill_rating = skill_rating)
                    has_obj.save()
            if 'achievementsubmit' in request.POST:
                form = AddAchievement(request.POST)
                if form.is_valid():
                    achievement = form.cleaned_data['achievement']
                    achievement_type = form.cleaned_data['achievement_type']
                    description = form.cleaned_data['description']
                    issuer = form.cleaned_data['issuer']
                    date_earned = form.cleaned_data['date_earned']
                    achievement_obj = Achievement.objects.create(unique_id=student,
                                                                 achievement=achievement,
                                                                 achievement_type=achievement_type,
                                                                 description=description,
                                                                 issuer=issuer,
                                                                 date_earned=date_earned)
                    achievement_obj.save()
            if 'publicationsubmit' in request.POST:
                form = AddPublication(request.POST)
                if form.is_valid():
                    publication_title = form.cleaned_data['publication_title']
                    description = form.cleaned_data['description']
                    publisher = form.cleaned_data['publisher']
                    publication_date = form.cleaned_data['publication_date']
                    publication_obj = Publication.objects.create(unique_id=student,
                                                                 publication_title=
                                                                 publication_title,
                                                                 publisher=publisher,
                                                                 description=description,
                                                                 publication_date=publication_date)
                    publication_obj.save()
            if 'patentsubmit' in request.POST:
                form = AddPatent(request.POST)
                if form.is_valid():
                    patent_name = form.cleaned_data['patent_name']
                    description = form.cleaned_data['description']
                    patent_office = form.cleaned_data['patent_office']
                    patent_date = form.cleaned_data['patent_date']
                    patent_obj = Patent.objects.create(unique_id=student, patent_name=patent_name,
                                                       patent_office=patent_office,
                                                       description=description,
                                                       patent_date=patent_date)
                    patent_obj.save()
            if 'coursesubmit' in request.POST:
                form = AddCourse(request.POST)
                if form.is_valid():
                    course_name = form.cleaned_data['course_name']
                    description = form.cleaned_data['description']
                    license_no = form.cleaned_data['license_no']
                    sdate = form.cleaned_data['sdate']
                    edate = form.cleaned_data['edate']
                    course_obj = Course.objects.create(unique_id=student, course_name=course_name,
                                                       license_no=license_no,
                                                       description=description,
                                                       sdate=sdate, edate=edate)
                    course_obj.save()
            if 'projectsubmit' in request.POST:
                form = AddProject(request.POST)
                if form.is_valid():
                    project_name = form.cleaned_data['project_name']
                    project_status = form.cleaned_data['project_status']
                    summary = form.cleaned_data['summary']
                    project_link = form.cleaned_data['project_link']
                    sdate = form.cleaned_data['sdate']
                    edate = form.cleaned_data['edate']
                    project_obj = Project.objects.create(unique_id=student, summary=summary,
                                                         project_name=project_name,
                                                         project_status=project_status,
                                                         project_link=project_link,
                                                         sdate=sdate, edate=edate)
                    project_obj.save()
            if 'experiencesubmit' in request.POST:
                form = AddExperience(request.POST)
                if form.is_valid():
                    title = form.cleaned_data['title']
                    status = form.cleaned_data['status']
                    company = form.cleaned_data['company']
                    location = form.cleaned_data['location']
                    description = form.cleaned_data['description']
                    sdate = form.cleaned_data['sdate']
                    edate = form.cleaned_data['edate']
                    experience_obj = Experience.objects.create(unique_id=student, title=title,
                                                               company=company, location=location,
                                                               status=status,
                                                               description=description,
                                                               sdate=sdate, edate=edate)
                    experience_obj.save()

            if 'deleteskill' in request.POST:
                hid = request.POST['deleteskill']
                hs = Has.objects.get(Q(pk=hid))
                hs.delete()
            if 'deleteedu' in request.POST:
                hid = request.POST['deleteedu']
                hs = Education.objects.get(Q(pk=hid))
                hs.delete()
            if 'deletecourse' in request.POST:
                hid = request.POST['deletecourse']
                hs = Course.objects.get(Q(pk=hid))
                hs.delete()
            if 'deleteexp' in request.POST:
                hid = request.POST['deleteexp']
                hs = Experience.objects.get(Q(pk=hid))
                hs.delete()
            if 'deletepro' in request.POST:
                hid = request.POST['deletepro']
                hs = Project.objects.get(Q(pk=hid))
                hs.delete()
            if 'deleteach' in request.POST:
                hid = request.POST['deleteach']
                hs = Achievement.objects.get(Q(pk=hid))
                hs.delete()
            if 'deletepub' in request.POST:
                hid = request.POST['deletepub']
                hs = Publication.objects.get(Q(pk=hid))
                hs.delete()
            if 'deletepat' in request.POST:
                hid = request.POST['deletepat']
                hs = Patent.objects.get(Q(pk=hid))
                hs.delete()

        placementschedule = PlacementSchedule.objects.filter(
            Q(placement_date__gte=date.today())).values_list('notify_id', flat=True)

        placementstatus = PlacementStatus.objects.filter(
            Q(unique_id=student,
            notify_id__in=placementschedule)).order_by('-timestamp')

        print(type(placementstatus),'-----------------\n\n')

        check_invitation_date(placementstatus)

    # facult and other staff view only statistics
    if not (current or current1 or current2):
        return redirect('/placement/statistics/')

    # delete the schedule
    if 'deletesch' in request.POST:
        print('coming--deletesch---\n\n')
        delete_sch_key = request.POST['delete_sch_key']
        try:
            placement_schedule = PlacementSchedule.objects.get(pk = delete_sch_key)
            NotifyStudent.objects.get(pk=placement_schedule.notify_id.id).delete()
            placement_schedule.delete()
            messages.success(request, 'Schedule Deleted Successfully')
        except Exception as e:
            messages.error(request, 'Problem Occurred for Schedule Delete!!!')
            print('---- \n\n record not found')

    # saving all the schedule details
    if 'schedulesubmit' in request.POST:
        form5 = AddSchedule(request.POST, request.FILES)
        if form5.is_valid():
            print('valid')
            company_name = form5.cleaned_data['company_name']
            placement_date = form5.cleaned_data['placement_date']
            location = form5.cleaned_data['location']
            ctc = form5.cleaned_data['ctc']
            time = form5.cleaned_data['time']
            attached_file = form5.cleaned_data['attached_file']
            placement_type = form5.cleaned_data['placement_type']
            role_offered = request.POST.get('role')
            description = form5.cleaned_data['description']

            try:
                comp_name = CompanyDetails.objects.filter(company_name=company_name)[0]
            except:
                CompanyDetails.objects.create(company_name=company_name)

            try:
                role = Role.objects.filter(role=role_offered)[0]
            except:
                role = Role.objects.create(role=role_offered)
                role.save()


            notify = NotifyStudent.objects.create(placement_type=placement_type,
                                                  company_name=company_name,
                                                  description=description,
                                                  ctc=ctc,
                                                  timestamp=timezone.now())

            schedule = PlacementSchedule.objects.create(notify_id=notify,
                                                        title=company_name,
                                                        description=description,
                                                        placement_date=placement_date,
                                                        attached_file = attached_file,
                                                        role=role,
                                                        location=location, time=time)

            notify.save()
            schedule.save()
            messages.success(request, "Schedule Added Successfull!!")


    schedules = PlacementSchedule.objects.all()


    context = {
        'current': current,
        'current1': current1,
        'current2': current2,
        'schedule_tab': schedule_tab,
        'schedules': schedules,
        'placementstatus': placementstatus,
        'form5': form5,
    }

    return render(request, 'placementModule/placement.html', context)


@login_required
def delete_invitation_status(request):
    '''
    function to delete the invitation that has been sent to the students
    '''
    user = request.user
    strecord_tab = 1
    mnpbi_tab = 0
    mnplacement_post = 0
    mnpbi_post = 0
    invitation_status_tab = 1
    placementstatus = []

    no_pagination = 1
    is_disabled = 0
    paginator = ''
    page_range = ''

    if 'deleteinvitationstatus' in request.POST:
        delete_invit_status_key = request.POST['deleteinvitationstatus']

        try:
            PlacementStatus.objects.get(pk=delete_invit_status_key).delete()
            messages.success(request, 'Invitation Deleted Successfully')
        except Exception as e:

            print('---- \n\n record not found')

    if 'pbi_tab_active' in request.POST:
        mnpbi_tab = 1
    else:
        mnplacement_tab = 1

    form1 = SearchStudentRecord(initial={})
    form9 = ManagePbiRecord(initial={})
    form11 = ManagePlacementRecord(initial={})
    form13 = SendInvite(initial={})
    current1 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement chairman"))
    current2 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement officer"))

    context = {
        'form1': form1,
        'form9': form9,
        'form11': form11,
        'form13': form13,
        'invitation_status_tab': invitation_status_tab,
        'mnplacement_post': mnplacement_post,
        'mnpbi_tab': mnpbi_tab,
        'placementstatus': placementstatus,
        'current':current,
        'current1': current1,
        'current2': current2,
        'strecord_tab': strecord_tab,
        'mnpbi_post': mnpbi_post,
        'page_range': page_range,
        'paginator': paginator,
        'no_pagination': no_pagination,
        'is_disabled': is_disabled,
    }

    return render(request, 'placementModule/studentrecords.html', context)


def invitation_status(request):
    '''
    function to check the invitation status
    '''
    user = request.user
    strecord_tab = 1
    mnpbi_tab = 0
    mnplacement_post = 0
    mnpbi_post = 0
    invitation_status_tab = 1
    placementstatus_placement = []
    placementstatus_pbi = []
    mnplacement_tab = 1

    no_pagination = 1
    is_disabled = 0
    paginator = ''
    page_range = ''
    placement_get_request = False
    pbi_get_request = False

    # invitation status for placement
    if 'studentplacementsearchsubmit' in request.POST:
        mnplacement_post = 1
        mnpbi_post = 0
        form = ManagePlacementRecord(request.POST)

        if form.is_valid():
            if form.cleaned_data['stuname']:
                stuname = form.cleaned_data['stuname']
            else:
                stuname = ''
            if form.cleaned_data['ctc']:
                ctc = form.cleaned_data['ctc']
            else:
                ctc = 0
            if form.cleaned_data['company']:
                cname = form.cleaned_data['company']
            else:
                cname = ''
            if form.cleaned_data['roll']:
                rollno = form.cleaned_data['roll']
            else:
                rollno = ''

            request.session['mn_stuname'] = stuname
            request.session['mn_ctc'] = ctc
            request.session['mn_cname'] = cname
            request.session['mn_rollno'] = rollno

            placementstatus_placement = PlacementStatus.objects.filter(Q(notify_id__in=NotifyStudent.objects.filter
                                                       (Q(placement_type="PLACEMENT",
                                                          company_name__icontains=cname,
                                                          ctc__gte=ctc)),
                                                       unique_id__in=Student.objects.filter
                                                       ((Q(id__in=ExtraInfo.objects.filter
                                                           (Q(user__in=User.objects.filter
                                                              (Q(first_name__icontains=stuname)),
                                                              id__icontains=rollno))
                                                           )))))
            # pagination stuff starts from here
            total_query = placementstatus_placement.count()

            if total_query > 30:
                no_pagination = 1
                paginator = Paginator(placementstatus_placement, 30)
                page = request.GET.get('page', 1)
                placementstatus_placement = paginator.page(page)
                page = int(page)
                total_page = int(page + 3)

                if page<(paginator.num_pages-3):
                    if total_query > 30 and total_query <=60:
                        page_range = range(1, 3)
                    else:
                        page_range = range(1, total_page+1)

                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, total_page)
                else:
                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, paginator.num_pages+1)
                    else:
                        page_range = range(1, paginator.num_pages+1)
            else:
                no_pagination = 0
    else:
        # when the request from pagination with some page number
        if request.GET.get('placement_page') != None:
            mnplacement_post = 1
            mnpbi_post = 0
            no_pagination = 1
            try:
                placementstatus_placement = PlacementStatus.objects.filter(Q(notify_id__in=NotifyStudent.objects.filter
                                                       (Q(placement_type="PLACEMENT",
                                                          company_name__icontains=request.session['mn_cname'],
                                                          ctc__gte=request.session['mn_ctc'])),
                                                       unique_id__in=Student.objects.filter
                                                       ((Q(id__in=ExtraInfo.objects.filter
                                                           (Q(user__in=User.objects.filter
                                                              (Q(first_name__icontains=request.session['mn_stuname'])),
                                                              id__icontains=request.session['mn_rollno']))
                                                           )))))
            except:
                placementstatus_placement = []

            if placementstatus_placement != '':
                total_query = placementstatus_placement.count()
            else:
                total_query = 0

            if total_query > 30:
                paginator = Paginator(placementstatus_placement, 30)
                page = request.GET.get('placement_page', 1)
                placementstatus_placement = paginator.page(page)
                page = int(page)
                total_page = int(page + 3)

                if page<(paginator.num_pages-3):
                    if total_query > 30 and total_query <=60:
                        page_range = range(1, 3)
                    else:
                        page_range = range(1, total_page+1)

                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, total_page)
                else:
                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, paginator.num_pages+1)
                    else:
                        page_range = range(1, paginator.num_pages+1)
            else:
                no_pagination = 0

    # invitation status for pbi
    if 'studentpbisearchsubmit' in request.POST:
        mnpbi_tab = 1
        mnpbi_post = 1
        mnplacement_post = 0
        form = ManagePbiRecord(request.POST)
        if form.is_valid():
            print(form.cleaned_data['company'])
            if form.cleaned_data['stuname']:
                stuname = form.cleaned_data['stuname']
            else:
                stuname = ''
            if form.cleaned_data['ctc']:
                ctc = form.cleaned_data['ctc']
            else:
                ctc = 0
            if form.cleaned_data['company']:
                cname = form.cleaned_data['company']
            else:
                cname = ''
            if form.cleaned_data['roll']:
                rollno = form.cleaned_data['roll']
            else:
                rollno = ''
            request.session['mn_pbi_stuname'] = stuname
            request.session['mn_pbi_ctc'] = ctc
            request.session['mn_pbi_cname'] = cname
            request.session['mn_pbi_rollno'] = rollno
            placementstatus_pbi = PlacementStatus.objects.filter(
                Q(notify_id__in=NotifyStudent.objects.filter(
                Q(placement_type="PBI",
                company_name__icontains=cname,
                ctc__gte=ctc)),
                unique_id__in=Student.objects.filter(
                (Q(id__in=ExtraInfo.objects.filter(
                Q(user__in=User.objects.filter(
                Q(first_name__icontains=stuname)),
                id__icontains=rollno))))))).order_by('id')

            total_query = placementstatus_pbi.count()
            print(total_query)

            if total_query > 30:
                no_pagination = 1
                paginator = Paginator(placementstatus_pbi, 30)
                page = request.GET.get('pbi_page', 1)
                print(page)
                placementstatus_pbi = paginator.page(page)
                page = int(page)
                total_page = int(page + 3)

                if page<(paginator.num_pages-3):
                    if total_query > 30 and total_query <=60:
                        page_range = range(1, 3)
                    else:
                        page_range = range(1, total_page+1)

                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, total_page)
                else:
                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, paginator.num_pages+1)
                    else:
                        page_range = range(1, paginator.num_pages+1)
            else:
                no_pagination = 0
    else:
        if request.GET.get('pbi_page') != None:
            mnpbi_tab = 1
            mnpbi_post = 1
            no_pagination = 1
            try:
                placementstatus_pbi = PlacementStatus.objects.filter(
                    Q(notify_id__in=NotifyStudent.objects.filter(
                    Q(placement_type="PBI",
                    company_name__icontains=request.session['mn_pbi_cname'],
                                              ctc__gte=request.session['mn_pbi_ctc'])),
                                           unique_id__in=Student.objects.filter(
                                            (Q(id__in=ExtraInfo.objects.filter(
                                                Q(user__in=User.objects.filter(
                    Q(first_name__icontains=request.session['mn_pbi_stuname'])),
                                                  id__icontains=request.session['mn_pbi_rollno']))
                                               )))))
            except:
                placementstatus_pbi = ''

            if placementstatus_pbi != '':
                total_query = placementstatus_pbi.count()
            else:
                total_query = 0
            if total_query > 30:
                paginator = Paginator(placementstatus_pbi, 30)
                page = request.GET.get('pbi_page', 1)
                placementstatus_pbi = paginator.page(page)
                page = int(page)
                total_page = int(page + 3)

                if page<(paginator.num_pages-3):
                    if total_query > 30 and total_query <=60:
                        page_range = range(1, 3)
                    else:
                        page_range = range(1, total_page+1)

                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, total_page)
                else:
                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, paginator.num_pages+1)
                    else:
                        page_range = range(1, paginator.num_pages+1)
            else:
                no_pagination = 0


    if 'pdf_gen_invitation_status' in request.POST:
        print('coming--generate--pdf')

        placementstatus = None
        if 'pdf_gen_invitation_status_placement' in request.POST:
            stuname = request.session['mn_stuname']
            ctc = request.session['mn_ctc']
            cname = request.session['mn_cname']
            rollno = request.session['mn_rollno']

            placementstatus = PlacementStatus.objects.filter(Q(notify_id__in=NotifyStudent.objects.filter
                                                           (Q(placement_type="PLACEMENT",
                                                              company_name__icontains=cname,
                                                              ctc__gte=ctc)),
                                                           unique_id__in=Student.objects.filter
                                                           ((Q(id__in=ExtraInfo.objects.filter
                                                               (Q(user__in=User.objects.filter
                                                                  (Q(first_name__icontains=stuname)),
                                                                  id__icontains=rollno))
                                                               )))))

        if 'pdf_gen_invitation_status_pbi' in request.POST:
            stuname = request.session['mn_pbi_stuname']
            ctc = request.session['mn_pbi_ctc']
            cname = request.session['mn_pbi_cname']
            rollno = request.session['mn_pbi_rollno']

            placementstatus = PlacementStatus.objects.filter(
                Q(notify_id__in=NotifyStudent.objects.filter(
                Q(placement_type="PBI",
                company_name__icontains=cname,
                ctc__gte=ctc)),
                unique_id__in=Student.objects.filter(
                (Q(id__in=ExtraInfo.objects.filter(
                Q(user__in=User.objects.filter(
                Q(first_name__icontains=stuname)),
                id__icontains=rollno))))))).order_by('id')

        context = {
            'placementstatus' : placementstatus
        }

        print('rendering the pdf--student record')
        return render_to_pdf('placementModule/pdf_invitation_status.html', context)

    if 'excel_gen_invitation_status' in request.POST:
        print('coming--generate--excel')

        placementstatus = None
        if 'excel_gen_invitation_status_placement' in request.POST:
            stuname = request.session['mn_stuname']
            ctc = request.session['mn_ctc']
            cname = request.session['mn_cname']
            rollno = request.session['mn_rollno']

            placementstatus = PlacementStatus.objects.filter(Q(notify_id__in=NotifyStudent.objects.filter
                                                           (Q(placement_type="PLACEMENT",
                                                              company_name__icontains=cname,
                                                              ctc__gte=ctc)),
                                                           unique_id__in=Student.objects.filter
                                                           ((Q(id__in=ExtraInfo.objects.filter
                                                               (Q(user__in=User.objects.filter
                                                                  (Q(first_name__icontains=stuname)),
                                                                  id__icontains=rollno))
                                                               )))))

        if 'excel_gen_invitation_status_pbi' in request.POST:
            stuname = request.session['mn_pbi_stuname']
            ctc = request.session['mn_pbi_ctc']
            cname = request.session['mn_pbi_cname']
            rollno = request.session['mn_pbi_rollno']

            placementstatus = PlacementStatus.objects.filter(
                Q(notify_id__in=NotifyStudent.objects.filter(
                Q(placement_type="PBI",
                company_name__icontains=cname,
                ctc__gte=ctc)),
                unique_id__in=Student.objects.filter(
                (Q(id__in=ExtraInfo.objects.filter(
                Q(user__in=User.objects.filter(
                Q(first_name__icontains=stuname)),
                id__icontains=rollno))))))).order_by('id')

        context = {
            'placementstatus' : placementstatus
        }

        print('rendering the excel--student record')

        return export_to_xls_invitation_status(placementstatus)

    form1 = SearchStudentRecord(initial={})
    form9 = ManagePbiRecord(initial={})
    form11 = ManagePlacementRecord(initial={})
    form13 = SendInvite(initial={})
    current1 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement chairman"))
    current2 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement officer"))

    context = {
        'form1': form1,
        'form9': form9,
        'form11': form11,
        'form13': form13,
        'invitation_status_tab': invitation_status_tab,
        'mnplacement_post': mnplacement_post,
        'mnpbi_tab': mnpbi_tab,
        'mnplacement_tab': mnplacement_tab,
        'placementstatus_placement': placementstatus_placement,
        'placementstatus_pbi': placementstatus_pbi,
        'current1': current1,
        'current2': current2,
        'strecord_tab': strecord_tab,
        'mnpbi_post': mnpbi_post,
        'page_range': page_range,
        'paginator': paginator,
        'no_pagination': no_pagination,
        'is_disabled': is_disabled,
    }

    return render(request, 'placementModule/studentrecords.html', context)


@login_required
def student_records(request):
    '''
        function for searching the records of student
    '''
    print('starts', request.GET.get('page'))
    user = request.user
    strecord_tab = 1
    no_pagination = 0
    is_disabled = 0
    paginator = ''
    page_range = ''
    mnplacement_tab = 1

    form1 = SearchStudentRecord(initial={})
    form9 = ManagePbiRecord(initial={})
    form11 = ManagePlacementRecord(initial={})
    form13 = SendInvite(initial={})
    current1 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement chairman"))
    current2 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement officer"))

    # querying the students details a/c to the input data
    if 'recordsubmit' in request.POST:
        print('search')
        student_record_check = 1
        form1 = SearchStudentRecord(request.POST)
        if form1.is_valid():
            print('search form for student record valid')
            if form1.cleaned_data['name']:
                name = form1.cleaned_data['name']
            else:
                name = ''
            if form1.cleaned_data['rollno']:
                rollno = form1.cleaned_data['rollno']
            else:
                rollno = ''

            programme = form1.cleaned_data['programme']

            department = []
            if form1.cleaned_data['dep_btech']:
                department.extend(form1.cleaned_data['dep_btech'])
            if form1.cleaned_data['dep_mtech']:
                department.extend(form1.cleaned_data['dep_mtech'])
            if form1.cleaned_data['dep_bdes']:
                department.extend(form1.cleaned_data['dep_bdes'])
            if form1.cleaned_data['dep_mdes']:
                department.extend(form1.cleaned_data['dep_mdes'])
            if form1.cleaned_data['dep_phd']:
                department.extend(form1.cleaned_data['dep_phd'])

            if form1.cleaned_data['cpi']:
                cpi = form1.cleaned_data['cpi']
            else:
                cpi = 0
            debar = form1.cleaned_data['debar']
            placed_type = form1.cleaned_data['placed_type']

            request.session['name'] = name
            request.session['rollno'] = rollno
            request.session['programme'] = programme
            request.session['department'] = department
            request.session['cpi'] = str(cpi)
            request.session['debar'] = debar
            request.session['placed_type'] = placed_type

            print(department)
            print('before request --- students')

            students = Student.objects.filter(
                Q(id__in=ExtraInfo.objects.filter(Q(
                user__in=User.objects.filter(Q(first_name__icontains=name)),
                department__in=DepartmentInfo.objects.filter(Q(name__in=department)),
                id__icontains=rollno)),
                programme=programme,
                cpi__gte=cpi)).filter(Q(pk__in=StudentPlacement.objects.filter(
                    Q(debar=debar, placed_type=placed_type)).values('unique_id_id'))).order_by('id')

            # pagination stuff starts from here
            st = students
            student_record_check= 1
            total_query = students.count()

            if total_query > 30:
                no_pagination = 1
                paginator = Paginator(students, 30)
                page = request.GET.get('page', 1)
                students = paginator.page(page)
                print(paginator.num_pages)
                print(page)
                page = int(page)
                total_page = int(page + 3)
                print(students.has_previous)

                if page<(paginator.num_pages-3):
                    if total_query > 30 and total_query <=60:
                        page_range = range(1, 3)
                    else:
                        page_range = range(1, total_page+1)

                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, total_page)
                else:
                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, paginator.num_pages+1)
                    else:
                        page_range = range(1, paginator.num_pages+1)
            else:
                no_pagination = 0
    else:
        # when the request came from pagintion with some page no.
        if request.GET.get('page') != None:
            try:
                students = Student.objects.filter(
                    Q(id__in=ExtraInfo.objects.filter(
                        Q(user__in=User.objects.filter(
                            Q(first_name__icontains=request.session['name'])
                        ),
                        department__in=DepartmentInfo.objects.filter(
                            Q(name__in=request.session['department'])
                        ),
                        id__icontains=request.session['rollno']
                        )
                    ),
                    programme=request.session['programme'],
                    cpi__gte=decimal.Decimal(request.session['cpi']))).filter(Q(pk__in=StudentPlacement.objects.filter(Q(debar=request.session['debar'],
                    placed_type=request.session['placed_type'])).values('unique_id_id'))).order_by('id')
            except:
                students = ''

            if students != '':
                total_query = students.count()
                print(students)
                print('total_query=', total_query)
            else:
                total_query = 0

            if total_query > 30:
                no_pagination = 1
                paginator = Paginator(students, 30)
                page = request.GET.get('page', 1)
                students = paginator.page(page)
                page = int(page)
                total_page = int(page + 3)

                if page<(paginator.num_pages-3):
                    if total_query > 30 and total_query <=60:
                        page_range = range(1, 3)
                    else:
                        page_range = range(1, total_page+1)

                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, total_page)
                else:
                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, paginator.num_pages+1)
                    else:
                        page_range = range(1, paginator.num_pages+1)
            else:
                no_pagination = 0
        else:
            students = ''

            if 'debar' in request.POST:
                spid = request.POST['debar']
                print('spid')
                print(spid)
                sr = StudentPlacement.objects.get(Q(pk=spid))
                sr.debar = "DEBAR"
                sr.save()
            if 'undebar' in request.POST:
                spid = request.POST['undebar']
                sr = StudentPlacement.objects.get(Q(pk=spid))
                sr.debar = "NOT DEBAR"
                sr.save()

    # pdf generation logic
    if 'pdf_gen_std_record' in request.POST:
        print('coming--generate--pdf')

        name = request.session['name']
        rollno = request.session['rollno']
        programme = request.session['programme']
        department = request.session['department']
        cpi =  int(request.session['cpi'])
        debar = request.session['debar']
        placed_type = request.session['placed_type']

        students = Student.objects.filter(
            Q(id__in=ExtraInfo.objects.filter(Q(
            user__in=User.objects.filter(Q(first_name__icontains=name)),
            department__in=DepartmentInfo.objects.filter(Q(name__in=department)),
            id__icontains=rollno)),
            programme=programme,
            cpi__gte=cpi)).filter(Q(pk__in=StudentPlacement.objects.filter(
                Q(debar=debar, placed_type=placed_type)).values('unique_id_id'))).order_by('id')

        context = {
            'students' : students
        }

        print('rendering the pdf--student record')

        return render_to_pdf('placementModule/pdf_student_record.html', context)

    # excel generation logic
    if 'excel_gen_std_record' in request.POST:
        print('coming--generate--excel')

        name = request.session['name']
        rollno = request.session['rollno']
        programme = request.session['programme']
        department = request.session['department']
        cpi =  int(request.session['cpi'])
        debar = request.session['debar']
        placed_type = request.session['placed_type']

        students = Student.objects.filter(
            Q(id__in=ExtraInfo.objects.filter(Q(
            user__in=User.objects.filter(Q(first_name__icontains=name)),
            department__in=DepartmentInfo.objects.filter(Q(name__in=department)),
            id__icontains=rollno)),
            programme=programme,
            cpi__gte=cpi)).filter(Q(pk__in=StudentPlacement.objects.filter(
                Q(debar=debar, placed_type=placed_type)).values('unique_id_id'))).order_by('id')

        context = {
            'students' : students
        }

        print('rendering the excel--student record')

        return export_to_xls_std_records(students)


    # for sending the invite to students for particular schedule
    if 'sendinvite' in request.POST:
        # invitecheck=1;
        print('send invitation coming')

        form13 = SendInvite(request.POST)

        if form13.is_valid():
            if form13.cleaned_data['company']:
                print('valid')
                if form13.cleaned_data['rollno']:
                    rollno = form13.cleaned_data['rollno']
                else:
                    rollno = ''

                programme = form13.cleaned_data['programme']

                department = []
                if form13.cleaned_data['dep_btech']:
                    department.extend(form13.cleaned_data['dep_btech'])
                if form13.cleaned_data['dep_mtech']:
                    department.extend(form13.cleaned_data['dep_mtech'])
                if form13.cleaned_data['dep_bdes']:
                    department.extend(form13.cleaned_data['dep_bdes'])
                if form13.cleaned_data['dep_mdes']:
                    department.extend(form13.cleaned_data['dep_mdes'])
                if form13.cleaned_data['dep_phd']:
                    department.extend(form13.cleaned_data['dep_phd'])


                if form13.cleaned_data['cpi']:
                    cpi = form13.cleaned_data['cpi']
                else:
                    cpi = 0

                if form13.cleaned_data['no_of_days']:
                    no_of_days = form13.cleaned_data['no_of_days']
                else:
                    no_of_days = 10

                print('\n\n\n  coming ', no_of_days)

                comp = form13.cleaned_data['company']

                notify = NotifyStudent.objects.get(company_name=comp.company_name,
                                                   placement_type=comp.placement_type)

                students = Student.objects.filter(
                    Q(
                        id__in = ExtraInfo.objects.filter(
                            Q(
                            department__in = DepartmentInfo.objects.filter(Q(name__in=department)),
                            id__icontains = rollno
                            )
                        ),
                        programme = programme,
                        cpi__gte = cpi
                    )
                ).exclude(id__in = PlacementStatus.objects.filter(
                    notify_id=notify).values_list('unique_id', flat=True))

                PlacementStatus.objects.bulk_create( [PlacementStatus(notify_id=notify,
                            unique_id=student, no_of_days=no_of_days) for student in students] )

                for st in students:
                    #print(request.user, '-----------------------', st.id.user,'-----------------')
                    placement_cell_notif(request.user, st.id.user, "")

                students = ''
                messages.success(request, 'Notification Sent')
            else:
                messages.error(request, 'Problem Occurred!! Please Try Again!!')

    print(students)
    context = {
        'form1': form1,
        'form9': form9,
        'form11': form11,
        'form13': form13,
        'current1': current1,
        'current2': current2,
        'mnplacement_tab': mnplacement_tab,
        'strecord_tab': strecord_tab,
        'students': students,
        'page_range': page_range,
        'paginator': paginator,
        'no_pagination': no_pagination,
        'is_disabled': is_disabled,
    }

    print('send invitation last checkpoint')
    return render(request, 'placementModule/studentrecords.html', context)


@login_required
def manage_records(request):
    '''
        function to manage the records
        - can add the records under placement | pbi | higher studies
        - can also search the records under placement | pbi | higher studies
    '''
    user = request.user
    mnrecord_tab = 1
    pagination_placement = 0
    pagination_pbi = 0
    pagination_higher = 0
    is_disabled = 0
    years = None
    records = None
    paginator = ''
    page_range = ''
    pbirecord = None
    placementrecord = None
    higherrecord = None
    officer_statistics_past_pbi_search = 0
    officer_statistics_past_higher_search = 0

    profile = get_object_or_404(ExtraInfo, Q(user=user))
    studentrecord = StudentRecord.objects.all()

    years = PlacementRecord.objects.filter(~Q(placement_type="HIGHER STUDIES")).values('year').annotate(Count('year'))
    records = PlacementRecord.objects.values('name', 'year', 'ctc', 'placement_type').annotate(Count('name'), Count('year'), Count('placement_type'), Count('ctc'))


    form2 = SearchPlacementRecord(initial={})
    form3 = SearchPbiRecord(initial={})
    form4 = SearchHigherRecord(initial={})
    current1 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement chairman"))
    current2 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement officer"))

    current = HoldsDesignation.objects.filter(Q(working=user, designation__name="student"))

    if len(current) == 0:
        current = None


    try:
        # for adding the new data for student under higher studies category
        if 'studenthigheraddsubmit' in request.POST:
            officer_statistics_past_higher_add = 1
            form = SearchHigherRecord(request.POST)
            if form.is_valid():
                rollno = form.cleaned_data['roll']
                uname = form.cleaned_data['uname']
                test_score = form.cleaned_data['test_score']
                test_type = form.cleaned_data['test_type']
                year = form.cleaned_data['year']
                placementr = PlacementRecord.objects.create(year=year, name=uname,
                                                                  placement_type="HIGHER STUDIES",
                                                                  test_type=test_type,
                                                                  test_score=test_score)
                studentr = StudentRecord.objects.create(record_id=placementr,
                                                             unique_id=Student.objects.get
                                                             ((Q(id=ExtraInfo.objects.get
                                                                 (Q(id=rollno))))))
                studentr.save()
                placementr.save()
                messages.success(request, 'Record Added Successfully!!')

        # for adding the new data for student under pbi category
        if 'studentpbiaddsubmit' in request.POST:
            officer_statistics_past_pbi_add = 1
            form = SearchPbiRecord(request.POST)
            if form.is_valid():
                rollno = form.cleaned_data['roll']
                ctc = form.cleaned_data['ctc']
                year = form.cleaned_data['year']
                cname = form.cleaned_data['cname']
                placementr = PlacementRecord.objects.create(year=year, ctc=ctc,
                                                                  placement_type="PBI",
                                                                  name=cname)
                studentr = StudentRecord.objects.create(record_id=placementr,
                                                             unique_id=Student.objects.get
                                                             ((Q(id=ExtraInfo.objects.get
                                                                 (Q(id=rollno))))))
                studentr.save()
                placementr.save()
                messages.success(request, 'Record Added Successfully!!')

        # for adding the new data for student under placement category
        if 'studentplacementaddsubmit' in request.POST:
            officer_statistics_past_add = 1
            form = SearchPlacementRecord(request.POST)
            if form.is_valid():
                rollno = form.cleaned_data['roll']
                ctc = form.cleaned_data['ctc']
                year = form.cleaned_data['year']
                cname = form.cleaned_data['cname']
                placementr = PlacementRecord.objects.create(year=year, ctc=ctc,
                                                                  placement_type="PLACEMENT",
                                                                  name=cname)
                studentr = StudentRecord.objects.create(record_id=placementr,
                                                             unique_id=Student.objects.get
                                                             ((Q(id=ExtraInfo.objects.get
                                                                 (Q(id=rollno))))))
                studentr.save()
                placementr.save()
                messages.success(request, 'Record Added Successfully!!')

        # for searching the student details under placement category
        if 'studentplacementrecordsubmit' in request.POST:
            officer_statistics_past = 1
            form = SearchPlacementRecord(request.POST)
            if form.is_valid():
                if form.cleaned_data['stuname']:
                    stuname = form.cleaned_data['stuname']
                else:
                    stuname = ''
                if form.cleaned_data['ctc']:
                    ctc = form.cleaned_data['ctc']
                else:
                    ctc = 0
                if form.cleaned_data['cname']:
                    cname = form.cleaned_data['cname']
                else:
                    cname = ''
                if form.cleaned_data['roll']:
                    rollno = form.cleaned_data['roll']
                else:
                    rollno = ''
                if form.cleaned_data['year']:
                    print('yeayryeayryeayr')
                    year = form.cleaned_data['year']
                    s = Student.objects.filter((Q(id__in=ExtraInfo.objects.filter
                        (Q(user__in=User.objects.filter
                           (Q(first_name__icontains=stuname)),
                           id__icontains=rollno))
                        )))

                    p = PlacementRecord.objects.filter(Q(placement_type="PLACEMENT", name__icontains=cname, ctc__gte=ctc, year=year))

                    placementrecord = StudentRecord.objects.filter(Q(record_id__in=PlacementRecord.objects.filter(Q(placement_type="PLACEMENT", name__icontains=cname, ctc__gte=ctc, year=year)), unique_id__in=Student.objects.filter((Q(id__in=ExtraInfo.objects.filter(Q(user__in=User.objects.filter(Q(first_name__icontains=stuname)),id__icontains=rollno)))))))
                else:
                    print('dfd')
                    s = Student.objects.filter((Q(id__in=ExtraInfo.objects.filter
                        (Q(user__in=User.objects.filter
                           (Q(first_name__icontains=stuname)),
                           id__icontains=rollno))
                        )))

                    p = PlacementRecord.objects.filter(Q(placement_type="PLACEMENT", name__icontains=cname, ctc__gte=ctc))

                    placementrecord = StudentRecord.objects.filter(
                        Q(record_id__in=PlacementRecord.objects.filter(
                        Q(placement_type="PLACEMENT", name__icontains=cname, ctc__gte=ctc)),
                        unique_id__in=Student.objects.filter(
                        (Q(id__in=ExtraInfo.objects.filter(
                        Q(user__in=User.objects.filter(Q(first_name__icontains=stuname)),
                        id__icontains=rollno)))))))

                request.session['stuname'] = stuname
                request.session['ctc'] = ctc
                request.session['cname'] = cname
                request.session['rollno'] = rollno
                request.session['year'] = form.cleaned_data['year']

                total_query = placementrecord.count()

                if total_query > 30:
                    pagination_placement = 1
                    paginator = Paginator(placementrecord, 30)
                    page = request.GET.get('page', 1)
                    placementrecord = paginator.page(page)
                    print(paginator.num_pages)
                    print(page)
                    page = int(page)
                    total_page = int(page + 3)
                    print(placementrecord.has_previous)

                    if page<(paginator.num_pages-3):
                        if total_query > 30 and total_query <=60:
                            page_range = range(1, 3)
                        else:
                            page_range = range(1, total_page+1)

                        if page >= 5:
                            is_disabled = 1
                            page_range = range(page-2, total_page)
                    else:
                        if page >= 5:
                            is_disabled = 1
                            page_range = range(page-2, paginator.num_pages+1)
                        else:
                            page_range = range(1, paginator.num_pages+1)
                else:
                    pagination_placement = 0
        else:
            if request.GET.get('page') != None:
                print('--------------------page value none')
                try:
                    if request.session['year']:
                        print('lololololol')
                        s = Student.objects.filter(
                            (Q(id__in=ExtraInfo.objects.filter(
                            Q(user__in=User.objects.filter(
                            Q(first_name__icontains=request.session['stuname'])),
                           id__icontains=request.session['rollno']))
                        )))

                        p = PlacementRecord.objects.filter(
                            Q(placement_type="PLACEMENT",
                            name__icontains=request.session['cname'],
                            ctc__gte=request.session['ctc'],
                            year=request.session['year']))

                        placementrecord = StudentRecord.objects.filter(
                            Q(record_id__in=PlacementRecord.objects.filter(
                                Q(placement_type="PLACEMENT",
                                name__icontains=request.session['cname'],
                                ctc__gte=request.session['ctc'],
                                year=request.session['year'])),
                                unique_id__in=Student.objects.filter(
                                (Q(id__in=ExtraInfo.objects.filter(
                                Q(user__in=User.objects.filter(
                                Q(first_name__icontains=request.session['stuname'])),
                                id__icontains=request.session['rollno'])))))))
                    else:
                        s = Student.objects.filter((Q(id__in=ExtraInfo.objects.filter
                        (Q(user__in=User.objects.filter
                           (Q(first_name__icontains=request.session['stuname'])),
                           id__icontains=request.session['rollno']))
                        )))

                        p = PlacementRecord.objects.filter(
                            Q(placement_type="PLACEMENT",
                                name__icontains=request.session['cname'],
                                ctc__gte=request.session['ctc']))

                        placementrecord = StudentRecord.objects.filter(
                            Q(record_id__in=PlacementRecord.objects.filter(
                            Q(placement_type="PLACEMENT",
                                name__icontains=request.session['cname'],
                                ctc__gte=request.session['ctc'])),
                            unique_id__in=Student.objects.filter(
                            (Q(id__in=ExtraInfo.objects.filter(
                            Q(user__in=User.objects.filter(
                            Q(first_name__icontains=request.session['stuname'])),
                            id__icontains=request.session['rollno'])))))))
                except:
                    print('except')
                    placementrecord = ''

                if placementrecord != '':
                    total_query = placementrecord.count()
                else:
                    total_query = 0

                if total_query > 30:
                    pagination_placement = 1
                    paginator = Paginator(placementrecord, 30)
                    page = request.GET.get('page', 1)
                    placementrecord = paginator.page(page)
                    page = int(page)
                    total_page = int(page + 3)

                    if page<(paginator.num_pages-3):
                        if total_query > 30 and total_query <=60:
                            page_range = range(1, 3)
                        else:
                            page_range = range(1, total_page+1)

                        if page >= 5:
                            is_disabled = 1
                            page_range = range(page-2, total_page)
                    else:
                        if page >= 5:
                            is_disabled = 1
                            page_range = range(page-2, paginator.num_pages+1)
                        else:
                            page_range = range(1, paginator.num_pages+1)
                else:
                    pagination_placement = 0
            else:
                placementrecord = ''

        # for searching the student details under pbi category
        if 'studentpbirecordsubmit' in request.POST:
            officer_statistics_past_pbi_search = 1
            form = SearchPbiRecord(request.POST)
            if form.is_valid():
                if form.cleaned_data['stuname']:
                    stuname = form.cleaned_data['stuname']
                else:
                    stuname = ''
                if form.cleaned_data['ctc']:
                    ctc = form.cleaned_data['ctc']
                else:
                    ctc = 0
                if form.cleaned_data['cname']:
                    cname = form.cleaned_data['cname']
                else:
                    cname = ''
                if form.cleaned_data['roll']:
                    rollno = form.cleaned_data['roll']
                else:
                    rollno = ''
                if form.cleaned_data['year']:
                    year = form.cleaned_data['year']
                    pbirecord = StudentRecord.objects.filter(Q(record_id__in=PlacementRecord.objects.filter
                                                           (Q(placement_type="PBI",
                                                              name__icontains=cname,
                                                              ctc__gte=ctc, year=year)),
                                                           unique_id__in=Student.objects.filter
                                                           ((Q(id__in=ExtraInfo.objects.filter
                                                               (Q(user__in=User.objects.filter
                                                                  (Q(first_name__icontains=stuname)),
                                                                  id__icontains=rollno))
                                                               )))))
                else:
                    pbirecord = StudentRecord.objects.filter(Q(record_id__in=PlacementRecord.objects.filter
                                                           (Q(placement_type="PBI",
                                                              name__icontains=cname,
                                                              ctc__gte=ctc)),
                                                           unique_id__in=Student.objects.filter
                                                           ((Q(id__in=ExtraInfo.objects.filter
                                                               (Q(user__in=User.objects.filter
                                                                  (Q(first_name__icontains=stuname)),
                                                                  id__icontains=rollno))
                                                               )))))
                request.session['stuname'] = stuname
                request.session['ctc'] = ctc
                request.session['cname'] = cname
                request.session['rollno'] = rollno
                request.session['year'] = form.cleaned_data['year']

                total_query = pbirecord.count()

                if total_query > 30:
                    pagination_pbi = 1
                    paginator = Paginator(pbirecord, 30)
                    page = request.GET.get('page', 1)
                    pbirecord = paginator.page(page)
                    page = int(page)
                    total_page = int(page + 3)

                    if page<(paginator.num_pages-3):
                        if total_query > 30 and total_query <=60:
                            page_range = range(1, 3)
                        else:
                            page_range = range(1, total_page+1)

                        if page >= 5:
                            is_disabled = 1
                            page_range = range(page-2, total_page)
                    else:
                        if page >= 5:
                            is_disabled = 1
                            page_range = range(page-2, paginator.num_pages+1)
                        else:
                            page_range = range(1, paginator.num_pages+1)
                else:
                    pagination_pbi = 0
        else:
            if request.GET.get('page') != None:
                print('--------------------page value none')
                try:
                    if request.session['year']:
                        pbirecord = StudentRecord.objects.filter(
                            Q(record_id__in=PlacementRecord.objects.filter(
                            Q(placement_type="PBI",
                            name__icontains=request.session['cname'],
                            ctc__gte=ctc, year=request.session['year'])),
                            unique_id__in=Student.objects.filter((
                            Q(id__in=ExtraInfo.objects.filter(
                            Q(user__in=User.objects.filter(
                            Q(first_name__icontains=request.session['stuname'])),
                            id__icontains=request.session['rollno'])))))))
                    else:
                        pbirecord = StudentRecord.objects.filter(
                            Q(record_id__in=PlacementRecord.objects.filter(Q(placement_type="PBI",
                                                                  name__icontains=request.session['cname'],
                                                                  ctc__gte=request.session['ctc'])),
                                                               unique_id__in=Student.objects.filter(
                                                                (Q(id__in=ExtraInfo.objects.filter(
                                                                Q(user__in=User.objects.filter(
                            Q(first_name__icontains=request.session['stuname'])),
                            id__icontains=request.session['rollno'])))))))
                except:
                    print('except')
                    pbirecord = ''

                if pbirecord != '':
                    total_query = pbirecord.count()
                else:
                    total_query = 0

                if total_query > 30:
                    pagination_pbi = 1
                    paginator = Paginator(pbirecord, 30)
                    page = request.GET.get('page', 1)
                    pbirecord = paginator.page(page)
                    page = int(page)
                    total_page = int(page + 3)

                    if page<(paginator.num_pages-3):
                        if total_query > 30 and total_query <=60:
                            page_range = range(1, 3)
                        else:
                            page_range = range(1, total_page+1)

                        if page >= 5:
                            is_disabled = 1
                            page_range = range(page-2, total_page)
                    else:
                        if page >= 5:
                            is_disabled = 1
                            page_range = range(page-2, paginator.num_pages+1)
                        else:
                            page_range = range(1, paginator.num_pages+1)
                else:
                    pagination_pbi = 0
            else:
                pbirecord = ''

        # for searching the student details under higher studies category
        if 'studenthigherrecordsubmit' in request.POST:
            officer_statistics_past_higher_search = 1
            form = SearchHigherRecord(request.POST)
            if form.is_valid():
                if form.cleaned_data['stuname']:
                    stuname = form.cleaned_data['stuname']
                else:
                    stuname = ''
                if form.cleaned_data['test_type']:
                    test_type = form.cleaned_data['test_type']
                else:
                    test_type = ''
                if form.cleaned_data['uname']:
                    uname = form.cleaned_data['uname']
                else:
                    uname = ''
                if form.cleaned_data['test_score']:
                    test_score = form.cleaned_data['test_score']
                else:
                    test_score = 0
                if form.cleaned_data['roll']:
                    rollno = form.cleaned_data['roll']
                else:
                    rollno = ''
                if form.cleaned_data['year']:
                    year = form.cleaned_data['year']
                    higherrecord = StudentRecord.objects.filter(Q(record_id__in=PlacementRecord.objects.filter
                                                           (Q(placement_type="HIGHER STUDIES",
                                                              test_type__icontains=test_type,
                                                              name__icontains=uname, year=year,
                                                              test_score__gte=test_score)),
                                                           unique_id__in=Student.objects.filter
                                                           ((Q(id__in=ExtraInfo.objects.filter
                                                               (Q(user__in=User.objects.filter
                                                                  (Q(first_name__icontains=stuname)),
                                                                  id__icontains=rollno))
                                                               )))))
                else:
                    higherrecord = StudentRecord.objects.filter(
                        Q(record_id__in=PlacementRecord.objects.filter
                                                           (Q(placement_type="HIGHER STUDIES",
                                                              test_type__icontains=test_type,
                                                              name__icontains=uname,
                                                              test_score__gte=test_score)),
                                                           unique_id__in=Student.objects.filter
                                                           ((Q(id__in=ExtraInfo.objects.filter
                                                               (Q(user__in=User.objects.filter
                                                                  (Q(first_name__icontains=stuname)),
                                                                  id__icontains=rollno))
                                                               )))))
                request.session['stuname'] = stuname
                request.session['test_score'] = test_score
                request.session['uname'] = uname
                request.session['test_type'] = test_type
                request.session['rollno'] = rollno
                request.session['year'] = form.cleaned_data['year']

                total_query = higherrecord.count()

                if total_query > 30:
                    pagination_higher = 1
                    paginator = Paginator(higherrecord, 30)
                    page = request.GET.get('page', 1)
                    higherrecord = paginator.page(page)
                    page = int(page)
                    total_page = int(page+3)

                    if page < (paginator.num_pages-3):
                        if total_query > 30 and total_query <= 60:
                            page_range = range(1, 3)
                        else:
                            page_range = range(1, total_page+1)

                        if page >= 5:
                            is_disabled = 1
                            page_range = range(page-2, total_page)
                    else:
                        if page >= 5:
                            is_disabled = 1
                            page_range = range(page-2, paginator.num_pages+1)
                        else:
                            page_range = range(page-2, paginator.num_pages+1)
                else:
                    pagination_higher = 0
        else:
            if request.GET.get('page') != None:
                print('--------------------page value none')
                try:
                    if request.session['year']:
                        higherrecord = StudentRecord.objects.filter(
                            Q(record_id__in=PlacementRecord.objects.filter(
                                Q(placement_type="HIGHER STUDIES",
                                                              test_type__icontains=request.session['test_type'],
                                                              name__icontains=request.session['uname'],
                                                              year=request.session['year'],
                                                              test_score__gte=request.session['test_score'])),
                                                           unique_id__in=Student.objects.filter(
                                                            (Q(id__in=ExtraInfo.objects.filter(
                                                                Q(user__in=User.objects.filter(
                                                                Q(first_name__icontains=request.session['stuname'])),
                                                                id__icontains=request.session['rollno']))
                                                               )))))
                    else:
                        higherrecord = StudentRecord.objects.filter(
                            Q(record_id__in=PlacementRecord.objects.filter
                                                               (Q(placement_type="HIGHER STUDIES",
                                                                  test_type__icontains=request.session['test_type'],
                                                                  name__icontains=request.session['uname'],
                                                                  test_score__gte=request.session['test_score'])),
                                                               unique_id__in=Student.objects.filter
                                                               ((Q(id__in=ExtraInfo.objects.filter
                                                                   (Q(user__in=User.objects.filter
                                                                      (Q(first_name__icontains=request.session['stuname'])),
                                                                      id__icontains=request.session['rollno']))
                                                                   )))))
                except:
                    print('except')
                    higherrecord = ''

                if higherrecord != '':
                    total_query = higherrecord.count()
                else:
                    total_query = 0

                if total_query > 30:
                    no_pagination = 1
                    paginator = Paginator(higherrecord, 30)
                    page = request.GET.get('page', 1)
                    higherrecord = paginator.page(page)
                    page = int(page)
                    total_page = int(page + 3)

                    if page<(paginator.num_pages-3):
                        if total_query > 30 and total_query <=60:
                            page_range = range(1, 3)
                        else:
                            page_range = range(1, total_page+1)

                        if page >= 5:
                            is_disabled = 1
                            page_range = range(page-2, total_page)
                    else:
                        if page >= 5:
                            is_disabled = 1
                            page_range = range(page-2, paginator.num_pages+1)
                        else:
                            page_range = range(1, paginator.num_pages+1)
                else:
                    no_pagination = 0
            else:
                higherrecord = ''


    except Exception as e:
        messages.error(request, "Problem Occurred!!! Please Try Again with Correct Info!!")
        print(e)


    context = {
        'form2'             :            form2,
        'form3'             :            form3,
        'form4'             :            form4,
        'current'           :          current,
        'current1'          :         current1,
        'current2'          :         current2,
        'mnrecord_tab'      :         mnrecord_tab,
        'pbirecord'         :        pbirecord,
        'placementrecord'   :  placementrecord,
        'higherrecord'      :     higherrecord,
        'years'             :            years,
        'records'           :          records,
        'page_range': page_range,
        'paginator': paginator,
        'pagination_placement': pagination_placement,
        'pagination_pbi': pagination_pbi,
        'pagination_higher': pagination_higher,
        'is_disabled': is_disabled,
        'officer_statistics_past_pbi_search': officer_statistics_past_pbi_search,
        'officer_statistics_past_higher_search': officer_statistics_past_higher_search
    }

    return render(request, 'placementModule/managerecords.html', context)




@login_required
def placement_statistics(request):
    '''
    logic of the view shown under Placement Statistics tab
    '''
    user = request.user
    statistics_tab = 1
    delete_operation = 0

    pagination_placement = 0
    pagination_pbi = 0
    pagination_higher = 0
    is_disabled = 0
    paginator = ''
    page_range = ''
    officer_statistics_past_pbi_search = 0
    officer_statistics_past_higher_search = 0

    profile = get_object_or_404(ExtraInfo, Q(user=user))
    studentrecord = StudentRecord.objects.all()

    years = PlacementRecord.objects.filter(~Q(placement_type="HIGHER STUDIES")).values('year').annotate(Count('year'))
    records = PlacementRecord.objects.values('name', 'year', 'ctc', 'placement_type').annotate(Count('name'), Count('year'), Count('placement_type'), Count('ctc'))

    invitecheck=0;
    for r in records:
        r['name__count'] = 0
        r['year__count'] = 0
        r['placement_type__count'] = 0
    tcse = dict()
    tece = dict()
    tme = dict()
    tadd = dict()
    for y in years:
        tcse[y['year']] = 0
        tece[y['year']] = 0
        tme[y['year']] = 0
        for r in records:
            if r['year'] == y['year']:
                if r['placement_type'] != "HIGHER STUDIES":
                    for z in studentrecord:
                        if z.record_id.name == r['name'] and z.record_id.year == r['year'] and z.unique_id.id.department.name == "CSE":
                            tcse[y['year']] = tcse[y['year']]+1
                            r['name__count'] = r['name__count']+1
                        if z.record_id.name == r['name'] and z.record_id.year == r['year'] and z.unique_id.id.department.name == "ECE":
                            tece[y['year']] = tece[y['year']]+1
                            r['year__count'] = r['year__count']+1
                        if z.record_id.name == r['name'] and z.record_id.year == r['year'] and z.unique_id.id.department.name == "ME":
                            tme[y['year']] = tme[y['year']]+1
                            r['placement_type__count'] = r['placement_type__count']+1
        tadd[y['year']] = tcse[y['year']]+tece[y['year']]+tme[y['year']]
        y['year__count'] = [tadd[y['year']], tcse[y['year']], tece[y['year']], tme[y['year']]]

    form2 = SearchPlacementRecord(initial={})
    form3 = SearchPbiRecord(initial={})
    form4 = SearchHigherRecord(initial={})
    current1 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement chairman"))
    current2 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement officer"))
    current = HoldsDesignation.objects.filter(Q(working=user, designation__name="student"))

    if len(current1)!=0 or len(current2)!=0:
        delete_operation = 1

    print('\n\n\n\n-----------------', delete_operation)

    if len(current) == 0:
        current = None

    # results of the searched query under placement tab
    if 'studentplacementrecordsubmit' in request.POST:
        officer_statistics_past = 1
        form = SearchPlacementRecord(request.POST)
        if form.is_valid():
            if form.cleaned_data['stuname']:
                stuname = form.cleaned_data['stuname']
                try:
                    first_name = stuname.split(" ")[0]
                    last_name = stuname.split(" ")[1]
                except Exception as e:
                    print(e)
                    first_name = stuname
                    last_name = ''
            else:
                stuname = ''
                first_name = ''
                last_name = ''
            if form.cleaned_data['ctc']:
                ctc = form.cleaned_data['ctc']
            else:
                ctc = 0
            if form.cleaned_data['cname']:
                cname = form.cleaned_data['cname']
            else:
                cname = ''
            if form.cleaned_data['roll']:
                rollno = form.cleaned_data['roll']
            else:
                rollno = ''
            if form.cleaned_data['year']:
                year = form.cleaned_data['year']
                s = Student.objects.filter((Q(id__in=ExtraInfo.objects.filter(
                    Q(user__in=User.objects.filter(
                        first_name__icontains=first_name,
                        last_name__icontains=last_name),
                       id__icontains=rollno))
                    )))

                p = PlacementRecord.objects.filter(Q(placement_type="PLACEMENT", name__icontains=cname, ctc__gte=ctc, year=year))

                placementrecord = StudentRecord.objects.filter(
                    Q(record_id__in=PlacementRecord.objects.filter(
                        Q(placement_type="PLACEMENT", name__icontains=cname, ctc__gte=ctc, year=year)),
                    unique_id__in=Student.objects.filter(
                        (Q(id__in=ExtraInfo.objects.filter(
                            Q(user__in=User.objects.filter(
                                first_name__icontains=first_name,
                                last_name__icontains=last_name,
                            id__icontains=rollno))))))))
            else:
                s = Student.objects.filter((Q(id__in=ExtraInfo.objects.filter(
                    Q(user__in=User.objects.filter(
                        first_name__icontains=first_name,
                        last_name__icontains=last_name),
                        id__icontains=rollno))
                    )))

                p = PlacementRecord.objects.filter(Q(placement_type="PLACEMENT", name__icontains=cname, ctc__gte=ctc))
                placementrecord = StudentRecord.objects.filter(
                    Q(record_id__in=PlacementRecord.objects.filter(
                    Q(placement_type="PLACEMENT", name__icontains=cname, ctc__gte=ctc)),
                    unique_id__in=Student.objects.filter(
                    (Q(id__in=ExtraInfo.objects.filter(
                    Q(user__in=User.objects.filter(
                        first_name__icontains=first_name,
                        last_name__icontains=last_name),
                    id__icontains=rollno)))))))

            request.session['first_name'] = first_name
            request.session['last_name'] = last_name
            request.session['ctc'] = ctc
            request.session['cname'] = cname
            request.session['rollno'] = rollno
            request.session['year'] = form.cleaned_data['year']

            total_query = placementrecord.count()

            if total_query > 30:
                pagination_placement = 1
                paginator = Paginator(placementrecord, 30)
                page = request.GET.get('page', 1)
                placementrecord = paginator.page(page)
                print(paginator.num_pages)
                print(page)
                page = int(page)
                total_page = int(page + 3)
                print(placementrecord.has_previous)

                if page<(paginator.num_pages-3):
                    if total_query > 30 and total_query <=60:
                        page_range = range(1, 3)
                    else:
                        page_range = range(1, total_page+1)

                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, total_page)
                else:
                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, paginator.num_pages+1)
                    else:
                        page_range = range(1, paginator.num_pages+1)
            else:
                pagination_placement = 0
    else:
        if request.GET.get('page') != None:
            print('--------------------page value none')
            try:
                if request.session['year']:
                    print('lololololol')
                    s = Student.objects.filter(
                        (Q(id__in=ExtraInfo.objects.filter(
                        Q(user__in=User.objects.filter(
                        Q(first_name__icontains=request.session['first_name'],
                        last_name__icontains=request.session['last_name'])),
                       id__icontains=request.session['rollno']))
                    )))

                    p = PlacementRecord.objects.filter(
                        Q(placement_type="PLACEMENT",
                        name__icontains=request.session['cname'],
                        ctc__gte=request.session['ctc'],
                        year=request.session['year']))

                    placementrecord = StudentRecord.objects.filter(
                        Q(record_id__in=PlacementRecord.objects.filter(
                            Q(placement_type="PLACEMENT",
                            name__icontains=request.session['cname'],
                            ctc__gte=request.session['ctc'],
                            year=request.session['year'])),
                            unique_id__in=Student.objects.filter(
                            (Q(id__in=ExtraInfo.objects.filter(
                            Q(user__in=User.objects.filter(
                            Q(first_name__icontains=request.session['first_name'],
                            last_name__icontains=request.session['last_name'])),
                            id__icontains=request.session['rollno'])))))))
                else:
                    s = Student.objects.filter((Q(id__in=ExtraInfo.objects.filter
                    (Q(user__in=User.objects.filter
                       (Q(first_name__icontains=request.session['first_name'],
                        last_name__icontains=request.session['last_name'])),
                       id__icontains=request.session['rollno']))
                    )))

                    p = PlacementRecord.objects.filter(
                        Q(placement_type="PLACEMENT",
                            name__icontains=request.session['cname'],
                            ctc__gte=request.session['ctc']))

                    placementrecord = StudentRecord.objects.filter(
                        Q(record_id__in=PlacementRecord.objects.filter(
                        Q(placement_type="PLACEMENT",
                            name__icontains=request.session['cname'],
                            ctc__gte=request.session['ctc'])),
                        unique_id__in=Student.objects.filter(
                        (Q(id__in=ExtraInfo.objects.filter(
                        Q(user__in=User.objects.filter(
                        Q(first_name__icontains=request.session['first_name'],
                        last_name__icontains=request.session['last_name'])),
                        id__icontains=request.session['rollno'])))))))
            except Exception as e:
                print(e)
                placementrecord = ''

            if placementrecord != '':
                total_query = placementrecord.count()
            else:
                total_query = 0

            if total_query > 30:
                pagination_placement = 1
                paginator = Paginator(placementrecord, 30)
                page = request.GET.get('page', 1)
                placementrecord = paginator.page(page)
                page = int(page)
                total_page = int(page + 3)

                if page<(paginator.num_pages-3):
                    if total_query > 30 and total_query <=60:
                        page_range = range(1, 3)
                    else:
                        page_range = range(1, total_page+1)

                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, total_page)
                else:
                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, paginator.num_pages+1)
                    else:
                        page_range = range(1, paginator.num_pages+1)
            else:
                pagination_placement = 0
        else:
            placementrecord = ''

    # results of the searched query under pbi tab
    if 'studentpbirecordsubmit' in request.POST:
        officer_statistics_past_pbi_search = 1
        form = SearchPbiRecord(request.POST)
        if form.is_valid():
            if form.cleaned_data['stuname']:
                stuname = form.cleaned_data['stuname']
                try:
                    first_name = stuname.split(" ")[0]
                    last_name = stuname.split(" ")[1]
                except:
                    first_name = stuname
                    last_name = ''
            else:
                stuname = ''
                first_name = ''
                last_name = ''
            if form.cleaned_data['ctc']:
                ctc = form.cleaned_data['ctc']
            else:
                ctc = 0
            if form.cleaned_data['cname']:
                cname = form.cleaned_data['cname']
            else:
                cname = ''
            if form.cleaned_data['roll']:
                rollno = form.cleaned_data['roll']
            else:
                rollno = ''
            if form.cleaned_data['year']:
                year = form.cleaned_data['year']
                pbirecord = StudentRecord.objects.filter(Q(record_id__in=PlacementRecord.objects.filter
                                                       (Q(placement_type="PBI",
                                                          name__icontains=cname,
                                                          ctc__gte=ctc, year=year)),
                                                       unique_id__in=Student.objects.filter
                                                       ((Q(id__in=ExtraInfo.objects.filter
                                                           (Q(user__in=User.objects.filter
                                                              (Q(first_name__icontains=first_name,
                                                            last_name__icontains=last_name)),
                                                              id__icontains=rollno))
                                                           )))))
            else:
                pbirecord = StudentRecord.objects.filter(Q(record_id__in=PlacementRecord.objects.filter
                                                       (Q(placement_type="PBI",
                                                          name__icontains=cname,
                                                          ctc__gte=ctc)),
                                                       unique_id__in=Student.objects.filter
                                                       ((Q(id__in=ExtraInfo.objects.filter
                                                           (Q(user__in=User.objects.filter
                                                              (Q(first_name__icontains=first_name,
                                                            last_name__icontains=last_name)),
                                                              id__icontains=rollno))
                                                           )))))
            request.session['first_name'] = first_name
            request.session['last_name'] = last_name
            request.session['ctc'] = ctc
            request.session['cname'] = cname
            request.session['rollno'] = rollno
            request.session['year'] = form.cleaned_data['year']

            total_query = pbirecord.count()

            if total_query > 30:
                pagination_pbi = 1
                paginator = Paginator(pbirecord, 30)
                page = request.GET.get('page', 1)
                pbirecord = paginator.page(page)
                page = int(page)
                total_page = int(page + 3)

                if page<(paginator.num_pages-3):
                    if total_query > 30 and total_query <=60:
                        page_range = range(1, 3)
                    else:
                        page_range = range(1, total_page+1)

                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, total_page)
                else:
                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, paginator.num_pages+1)
                    else:
                        page_range = range(1, paginator.num_pages+1)
            else:
                pagination_pbi = 0
    else:
        if request.GET.get('page') != None:
            print('--------------------page value none')
            try:
                if request.session['year']:
                    pbirecord = StudentRecord.objects.filter(
                        Q(record_id__in=PlacementRecord.objects.filter(
                        Q(placement_type="PBI",
                        name__icontains=request.session['cname'],
                        ctc__gte=ctc, year=request.session['year'])),
                        unique_id__in=Student.objects.filter((
                        Q(id__in=ExtraInfo.objects.filter(
                        Q(user__in=User.objects.filter(
                        Q(first_name__icontains=request.session['first_name'],
                        last_name__icontains=request.session['last_name'])),
                        id__icontains=request.session['rollno'])))))))
                else:
                    pbirecord = StudentRecord.objects.filter(
                        Q(record_id__in=PlacementRecord.objects.filter(Q(placement_type="PBI",
                                                              name__icontains=request.session['cname'],
                                                              ctc__gte=request.session['ctc'])),
                                                           unique_id__in=Student.objects.filter(
                                                            (Q(id__in=ExtraInfo.objects.filter(
                                                            Q(user__in=User.objects.filter(
                        Q(first_name__icontains=request.session['first_name'],
                        last_name__icontains=request.session['last_name'])),
                        id__icontains=request.session['rollno'])))))))
            except:
                print('except')
                pbirecord = ''

            if pbirecord != '':
                total_query = pbirecord.count()
            else:
                total_query = 0

            if total_query > 30:
                pagination_pbi = 1
                paginator = Paginator(pbirecord, 30)
                page = request.GET.get('page', 1)
                pbirecord = paginator.page(page)
                page = int(page)
                total_page = int(page + 3)

                if page<(paginator.num_pages-3):
                    if total_query > 30 and total_query <=60:
                        page_range = range(1, 3)
                    else:
                        page_range = range(1, total_page+1)

                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, total_page)
                else:
                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, paginator.num_pages+1)
                    else:
                        page_range = range(1, paginator.num_pages+1)
            else:
                pagination_pbi = 0
        else:
            pbirecord = ''

    # results of the searched query under higher studies tab
    if 'studenthigherrecordsubmit' in request.POST:
        officer_statistics_past_higher_search = 1
        form = SearchHigherRecord(request.POST)
        if form.is_valid():
            # getting all the variables send through form
            if form.cleaned_data['stuname']:
                stuname = form.cleaned_data['stuname']
                try:
                    first_name = stuname.split(" ")[0]
                    last_name = stuname.split(" ")[1]
                except:
                    first_name = stuname
                    last_name = ''
            else:
                stuname = ''
                first_name = ''
                last_name = ''
            if form.cleaned_data['test_type']:
                test_type = form.cleaned_data['test_type']
            else:
                test_type = ''
            if form.cleaned_data['uname']:
                uname = form.cleaned_data['uname']
            else:
                uname = ''
            if form.cleaned_data['test_score']:
                test_score = form.cleaned_data['test_score']
            else:
                test_score = 0
            if form.cleaned_data['roll']:
                rollno = form.cleaned_data['roll']
            else:
                rollno = ''
            if form.cleaned_data['year']:
                year = form.cleaned_data['year']
                # result of the query when year is given
                higherrecord = StudentRecord.objects.filter(Q(record_id__in=PlacementRecord.objects.filter
                                                       (Q(placement_type="HIGHER STUDIES",
                                                          test_type__icontains=test_type,
                                                          name__icontains=uname, year=year,
                                                          test_score__gte=test_score)),
                                                       unique_id__in=Student.objects.filter
                                                       ((Q(id__in=ExtraInfo.objects.filter
                                                           (Q(user__in=User.objects.filter
                                                              (Q(first_name__icontains=first_name,
                                                            last_name__icontains=last_name)),
                                                              id__icontains=rollno))
                                                           )))))
            else:
                # result of the query when year is not given
                higherrecord = StudentRecord.objects.filter(
                    Q(record_id__in=PlacementRecord.objects.filter
                                                       (Q(placement_type="HIGHER STUDIES",
                                                          test_type__icontains=test_type,
                                                          name__icontains=uname,
                                                          test_score__gte=test_score)),
                                                       unique_id__in=Student.objects.filter
                                                       ((Q(id__in=ExtraInfo.objects.filter
                                                           (Q(user__in=User.objects.filter
                                                              (Q(first_name__icontains=first_name,
                                                                last_name__icontains=last_name)),
                                                              id__icontains=rollno))
                                                           )))))
            request.session['first_name'] = first_name
            request.session['last_name'] = last_name
            request.session['test_score'] = test_score
            request.session['uname'] = uname
            request.session['test_type'] = test_type
            request.session['rollno'] = rollno
            request.session['year'] = form.cleaned_data['year']

            total_query = higherrecord.count()

            if total_query > 30:
                pagination_higher = 1
                paginator = Paginator(higherrecord, 30)
                page = request.GET.get('page', 1)
                higherrecord = paginator.page(page)
                page = int(page)
                total_page = int(page+3)

                if page < (paginator.num_pages-3):
                    if total_query > 30 and total_query <= 60:
                        page_range = range(1, 3)
                    else:
                        page_range = range(1, total_page+1)

                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, total_page)
                else:
                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, paginator.num_pages+1)
                    else:
                        page_range = range(page-2, paginator.num_pages+1)
            else:
                pagination_higher = 0
    else:
        if request.GET.get('page') != None:
            try:
                if request.session['year']:
                    higherrecord = StudentRecord.objects.filter(
                        Q(record_id__in=PlacementRecord.objects.filter(
                            Q(placement_type="HIGHER STUDIES",
                              test_type__icontains=request.session['test_type'],
                              name__icontains=request.session['uname'],
                              year=request.session['year'],
                              test_score__gte=request.session['test_score'])),
                           unique_id__in=Student.objects.filter(
                            (Q(id__in=ExtraInfo.objects.filter(
                                Q(user__in=User.objects.filter(
                                Q(first_name__icontains=request.session['first_name'],
                                last_name__icontains=request.session['last_name'])),
                                id__icontains=request.session['rollno']))
                               )))))
                else:
                    higherrecord = StudentRecord.objects.filter(
                        Q(record_id__in=PlacementRecord.objects.filter(
                            Q(placement_type="HIGHER STUDIES",
                          test_type__icontains=request.session['test_type'],
                          name__icontains=request.session['uname'],
                          test_score__gte=request.session['test_score'])),
                       unique_id__in=Student.objects.filter
                       ((Q(id__in=ExtraInfo.objects.filter(
                        Q(user__in=User.objects.filter(
                            Q(first_name__icontains=request.session['first_name'],
                        last_name__icontains=request.session['last_name'])),
                              id__icontains=request.session['rollno']))
                           )))))
            except:
                higherrecord = ''

            if higherrecord != '':
                total_query = higherrecord.count()
            else:
                total_query = 0

            if total_query > 30:
                no_pagination = 1
                paginator = Paginator(higherrecord, 30)
                page = request.GET.get('page', 1)
                higherrecord = paginator.page(page)
                page = int(page)
                total_page = int(page + 3)

                if page<(paginator.num_pages-3):
                    if total_query > 30 and total_query <=60:
                        page_range = range(1, 3)
                    else:
                        page_range = range(1, total_page+1)

                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, total_page)
                else:
                    if page >= 5:
                        is_disabled = 1
                        page_range = range(page-2, paginator.num_pages+1)
                    else:
                        page_range = range(1, paginator.num_pages+1)
            else:
                no_pagination = 0
        else:
            higherrecord = ''


    context = {
        'form2'             :            form2,
        'form3'             :            form3,
        'form4'             :            form4,
        'current'           :          current,
        'current1'          :         current1,
        'current2'          :         current2,
        'statistics_tab'    :   statistics_tab,
        'pbirecord'         :        pbirecord,
        'placementrecord'   :  placementrecord,
        'higherrecord'      :     higherrecord,
        'years'             :            years,
        'records'           :          records,
        'delete_operation'  :       delete_operation,
        'page_range': page_range,
        'paginator': paginator,
        'pagination_placement': pagination_placement,
        'pagination_pbi': pagination_pbi,
        'pagination_higher': pagination_higher,
        'is_disabled': is_disabled,
        'officer_statistics_past_pbi_search': officer_statistics_past_pbi_search,
        'officer_statistics_past_higher_search': officer_statistics_past_higher_search
    }

    return render(request, 'placementModule/placementstatistics.html', context)


@login_required
def delete_placement_statistics(request):
    """
    The function is used to delete the placement statistic record.
    @param:
            request - trivial
    @variables:
            record_id = stores current StudentRecord Id.
    """
    print('coming delete request')
    if 'deleterecord' in request.POST or 'deleterecordmanaged' in request.POST:
        try:
            if 'deleterecord' in request.POST:
                record_id = int(request.POST['deleterecord'])
            elif 'deleterecordmanaged' in request.POST:
                record_id = int(request.POST['deleterecordmanaged'])

            print('------------------------\n\n\n')
            print(record_id)
            print(StudentRecord.objects.get(pk = record_id))
            student_record =  StudentRecord.objects.get(pk=record_id)
            print('-asdasdasda', PlacementRecord.objects.get(pk=student_record.record_id.id))
            PlacementRecord.objects.get(id=student_record.record_id.id).delete()
            student_record.delete()
            messages.success(request, 'Placement Statistics deleted Successfully!!')

        except Exception as e:
            messages.error(request, 'Problem Occurred!! Please Try Again!!')
            print(e)
            print('------------problem in deleting the record of statistics-------------')


    if 'deleterecordmanaged' in request.POST:
        return redirect('/placement/manage_records/')

    return redirect('/placement/statistics/')


def cv(request, username):
    print('first coming to function ---------------------\n\n\n')
    # Retrieve data or whatever you need
    """
    The function is used to generate the cv in the pdf format.
    Embeds the data into the predefined template.
    @param:
            request - trivial
            username - name of user whose cv is to be generated
    @variables:
            user = stores current user
            profile = stores extrainfo of user
            current = Stores all working students from HoldsDesignation for the respective degignation
            achievementcheck = variable for achievementcheck in form for cv generation
            educationcheck = variable for educationcheck in form for cv generation
            publicationcheck = variable for publicationcheck in form for cv generation
            patentcheck = variable for patentcheck in form for cv generation
            internshipcheck = variable for internshipcheck in form for cv generation
            projectcheck = variable for projectcheck in form for cv generation
            coursecheck = variable for coursecheck in form for cv generation
            skillcheck = variable for skillcheck in form for cv generation
            user = get_object_or_404(User, Q(username=username))
            profile = get_object_or_404(ExtraInfo, Q(user=user))
            import datetime
            now = stores current timestamp
            roll = roll of the user
            student = variable storing the profile data
            studentplacement = variable storing the placement data
            skills = variable storing the skills data
            education = variable storing the education data
            course = variable storing the course data
            experience = variable storing the experience data
            project = variable storing the project data
            achievement = variable storing the achievement data
            publication = variable storing the publication data
            patent = variable storing the patent data
    """
    user = request.user
    profile = get_object_or_404(ExtraInfo, Q(user=user))

    current = HoldsDesignation.objects.filter(Q(working=user, designation__name="student"))
    if current:
        if request.method == 'POST':
            achievementcheck = request.POST.get('achievementcheck')
            educationcheck = request.POST.get('educationcheck')
            publicationcheck = request.POST.get('publicationcheck')
            patentcheck = request.POST.get('patentcheck')
            internshipcheck = request.POST.get('internshipcheck')
            projectcheck = request.POST.get('projectcheck')
            coursecheck = request.POST.get('coursecheck')
            skillcheck = request.POST.get('skillcheck')
            reference_list = request.POST.getlist('reference_checkbox_list')
            extracurricularcheck = request.POST.get('extracurricularcheck')
            conferencecheck =  request.POST.get('conferencecheck')
    else:
        conferencecheck = '1'
        achievementcheck = '1'
        educationcheck = '1'
        publicationcheck = '1'
        patentcheck = '1'
        internshipcheck = '1'
        projectcheck = '1'
        coursecheck = '1'
        skillcheck = '1'
        extracurricularcheck = '1'


    # print(achievementcheck,' ',educationcheck,' ',publicationcheck,' ',patentcheck,' ',internshipcheck,' ',projectcheck,' \n\n\n')
    user = get_object_or_404(User, Q(username=username))
    profile = get_object_or_404(ExtraInfo, Q(user=user))
    now = datetime.datetime.now()
    if int(str(profile.id)[:2]) == 20:
        if (now.month>4):
          roll = 1+now.year-int(str(profile.id)[:4])
        else:
          roll = now.year-int(str(profile.id)[:4])
    else:
        if (now.month>4):
          roll = 1+(now.year)-int("20"+str(profile.id)[0:2])
        else:
          roll = (now.year)-int("20"+str(profile.id)[0:2])

    student = get_object_or_404(Student, Q(id=profile.id))
    skills = Has.objects.filter(Q(unique_id=student))
    education = Education.objects.filter(Q(unique_id=student))
    reference = Reference.objects.filter(id__in=reference_list)
    course = Course.objects.filter(Q(unique_id=student))
    experience = Experience.objects.filter(Q(unique_id=student))
    project = Project.objects.filter(Q(unique_id=student))
    achievement = Achievement.objects.filter(Q(unique_id=student))
    extracurricular = Extracurricular.objects.filter(Q(unique_id=student))
    conference = Conference.objects.filter(Q(unique_id=student))
    publication = Publication.objects.filter(Q(unique_id=student))
    patent = Patent.objects.filter(Q(unique_id=student))
    today = datetime.date.today()

    if len(reference) == 0:
        referencecheck = '0'
    else:
        referencecheck = '1'

    return render_to_pdf('placementModule/cv.html', {'pagesize': 'A4', 'user': user, 'references': reference,
                                                     'profile': profile, 'projects': project,
                                                     'skills': skills, 'educations': education,
                                                     'courses': course, 'experiences': experience,
                                                     'referencecheck': referencecheck,
                                                     'achievements': achievement,
                                                     'extracurriculars': extracurricular,
                                                     'publications': publication,
                                                     'patents': patent, 'roll': roll,
                                                     'achievementcheck': achievementcheck,
                                                     'extracurricularcheck': extracurricularcheck,
                                                     'educationcheck': educationcheck,
                                                     'publicationcheck': publicationcheck,
                                                     'patentcheck': patentcheck,
                                                     'conferencecheck': conferencecheck,
                                                     'conferences': conference,
                                                     'internshipcheck': internshipcheck,
                                                     'projectcheck': projectcheck,
                                                     'coursecheck': coursecheck,
                                                     'skillcheck': skillcheck,
                                                     'today':today})


def render_to_pdf(template_src, context_dict):
    """
    The function is used to generate the cv in the pdf format.
    Embeds the data into the predefined template.
    @param:
            template_src - template of cv to be rendered
            context_dict - data fetched from the dtatabase to be filled in the cv template
    @variables:
            template - stores the template
            html - html rendered pdf
            result - variable to store data in BytesIO
            pdf - storing encoded html of pdf version
    """
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse('We had some errors<pre>%s</pre>' % escape(html))


def export_to_xls_std_records(qs):
    """
    The function is used to generate the file in the xls format.
    Embeds the data into the file.
    """
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="report.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Report')

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Roll No.', 'Name', 'CPI', 'Department', 'Discipline', 'Placed', 'Debarred' ]

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    for student in qs:
        row_num += 1

        row = []
        row.append(student.id.id)
        row.append(student.id.user.first_name+' '+student.id.user.last_name)
        row.append(student.cpi)
        row.append(student.programme)
        row.append(student.id.department.name)
        if student.studentplacement.placed_type == "PLACED":
            row.append('Yes')
        else:
            row.append('No')
        if student.studentplacement.placed_type == "DEBAR":
            row.append('Yes')
        else:
            row.append('No')

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    wb.save(response)
    return response


def export_to_xls_invitation_status(qs):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="report.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Report')

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Roll No.', 'Name', 'Company', 'CTC', 'Invitation Status']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    for student in qs:
        row_num += 1

        row = []
        row.append(student.unique_id.id.id)
        row.append(student.unique_id.id.user.first_name+' '+student.unique_id.id.user.last_name)
        row.append(student.notify_id.company_name)
        row.append(student.notify_id.ctc)
        row.append(student.invitation)

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    wb.save(response)
    return response


def check_invitation_date(placementstatus):
    """
    The function is used to run before render of student placement view for ensuring that
    last date for RESPONSE is not passed
    @param:
            placementstatus - queryset containing placement status of particular student
    @variables:
            ps - individual PlacementStatus object
    """
    try:
        for ps in placementstatus:
            if ps.invitation=='PENDING':
                dt = ps.timestamp+datetime.timedelta(days=ps.no_of_days)
                if dt<datetime.datetime.now():
                    #print('---------- time limit is finished---------------- \n\n\n\n\n')
                    ps.invitation = 'IGNORE'
                    ps.save()
    except Exception as e:
        print('---------------------Error Occurred ---------------')
        print(e)

    return













































































'''
    OLD CODE
'''

# @login_required
# def placement(request):

#     student_record_check = 0
#     officer_manage = 0
#     officer_manage_pbi = 0
#     officer_statistics_past = 0
#     officer_statistics_past_add = 0
#     officer_statistics_past_pbi_search = 0
#     officer_statistics_past_pbi_add = 0
#     officer_statistics_past_higher_search = 0
#     officer_statistics_past_higher_add = 0
#     chairman_visit_add = 0
#     invitecheck=0

#     placementrecord = 1
#     pbirecord = 1
#     higherrecord = 1
#     studentplacement = []
#     page_range = ''
#     paginator = ''
#     is_disabled = 0
#     no_pagination = 1

#     if 'std' in cache:
#         student_record_check= 1
#         students = cache.get('std')
#         total_query = students.count()

#         if total_query > 30:
#             paginator = Paginator(students, 30)
#             page = request.GET.get('page', 1)
#             students = paginator.page(page)
#             print(paginator.num_pages)
#             print(page)
#             page = int(page)
#             total_page = int(page + 3)

#             if page<(paginator.num_pages-3):
#                 if total_query > 30 and total_query <=60:
#                     page_range = range(1, 3)
#                 else:
#                     page_range = range(1, total_page+1)

#                 if page >= 5:
#                     is_disabled = 1
#                     page_range = range(page-2, total_page)
#             else:
#                 if page >= 5:
#                     is_disabled = 1
#                     page_range = range(page-2, paginator.num_pages+1)
#                 else:
#                     page_range = range(1, paginator.num_pages+1)
#         else:
#             no_pagination = 0
#     else:
#         students = ''

#     user = request.user

#     profile = get_object_or_404(ExtraInfo, Q(user=user))
#     studentrecord = StudentRecord.objects.all()

#     form5 = AddSchedule(initial={})

#     years = PlacementRecord.objects.filter(~Q(placement_type="HIGHER STUDIES")).values('year').annotate(Count('year'))
#     records = PlacementRecord.objects.values('name', 'year', 'ctc', 'placement_type').annotate(Count('name'), Count('year'), Count('placement_type'), Count('ctc'))

#     current1 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement chairman"))
#     current2 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement officer"))
#     schedules = PlacementSchedule.objects.all()


#     invitecheck=0;
#     if 'sendinvite' in request.POST:
#         invitecheck=1;
#         form13 = SendInvite(request.POST)
#         if form13.is_valid():
#             if form13.cleaned_data['company']:
#                 comp = form13.cleaned_data['company']
#                 com = [comp.company_name, comp.placement_type]
#                 notify = NotifyStudent.objects.get(company_name=com[0],
#                                                    placement_type=com[1])
#                 if 'q' not in request.session:
#                     stud = Student.objects.all()
#                 else:
#                     q = request.session['q']
#                     p = []
#                     for w in q:
#                         p.append(w['id_id'])
#                         stud = Student.objects.filter(Q(id__in=p))
#                 for student in stud:
#                     status = PlacementStatus.objects.create(notify_id=notify,
#                                                             unique_id=student,
#                                                             timestamp=timezone.now())
#                     status.save()


#     form1 = SearchStudentRecord(initial={})
#     form = AddChairmanVisit(initial={})
#     form2 = SearchPlacementRecord(initial={})
#     form3 = SearchPbiRecord(initial={})
#     form4 = SearchHigherRecord(initial={})
#     form11 = ManagePlacementRecord(initial={})
#     form9 = ManagePbiRecord(initial={})
#     form10 = ManageHigherRecord(initial={})
#     form13 = SendInvite(initial={})
#     chairmanvisit = ChairmanVisit.objects.all()
#     context = {'user': user, 'form5':form5, 'form1': form1, 'form13': form13, 'form11': form11, 'form9': form9,
#                'schedules':schedules,'studentrecord':studentrecord, 'form2': form2, 'form3':form3,
#                 'form4': form4, 'years': years, 'records': records, 'page_range': page_range, 'paginator': paginator,
#                'placementrecord':placementrecord, 'higherrecord':higherrecord, 'students': students,
#                'pbirecord':pbirecord, 'current1':current1, 'invitecheck':invitecheck, 'profile': profile,
#                'current2':current2, 'student_record_check': student_record_check, 'is_disabled': is_disabled,
#                'officer_manage': officer_manage, 'officer_manage_pbi': officer_manage_pbi,
#                'officer_statistics_past': officer_statistics_past, 'officer_statistics_past_add': officer_statistics_past_add,
#                'officer_statistics_past_pbi_search': officer_statistics_past_pbi_search, 'officer_statistics_past_pbi_add':
#                officer_statistics_past_pbi_add, 'officer_statistics_past_higher_add': officer_statistics_past_higher_add,
#                'officer_statistics_past_higher_search': officer_statistics_past_higher_search,
#                'chairman_visit_add': chairman_visit_add, 'no_pagination': no_pagination
#     }
#     print('heer')
#     return render(request, "placementModule/placement.html", context)




# def ScheduleSubmit(request):
#     print('\n\n coming--add schedule\n\n')
#     if 'schedulesubmit' in request.POST:
#         form5 = AddSchedule(request.POST, request.FILES)
#         if form5.is_valid():
#             company_name = form5.cleaned_data['company_name']
#             placement_date = form5.cleaned_data['placement_date']
#             location = form5.cleaned_data['location']
#             ctc = form5.cleaned_data['ctc']
#             time = form5.cleaned_data['time']
#             attached_file = form5.cleaned_data['attached_file']
#             placement_type = form5.cleaned_data['placement_type']
#             description = form5.cleaned_data['description']
#             notify = NotifyStudent.objects.create(placement_type=placement_type,
#                                                   company_name=company_name,
#                                                   description=description,
#                                                   ctc=ctc,
#                                                   timestamp=timezone.now())

#             schedule = PlacementSchedule.objects.create(notify_id=notify,
#                                                         title=company_name,
#                                                         description=description,
#                                                         placement_date=placement_date,
#                                                         attached_file = attached_file,
#                                                         location=location, time=time)
#             notify.save()
#             schedule.save()

#     else:
#         if 'delete_sch_key' in request.POST:
#             delete_sch_key = request.POST['delete_sch_key']
#             try:
#                 PlacementSchedule.objects.get(pk = delete_sch_key).delete()
#                 NotifyStudent.objects.get(pk = delete_sch_key).delete()
#             except Exception as e:
#                 print('---- \n\n record not found')

#     return redirect('/placement/')


# def SearchRecord(request):

#     if 'recordsubmit' in request.POST:
#         print('search')
#         student_record_check = 1
#         form1 = SearchStudentRecord(request.POST)
#         if form1.is_valid():
#             print('valid')
#             if form1.cleaned_data['name']:
#                 name = form1.cleaned_data['name']
#             else:
#                 name = ''
#             if form1.cleaned_data['rollno']:
#                 rollno = form1.cleaned_data['rollno']
#             else:
#                 rollno = ''
#             programme = form1.cleaned_data['programme']
#             if form1.cleaned_data['department']:
#                 department = form1.cleaned_data['department']
#             else:
#                 department = ''
#             if form1.cleaned_data['cpi']:
#                 cpi = form1.cleaned_data['cpi']
#             else:
#                 cpi = 0
#             debar = form1.cleaned_data['debar']
#             placed_type = form1.cleaned_data['placed_type']

#             students = Student.objects.filter(Q(id__in=ExtraInfo.objects.filter(Q(user__in=User.objects.filter(Q(first_name__icontains=name)),
#                 department__in=DepartmentInfo.objects.filter(Q(name__icontains=department)),
#                 id__icontains=rollno)),
#                 programme=programme,
#                 cpi__gte=cpi)).filter(Q(pk__in=StudentPlacement.objects.filter(Q(debar=debar, placed_type=placed_type)).values('unique_id_id'))).order_by('id')

#             st = students

#             cache.set('std', students)

#             return redirect('/placement/')


# def ManageRecords(request):
#     user = request.user
#     profile = get_object_or_404(ExtraInfo, Q(user=user))
#     officer_manage = 0
#     officer_manage_pbi = 0

#     current1 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement chairman"))
#     current2 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement officer"))

#     if 'studentplacementsearchsubmit' in request.POST:
#         print('coming')
#         officer_manage = 1
#         form = ManagePlacementRecord(request.POST)
#         if form.is_valid():
#             if form.cleaned_data['stuname']:
#                 stuname = form.cleaned_data['stuname']
#             else:
#                 stuname = ''
#             if form.cleaned_data['ctc']:
#                 ctc = form.cleaned_data['ctc']
#             else:
#                 ctc = 0
#             if form.cleaned_data['company']:
#                 cname = form.cleaned_data['company']
#             else:
#                 cname = ''
#             if form.cleaned_data['roll']:
#                 rollno = form.cleaned_data['roll']
#             else:
#                 rollno = ''
#             placementstatus = PlacementStatus.objects.filter(Q(notify_id__in=NotifyStudent.objects.filter
#                                                        (Q(placement_type="PLACEMENT",
#                                                           company_name__icontains=cname,
#                                                           ctc__gte=ctc)),
#                                                        unique_id__in=Student.objects.filter
#                                                        ((Q(id__in=ExtraInfo.objects.filter
#                                                            (Q(user__in=User.objects.filter
#                                                               (Q(first_name__icontains=stuname)),
#                                                               id__icontains=rollno))
#                                                            )))))
#     elif 'studentpbisearchsubmit' in request.POST:
#         officer_manage_pbi = 1
#         form = ManagePbiRecord(request.POST)
#         if form.is_valid():
#             if form.cleaned_data['stuname']:
#                 stuname = form.cleaned_data['stuname']
#             else:
#                 stuname = ''
#             if form.cleaned_data['ctc']:
#                 ctc = form.cleaned_data['ctc']
#             else:
#                 ctc = 0
#             if form.cleaned_data['company']:
#                 cname = form.cleaned_data['company']
#             else:
#                 cname = ''
#             if form.cleaned_data['roll']:
#                 rollno = form.cleaned_data['roll']
#             else:
#                 rollno = ''
#             placementstatus = PlacementStatus.objects.filter(Q(notify_id__in=NotifyStudent.objects.filter
#                                                        (Q(placement_type="PBI",
#                                                           company_name__icontains=cname,
#                                                           ctc__gte=ctc)),
#                                                        unique_id__in=Student.objects.filter
#                                                        ((Q(id__in=ExtraInfo.objects.filter
#                                                            (Q(user__in=User.objects.filter
#                                                               (Q(first_name__icontains=stuname)),
#                                                               id__icontains=rollno))
#                                                            )))))
#     else:
#         placementstatus = []

#     current = HoldsDesignation.objects.filter(Q(working=user, designation__name="student"))
#     if current:
#         student = get_object_or_404(Student, Q(id=profile.id))
#         placementschedule = PlacementSchedule.objects.filter(
#             Q(placement_date__gte=date.today())).values_list('notify_id',
#             flat=True)
#         placementstatus = PlacementStatus.objects.filter(Q(unique_id=student,
#                                                             notify_id__in=placementschedule
#                                                             )).order_by('-timestamp')

#     context = {
#         'placementstatus': placementstatus, 'officer_manage': officer_manage,
#         'officer_manage_pbi': officer_manage_pbi, 'current1': current1, 'current2': current2,
#     }

#     return render(request, "placementModule/placement.html", context)



# def html_to_pdf_view(request):
#     students = cache.get('std')
#     context = {
#         'students': students,
#     }
#     template = get_template('placementModule/pdf_demo.html')
#     html = template.render(context)

#     result = BytesIO()
#     pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
#     if not pdf.err:
#         return HttpResponse(result.getvalue(), content_type='application/pdf')
#     return HttpResponse('We had some errors<pre>%s</pre>' % escape(html))



# def render_to_pdf(template_src, context_dict):
#     """
#     The function is used to generate the cv in the pdf format.
#     Embeds the data into the predefined template.
#     @param:
#             template_src - template of cv to be rendered
#             context_dict - data fetched from the dtatabase to be filled in the cv template
#     @variables:
#             template - stores the template
#             html - html rendered pdf
#             result - variable to store data in BytesIO
#             pdf - storing encoded html of pdf version
#     """
#     template = get_template(template_src)
#     html = template.render(context_dict)
#     result = BytesIO()
#     pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
#     if not pdf.err:
#         return HttpResponse(result.getvalue(), content_type='application/pdf')
#     return HttpResponse('We had some errors<pre>%s</pre>' % escape(html))












# @login_required
# def placement(request):
#     student_record_check = 0
#     officer_manage = 0
#     officer_manage_pbi = 0
#     officer_statistics_past = 0
#     officer_statistics_past_add = 0
#     officer_statistics_past_pbi_search = 0
#     officer_statistics_past_pbi_add = 0
#     officer_statistics_past_higher_search = 0
#     officer_statistics_past_higher_add = 0
#     chairman_visit_add = 0
#     """
#     The function is used to placement related functionality/usecases.
#     @param:
#             request - trivial
#     @variables:
#             user - logged in user
#             profile - variable for extrainfo
#             studentrecord - storing all fetched student record from database
#             years - yearwise record of student placement
#             records - all the record of placement record table
#             tcse - all record of cse
#             tece - all record of ece
#             tme - all record of me
#             tadd - all record of student
#             form respective form object
#             stuname - student name obtained from the form
#             ctc - salary offered obtained from the form
#             cname - company name obtained from the form
#             rollno - roll no of student obtained from the form
#             year - year of placement obtained from the form
#             s - extra info data of the student obtained from the form
#             p - placement data of the student obtained from the form
#             placementrecord - placement record of the student obtained from the form
#             pbirecord - pbi data of the student obtained from the form
#             test_type - type of higher study test obtained from the form
#             uname - name of universty obtained from the form
#             test_score - score in the test obtained from the form
#             higherrecord - higher study record of the student obtained from the form
#             current - current user on a particular designation
#             status - status of the sent invitation by placement cell regarding placement/pbi
#             institute - institute for previous education obtained from the form
#             degree - degree for previous education obtained from the form
#             grade - grade for previous education obtained from the form
#             stream - stream for previous education obtained from the form
#             sdate - start date for previous education obtained from the form
#             edate - end date for previous education obtained from the form
#             education_obj - object variable of Education table
#             about_me - about me data obtained from the form
#             age - age data obtained from the form
#             address - address obtained from the form
#             contact - contact obtained from the form
#             pic - picture obtained from the form
#             skill - skill of the user obtained from the form
#             skill_rating - rating of respective skill obtained from the form
#             has_obj - object variable of Has table
#             achievement - achievement of user obtained from the form
#             achievement_type - type of achievement obtained from the form
#             description - description of respective achievement obtained from the form
#             issuer - certifier of respective achievement obtained from the form
#             date_earned - date of the respective achievement obtained from the form
#             achievement_obj - object variable of Achievement table
#             publication_title - title of the publication obtained from the form
#             description - description of respective publication obtained from the form
#             publisher - publisher of respective publication obtained from the form
#             publication_date - date of respective publication obtained from the form
#             publication_obj - object variable of Publication table
#             patent_name - name of patent obtained from the form
#             description - description of respective patent obtained from the form
#             patent_office - office of respective patent obtained from the form
#             patent_date - date of respective patent obtained from the form
#             patent_obj - object variable of Patent table
#             course_name - name of the course obtained from the form
#             description description of respective course obtained from the form
#             license_no - license_no of respective course obtained from the form
#             sdate - start date of respective course obtained from the form
#             edate - end date of respective course obtained from the form
#             course_obj - object variable of Course table
#             project_name - name of project obtained from the form
#             project_status - status of respective project obtained from the form
#             summary - summery of the respective project obtained from the form
#             project_link - link of the respective project obtained from the form
#             sdate - start date of respective project obtained from the form
#             edate - end date of respective project obtained from the form
#             project_obj - object variable of Project table
#             title - title of any kind of experience obtained from the form
#             status - status of the respective experience obtained from the form
#             company - company from which respective experience is gained as obtained from the form
#             location - location of the respective experience obtained from the form
#             description - description of respective experience obtained from the form
#             sdate - start date of respective experience obtained from the form
#             edate - end date of respective experience obtained from the form
#             experience_obj - object variable of Experience table
#             context - to sent the relevant context for html rendering
#             company_name - name of visiting comapany obtained from the form
#             location -location of visiting company obtained from the form
#             description - description of respective company obtained from the form
#             visiting_date - visiting date of respective company obtained from the form
#             visit_obj -object variable of ChairmanVisit table
#             notify - object of NotifyStudent table
#             schedule - object variable of PlacementSchedule table
#             q1 - all data of Has table
#             q3 - all data of Student table
#             st - all data of Student table
#             spid - id of student to be debar
#             sr - record from StudentPlacement of student having id=spid
#             achievementcheck - checking for achievent to be shown in cv
#             educationcheck - checking for education to be shown in cv
#             publicationcheck - checking for publication to be shown in cv
#             patentcheck - checking for patent to be shown in cv
#             internshipcheck - checking for internship to be shown in cv
#             projectcheck - checking for project to be shown in cv
#             coursecheck - checking for course to be shown in cv
#             skillcheck - checking for skill to be shown in cv
#     """

#     form5 = AddSchedule()
#     user = request.user
#     profile = get_object_or_404(ExtraInfo, Q(user=user))
#     studentrecord = StudentRecord.objects.all()
#     years = PlacementRecord.objects.filter(~Q(placement_type="HIGHER STUDIES")).values('year').annotate(Count('year'))
#     records = PlacementRecord.objects.values('name', 'year', 'ctc', 'placement_type').annotate(Count('name'), Count('year'), Count('placement_type'), Count('ctc'))
#     invitecheck=0;
#     for r in records:
#         r['name__count'] = 0
#         r['year__count'] = 0
#         r['placement_type__count'] = 0
#     tcse = dict()
#     tece = dict()
#     tme = dict()
#     tadd = dict()
#     for y in years:
#         tcse[y['year']] = 0
#         tece[y['year']] = 0
#         tme[y['year']] = 0
#         for r in records:
#             if r['year'] == y['year']:
#                 if r['placement_type'] != "HIGHER STUDIES":
#                     for z in studentrecord:
#                         if z.record_id.name == r['name'] and z.record_id.year == r['year'] and z.unique_id.id.department.name == "CSE":
#                             tcse[y['year']] = tcse[y['year']]+1
#                             r['name__count'] = r['name__count']+1
#                         if z.record_id.name == r['name'] and z.record_id.year == r['year'] and z.unique_id.id.department.name == "ECE":
#                             tece[y['year']] = tece[y['year']]+1
#                             r['year__count'] = r['year__count']+1
#                         if z.record_id.name == r['name'] and z.record_id.year == r['year'] and z.unique_id.id.department.name == "ME":
#                             tme[y['year']] = tme[y['year']]+1
#                             r['placement_type__count'] = r['placement_type__count']+1
#         tadd[y['year']] = tcse[y['year']]+tece[y['year']]+tme[y['year']]
#         y['year__count'] = [tadd[y['year']], tcse[y['year']], tece[y['year']], tme[y['year']]]

#     print(tcse[y['year']])
    # if request.method == 'POST':
    #     if 'studentplacementrecordsubmit' in request.POST:
    #         officer_statistics_past = 1
    #         form = SearchPlacementRecord(request.POST)
    #         if form.is_valid():
    #             if form.cleaned_data['stuname']:
    #                 stuname = form.cleaned_data['stuname']
    #             else:
    #                 stuname = ''
    #             if form.cleaned_data['ctc']:
    #                 ctc = form.cleaned_data['ctc']
    #             else:
    #                 ctc = 0
    #             if form.cleaned_data['cname']:
    #                 cname = form.cleaned_data['cname']
    #             else:
    #                 cname = ''
    #             if form.cleaned_data['roll']:
    #                 rollno = form.cleaned_data['roll']
    #             else:
    #                 rollno = ''
    #             if form.cleaned_data['year']:
    #                 year = form.cleaned_data['year']
    #                 s = Student.objects.filter((Q(id__in=ExtraInfo.objects.filter
    #                     (Q(user__in=User.objects.filter
    #                        (Q(first_name__icontains=stuname)),
    #                        id__icontains=rollno))
    #                     )))

    #                 p = PlacementRecord.objects.filter(Q(placement_type="PLACEMENT", name__icontains=cname, ctc__gte=ctc, year=year))

    #                 placementrecord = StudentRecord.objects.filter(Q(record_id__in=PlacementRecord.objects.filter(Q(placement_type="PLACEMENT", name__icontains=cname, ctc__gte=ctc, year=year)), unique_id__in=Student.objects.filter((Q(id__in=ExtraInfo.objects.filter(Q(user__in=User.objects.filter(Q(first_name__icontains=stuname)),id__icontains=rollno)))))))
    #             else:
    #                 print('dfd')
    #                 s = Student.objects.filter((Q(id__in=ExtraInfo.objects.filter
    #                     (Q(user__in=User.objects.filter
    #                        (Q(first_name__icontains=stuname)),
    #                        id__icontains=rollno))
    #                     )))

    #                 p = PlacementRecord.objects.filter(Q(placement_type="PLACEMENT", name__icontains=cname, ctc__gte=ctc))

    #                 placementrecord = StudentRecord.objects.filter(Q(record_id__in=PlacementRecord.objects.filter(Q(placement_type="PLACEMENT", name__icontains=cname, ctc__gte=ctc)), unique_id__in=Student.objects.filter((Q(id__in=ExtraInfo.objects.filter(Q(user__in=User.objects.filter(Q(first_name__icontains=stuname)),id__icontains=rollno)))))))
    #     else:
    #         placementrecord = StudentRecord.objects.all()
    #     if 'studentpbirecordsubmit' in request.POST:
    #         officer_statistics_past_pbi_search = 1
    #         form = SearchPbiRecord(request.POST)
    #         if form.is_valid():
    #             if form.cleaned_data['stuname']:
    #                 stuname = form.cleaned_data['stuname']
    #             else:
    #                 stuname = ''
    #             if form.cleaned_data['ctc']:
    #                 ctc = form.cleaned_data['ctc']
    #             else:
    #                 ctc = 0
    #             if form.cleaned_data['cname']:
    #                 cname = form.cleaned_data['cname']
    #             else:
    #                 cname = ''
    #             if form.cleaned_data['roll']:
    #                 rollno = form.cleaned_data['roll']
    #             else:
    #                 rollno = ''
    #             if form.cleaned_data['year']:
    #                 year = form.cleaned_data['year']
    #                 pbirecord = StudentRecord.objects.filter(Q(record_id__in=PlacementRecord.objects.filter
    #                                                        (Q(placement_type="PBI",
    #                                                           name__icontains=cname,
    #                                                           ctc__gte=ctc, year=year)),
    #                                                        unique_id__in=Student.objects.filter
    #                                                        ((Q(id__in=ExtraInfo.objects.filter
    #                                                            (Q(user__in=User.objects.filter
    #                                                               (Q(first_name__icontains=stuname)),
    #                                                               id__icontains=rollno))
    #                                                            )))))
    #             else:
    #                 pbirecord = StudentRecord.objects.filter(Q(record_id__in=PlacementRecord.objects.filter
    #                                                        (Q(placement_type="PBI",
    #                                                           name__icontains=cname,
    #                                                           ctc__gte=ctc)),
    #                                                        unique_id__in=Student.objects.filter
    #                                                        ((Q(id__in=ExtraInfo.objects.filter
    #                                                            (Q(user__in=User.objects.filter
    #                                                               (Q(first_name__icontains=stuname)),
    #                                                               id__icontains=rollno))
    #                                                            )))))
    #     else:
    #         pbirecord = StudentRecord.objects.all()
    #     if 'studenthigherrecordsubmit' in request.POST:
    #         officer_statistics_past_higher_search = 1
    #         form = SearchHigherRecord(request.POST)
    #         if form.is_valid():
    #             if form.cleaned_data['stuname']:
    #                 stuname = form.cleaned_data['stuname']
    #             else:
    #                 stuname = ''
    #             if form.cleaned_data['test_type']:
    #                 test_type = form.cleaned_data['test_type']
    #             else:
    #                 test_type = ''
    #             if form.cleaned_data['uname']:
    #                 uname = form.cleaned_data['uname']
    #             else:
    #                 uname = ''
    #             if form.cleaned_data['test_score']:
    #                 test_score = form.cleaned_data['test_score']
    #             else:
    #                 test_score = 0
    #             if form.cleaned_data['roll']:
    #                 rollno = form.cleaned_data['roll']
    #             else:
    #                 rollno = ''
    #             if form.cleaned_data['year']:
    #                 year = form.cleaned_data['year']
    #                 higherrecord = StudentRecord.objects.filter(Q(record_id__in=PlacementRecord.objects.filter
    #                                                        (Q(placement_type="HIGHER STUDIES",
    #                                                           test_type__icontains=test_type,
    #                                                           name__icontains=uname, year=year,
    #                                                           test_score__gte=test_score)),
    #                                                        unique_id__in=Student.objects.filter
    #                                                        ((Q(id__in=ExtraInfo.objects.filter
    #                                                            (Q(user__in=User.objects.filter
    #                                                               (Q(first_name__icontains=stuname)),
    #                                                               id__icontains=rollno))
    #                                                            )))))
    #             else:
    #                 higherrecord = StudentRecord.objects.filter(Q(record_id__in=PlacementRecord.objects.filter
    #                                                        (Q(placement_type="HIGHER STUDIES",
    #                                                           test_type__icontains=test_type,
    #                                                           name__icontains=uname,
    #                                                           test_score__gte=test_score)),
    #                                                        unique_id__in=Student.objects.filter
    #                                                        ((Q(id__in=ExtraInfo.objects.filter
    #                                                            (Q(user__in=User.objects.filter
    #                                                               (Q(first_name__icontains=stuname)),
    #                                                               id__icontains=rollno))
    #                                                            )))))
    #     else:
    #         higherrecord = StudentRecord.objects.all()
    # else:
    #     placementrecord = 1
    #     pbirecord = 1
    #     higherrecord = 1
    # if 'studentplacementsearchsubmit' in request.POST:
    #     officer_manage = 1
    #     form = ManagePlacementRecord(request.POST)
    #     if form.is_valid():
    #         if form.cleaned_data['stuname']:
    #             stuname = form.cleaned_data['stuname']
    #         else:
    #             stuname = ''
    #         if form.cleaned_data['ctc']:
    #             ctc = form.cleaned_data['ctc']
    #         else:
    #             ctc = 0
    #         if form.cleaned_data['company']:
    #             cname = form.cleaned_data['company']
    #         else:
    #             cname = ''
    #         if form.cleaned_data['roll']:
    #             rollno = form.cleaned_data['roll']
    #         else:
    #             rollno = ''
    #         placementstatus = PlacementStatus.objects.filter(Q(notify_id__in=NotifyStudent.objects.filter
    #                                                    (Q(placement_type="PLACEMENT",
    #                                                       company_name__icontains=cname,
    #                                                       ctc__gte=ctc)),
    #                                                    unique_id__in=Student.objects.filter
    #                                                    ((Q(id__in=ExtraInfo.objects.filter
    #                                                        (Q(user__in=User.objects.filter
    #                                                           (Q(first_name__icontains=stuname)),
    #                                                           id__icontains=rollno))
    #                                                        )))))
    # elif 'studentpbisearchsubmit' in request.POST:
    #     officer_manage_pbi = 1
    #     form = ManagePbiRecord(request.POST)
    #     if form.is_valid():
    #         if form.cleaned_data['stuname']:
    #             stuname = form.cleaned_data['stuname']
    #         else:
    #             stuname = ''
    #         if form.cleaned_data['ctc']:
    #             ctc = form.cleaned_data['ctc']
    #         else:
    #             ctc = 0
    #         if form.cleaned_data['company']:
    #             cname = form.cleaned_data['company']
    #         else:
    #             cname = ''
    #         if form.cleaned_data['roll']:
    #             rollno = form.cleaned_data['roll']
    #         else:
    #             rollno = ''
    #         placementstatus = PlacementStatus.objects.filter(Q(notify_id__in=NotifyStudent.objects.filter
    #                                                    (Q(placement_type="PBI",
    #                                                       company_name__icontains=cname,
    #                                                       ctc__gte=ctc)),
    #                                                    unique_id__in=Student.objects.filter
    #                                                    ((Q(id__in=ExtraInfo.objects.filter
    #                                                        (Q(user__in=User.objects.filter
    #                                                           (Q(first_name__icontains=stuname)),
    #                                                           id__icontains=rollno))
    #                                                        )))))
    # else:
    #     placementstatus = []
    # current = HoldsDesignation.objects.filter(Q(working=user, designation__name="student"))
    # if current:
    #     student = get_object_or_404(Student, Q(id=profile.id))
    #     if request.method == 'POST':
    #         if 'studentapprovesubmit' in request.POST:
    #             status = PlacementStatus.objects.filter(pk=request.POST['studentapprovesubmit']).update(invitation='ACCEPTED', timestamp=timezone.now())
    #         if 'studentdeclinesubmit' in request.POST:
    #             status = PlacementStatus.objects.filter(Q(pk=request.POST['studentdeclinesubmit'])).update(invitation='REJECTED', timestamp=timezone.now())
    #         if 'educationsubmit' in request.POST:
    #             form = AddEducation(request.POST)
    #             if form.is_valid():
    #                 institute = form.cleaned_data['institute']
    #                 degree = form.cleaned_data['degree']
    #                 grade = form.cleaned_data['grade']
    #                 stream = form.cleaned_data['stream']
    #                 sdate = form.cleaned_data['sdate']
    #                 edate = form.cleaned_data['edate']
    #                 education_obj = Education.objects.create(unique_id=student, degree=degree,
    #                                                          grade=grade, institute=institute,
    #                                                          stream=stream, sdate=sdate, edate=edate)
    #                 education_obj.save()
    #         if 'profilesubmit' in request.POST:
    #             about_me = request.POST.get('about')
    #             age = request.POST.get('age')
    #             address = request.POST.get('address')
    #             contact = request.POST.get('contact')
    #             pic = request.POST.get('pic')
    #             # futu = request.POST.get('futu')
    #             # print(studentplacement_obj.future_aspect)
    #             # print('fut=', fut)
    #             # print('futu=', futu)
    #             # if studentplacement_obj.future_aspect == "HIGHER STUDIES":
    #             #     if futu == 2:
    #             #         studentplacement_obj.future_aspect = "PLACEMENT"
    #             # elif studentplacement_obj.future_aspect == "PLACEMENT":
    #             #     if futu == None:
    #             #         studentplacement_obj.future_aspect = "HIGHER STUDIES"
    #             extrainfo_obj = ExtraInfo.objects.get(user=user)
    #             extrainfo_obj.about_me = about_me
    #             extrainfo_obj.age = age
    #             extrainfo_obj.address = address
    #             extrainfo_obj.phone_no = contact
    #             extrainfo_obj.profile_picture = pic
    #             extrainfo_obj.save()
    #             profile = get_object_or_404(ExtraInfo, Q(user=user))
    #         if 'skillsubmit' in request.POST:
    #             form = AddSkill(request.POST)
    #             if form.is_valid():
    #                 skill = form.cleaned_data['skill']
    #                 skill_rating = form.cleaned_data['skill_rating']
    #                 has_obj = Has.objects.create(unique_id=student,
    #                                              skill_id=Skill.objects.get(skill=skill),
    #                                              skill_rating = skill_rating)
    #                 has_obj.save()
    #         if 'achievementsubmit' in request.POST:
    #             form = AddAchievement(request.POST)
    #             if form.is_valid():
    #                 achievement = form.cleaned_data['achievement']
    #                 achievement_type = form.cleaned_data['achievement_type']
    #                 description = form.cleaned_data['description']
    #                 issuer = form.cleaned_data['issuer']
    #                 date_earned = form.cleaned_data['date_earned']
    #                 achievement_obj = Achievement.objects.create(unique_id=student,
    #                                                              achievement=achievement,
    #                                                              achievement_type=achievement_type,
    #                                                              description=description,
    #                                                              issuer=issuer,
    #                                                              date_earned=date_earned)
    #                 achievement_obj.save()
    #         if 'publicationsubmit' in request.POST:
    #             form = AddPublication(request.POST)
    #             if form.is_valid():
    #                 publication_title = form.cleaned_data['publication_title']
    #                 description = form.cleaned_data['description']
    #                 publisher = form.cleaned_data['publisher']
    #                 publication_date = form.cleaned_data['publication_date']
    #                 publication_obj = Publication.objects.create(unique_id=student,
    #                                                              publication_title=
    #                                                              publication_title,
    #                                                              publisher=publisher,
    #                                                              description=description,
    #                                                              publication_date=publication_date)
    #                 publication_obj.save()
    #         if 'patentsubmit' in request.POST:
    #             form = AddPatent(request.POST)
    #             if form.is_valid():
    #                 patent_name = form.cleaned_data['patent_name']
    #                 description = form.cleaned_data['description']
    #                 patent_office = form.cleaned_data['patent_office']
    #                 patent_date = form.cleaned_data['patent_date']
    #                 patent_obj = Patent.objects.create(unique_id=student, patent_name=patent_name,
    #                                                    patent_office=patent_office,
    #                                                    description=description,
    #                                                    patent_date=patent_date)
    #                 patent_obj.save()
    #         if 'coursesubmit' in request.POST:
    #             form = AddCourse(request.POST)
    #             if form.is_valid():
    #                 course_name = form.cleaned_data['course_name']
    #                 description = form.cleaned_data['description']
    #                 license_no = form.cleaned_data['license_no']
    #                 sdate = form.cleaned_data['sdate']
    #                 edate = form.cleaned_data['edate']
    #                 course_obj = Course.objects.create(unique_id=student, course_name=course_name,
    #                                                    license_no=license_no,
    #                                                    description=description,
    #                                                    sdate=sdate, edate=edate)
    #                 course_obj.save()
    #         if 'projectsubmit' in request.POST:
    #             form = AddProject(request.POST)
    #             if form.is_valid():
    #                 project_name = form.cleaned_data['project_name']
    #                 project_status = form.cleaned_data['project_status']
    #                 summary = form.cleaned_data['summary']
    #                 project_link = form.cleaned_data['project_link']
    #                 sdate = form.cleaned_data['sdate']
    #                 edate = form.cleaned_data['edate']
    #                 project_obj = Project.objects.create(unique_id=student, summary=summary,
    #                                                      project_name=project_name,
    #                                                      project_status=project_status,
    #                                                      project_link=project_link,
    #                                                      sdate=sdate, edate=edate)
    #                 project_obj.save()
    #         if 'experiencesubmit' in request.POST:
    #             form = AddExperience(request.POST)
    #             if form.is_valid():
    #                 title = form.cleaned_data['title']
    #                 status = form.cleaned_data['status']
    #                 company = form.cleaned_data['company']
    #                 location = form.cleaned_data['location']
    #                 description = form.cleaned_data['description']
    #                 sdate = form.cleaned_data['sdate']
    #                 edate = form.cleaned_data['edate']
    #                 experience_obj = Experience.objects.create(unique_id=student, title=title,
    #                                                            company=company, location=location,
    #                                                            status=status,
    #                                                            description=description,
    #                                                            sdate=sdate, edate=edate)
    #                 experience_obj.save()
    #         if 'deleteskill' in request.POST:
    #             hid = request.POST['deleteskill']
    #             hs = Has.objects.get(Q(pk=hid))
    #             hs.delete()
    #         if 'deleteedu' in request.POST:
    #             hid = request.POST['deleteedu']
    #             hs = Education.objects.get(Q(pk=hid))
    #             hs.delete()
    #         if 'deletecourse' in request.POST:
    #             hid = request.POST['deletecourse']
    #             hs = Course.objects.get(Q(pk=hid))
    #             hs.delete()
    #         if 'deleteexp' in request.POST:
    #             hid = request.POST['deleteexp']
    #             hs = Experience.objects.get(Q(pk=hid))
    #             hs.delete()
    #         if 'deletepro' in request.POST:
    #             hid = request.POST['deletepro']
    #             hs = Project.objects.get(Q(pk=hid))
    #             hs.delete()
    #         if 'deleteach' in request.POST:
    #             hid = request.POST['deleteach']
    #             hs = Achievement.objects.get(Q(pk=hid))
    #             hs.delete()
    #         if 'deletepub' in request.POST:
    #             hid = request.POST['deletepub']
    #             hs = Publication.objects.get(Q(pk=hid))
    #             hs.delete()
    #         if 'deletepat' in request.POST:
    #             hid = request.POST['deletepat']
    #             hs = Patent.objects.get(Q(pk=hid))
    #             hs.delete()
    #     form = AddEducation(initial={})
    #     form1 = AddProfile(initial={})
    #     form10 = AddSkill(initial={})
    #     form11 = AddCourse(initial={})
    #     form12 = AddAchievement(initial={})
    #     form5 = AddPublication(initial={})
    #     form6 = AddProject(initial={})
    #     form7 = AddPatent(initial={})
    #     form8 = AddExperience(initial={})
    #     form2 = SearchPlacementRecord(initial={})
    #     form3 = SearchPbiRecord(initial={})
    #     form4 = SearchHigherRecord(initial={})
    #     studentplacement = get_object_or_404(StudentPlacement, Q(unique_id=student))
    #     skills = Has.objects.filter(Q(unique_id=student))
    #     education = Education.objects.filter(Q(unique_id=student))
    #     course = Course.objects.filter(Q(unique_id=student))
    #     experience = Experience.objects.filter(Q(unique_id=student))
    #     project = Project.objects.filter(Q(unique_id=student))
    #     achievement = Achievement.objects.filter(Q(unique_id=student))
    #     publication = Publication.objects.filter(Q(unique_id=student))
    #     patent = Patent.objects.filter(Q(unique_id=student))
    #     placementschedule = PlacementSchedule.objects.filter(Q(placement_date__gte=date.today())).values_list('notify_id', flat=True)
    #     placementstatus = PlacementStatus.objects.filter(Q(unique_id=student,
    #                                                         notify_id__in=placementschedule
    #                                                         )).order_by('-timestamp')
    #     context = {'user': user, 'profile': profile, 'student': studentplacement, 'skills': skills,
    #                'educations': education, 'courses': course, 'experiences': experience,
    #                'projects': project, 'achievements': achievement, 'publications': publication,
    #                'patent': patent, 'form': form, 'form1': form1, 'form2': form2, 'form3': form3,
    #                'form4': form4, 'form5': form5, 'form6': form6, 'form7': form7, 'form8': form8,
    #                'placementstatus':placementstatus, 'studentrecord':studentrecord,
    #                'placementrecord':placementrecord, 'higherrecord':higherrecord, 'years':years,
    #                'pbirecord':pbirecord, 'form10':form10, 'form11':form11, 'form12':form12,
    #                'records':records, 'current':current, 'officer_manage': officer_manage,
    #                 'officer_manage_pbi': officer_manage_pbi, 'officer_statistics_past': officer_statistics_past,
    #                 'officer_statistics_past_add': officer_statistics_past_add, 'officer_statistics_past_pbi_search':
    #                 officer_statistics_past_pbi_search, 'officer_statistics_past_pbi_add': officer_statistics_past_pbi_add,
    #                 'officer_statistics_past_higher_add': officer_statistics_past_higher_add,
    #                 'officer_statistics_past_higher_search': officer_statistics_past_higher_search,
    #                 'chairman_visit_add': chairman_visit_add}
    #     return render(request, "placementModule/placement.html", context)
#     current1 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement chairman"))
#     current2 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement officer"))
#     if request.method == 'POST':
#         print('coming')
#         if 'visitsubmit' in request.POST:
#             chairman_visit_add = 1
#             form = AddChairmanVisit(request.POST)
#             if form.is_valid():
#                 company_name = form.cleaned_data['company_name']
#                 location = form.cleaned_data['location']
#                 description = form.cleaned_data['description']
#                 visiting_date = form.cleaned_data['visiting_date']
#                 visit_obj = ChairmanVisit.objects.create(company_name=company_name,
#                                                          location=location,
#                                                          description=description,
#                                                          visiting_date=visiting_date,
#                                                          timestamp=timezone.now())
#                 visit_obj.save()
#         if 'deleterecord' in request.POST:
#             rid = request.POST['deleterecord']
#             sr = StudentRecord.objects.get(Q(pk=rid))
#             sr.delete()
#         if 'deletevisit' in request.POST:
#             rid = request.POST['deletevisit']
#             sr = ChairmanVisit.objects.get(Q(pk=rid))
#             sr.delete()
#         if 'deleteinvite' in request.POST:
#             rid = request.POST['deleteinvite']
#             sr = PlacementStatus.objects.get(Q(pk=rid))
#             sr.delete()
#         if 'deletesch' in request.POST:
#             hid = request.POST['deletesch']
#             hs = PlacementSchedule.objects.get(Q(pk=hid))
#             ps = NotifyStudent.objects.get(Q(pk=hs.notify_id.pk))
#             hs.delete()
#             ps.delete()
#         if 'schedulesubmit' in request.POST:
#             form5 = AddSchedule(request.POST)
#             if form5.is_valid():
#                 company_name = form5.cleaned_data['company_name']
#                 placement_date = form5.cleaned_data['placement_date']
#                 location = form5.cleaned_data['location']
#                 ctc = form5.cleaned_data['ctc']
#                 time = form5.cleaned_data['time']
#                 placement_type = form5.cleaned_data['placement_type']
#                 description = form5.cleaned_data['description']
#                 notify = NotifyStudent.objects.create(placement_type=placement_type,
#                                                       company_name=company_name,
#                                                       description=description,
#                                                       ctc=ctc,
#                                                       timestamp=timezone.now())

#                 schedule = PlacementSchedule.objects.create(notify_id=notify,
#                                                             title=company_name,
#                                                             description=description,
#                                                             placement_date=placement_date,
#                                                             location=location, time=time)
#                 notify.save()
#                 schedule.save()

#         invitecheck=0;
#         if 'sendinvite' in request.POST:
#             invitecheck=1;
#             form13 = SendInvite(request.POST)
#             if form13.is_valid():
#                 if form13.cleaned_data['company']:
#                     comp = form13.cleaned_data['company']
#                     com = [comp.company_name, comp.placement_type]
#                     notify = NotifyStudent.objects.get(company_name=com[0],
#                                                        placement_type=com[1])
#                     if 'q' not in request.session:
#                         stud = Student.objects.all()
#                     else:
#                         q = request.session['q']
#                         p = []
#                         for w in q:
#                             p.append(w['id_id'])
#                             stud = Student.objects.filter(Q(id__in=p))
#                     for student in stud:
#                         status = PlacementStatus.objects.create(notify_id=notify,
#                                                                 unique_id=student,
#                                                                 timestamp=timezone.now())
#                         status.save()


#         if 'recordsubmit' in request.POST:
#             print('search')
#             student_record_check = 1
#             form1 = SearchStudentRecord(request.POST)
#             if form1.is_valid():
#                 print('valid')
#                 if form1.cleaned_data['name']:
#                     name = form1.cleaned_data['name']
#                 else:
#                     name = ''
#                 if form1.cleaned_data['rollno']:
#                     rollno = form1.cleaned_data['rollno']
#                 else:
#                     rollno = ''
#                 programme = form1.cleaned_data['programme']
#                 if form1.cleaned_data['department']:
#                     department = form1.cleaned_data['department']
#                 else:
#                     department = ''
#                 if form1.cleaned_data['cpi']:
#                     cpi = form1.cleaned_data['cpi']
#                 else:
#                     cpi = 0
#                 debar = form1.cleaned_data['debar']
#                 placed_type = form1.cleaned_data['placed_type']
#                 skill = form1.cleaned_data['skill']
#                 # q2 = []
#                 # skill = skill.values_list('skill', flat=True)
#                 # for sk in skill:
#                 #     q2.extend(list(Skill.objects.filter(skill=sk)))
#                 # q1 = Has.objects.all()
#                 # q3 = Student.objects.all()
#                 # for ski in q2:
#                 #     q5 = []
#                 #     q4 = Has.objects.filter(Q(skill_id=ski)).values_list('unique_id', flat=True)
#                 #     q5.extend(list(q4))
#                 #     q3 = q3.objects.filter(Q(id__in=ExtraInfo.objects.filter(Q(id__in=q4))))
#                 print('here')
#                 students = Student.objects.filter(Q(id__in=ExtraInfo.objects.filter(Q(user__in=User.objects.filter(Q(first_name__icontains=name)),
#                     department__in=DepartmentInfo.objects.filter(Q(name__icontains=department)),
#                     id__icontains=rollno)),
#                     programme=programme,
#                     cpi__gte=cpi)).filter(Q(pk__in=StudentPlacement.objects.filter(Q(debar=debar, placed_type=placed_type)).values('unique_id_id')))
#                 print('after')
#                 st = students

#         else:
#             st = Student.objects.all()
#             students = ''
#             if 'getcvsubmit' in request.POST:
#                 ee =[]
#             else:
#                 if 'debar' in request.POST:
#                     spid = request.POST['debar']
#                     sr = StudentPlacement.objects.get(Q(pk=spid))
#                     sr.debar = "DEBAR"
#                     sr.save()
#                 if 'undebar' in request.POST:
#                     spid = request.POST['undebar']
#                     sr = StudentPlacement.objects.get(Q(pk=spid))
#                     sr.debar = "NOT DEBAR"
#                     sr.save()
#         qq = st.values('id_id')
#         q = list(qq)
#         request.session['q'] = q
#         if 'getcvsubmit' in request.POST:
#             form1 = SearchStudentRecord(request.POST)
#             if form1.is_valid():
#                 if form1.cleaned_data['name']:
#                     name = form1.cleaned_data['name']
#                 else:
#                     name = ''
#                 if form1.cleaned_data['rollno']:
#                     rollno = form1.cleaned_data['rollno']
#                 else:
#                     rollno = ''
#                 programme = form1.cleaned_data['programme']
#                 if form1.cleaned_data['department']:
#                     department = form1.cleaned_data['department']
#                 else:
#                     department = ''
#                 if form1.cleaned_data['cpi']:
#                     cpi = form1.cleaned_data['cpi']
#                 else:
#                     cpi = 0
#                 debar = form1.cleaned_data['debar']
#                 skill = form1.cleaned_data['skill']
#                 placed_type = form1.cleaned_data['placed_type']
#                 students = Student.objects.filter(Q(id__in=ExtraInfo.objects.filter
#                                                     (Q(user__in=User.objects.filter
#                                                        (Q(first_name__icontains=name)),
#                                                        department__in=DepartmentInfo.objects.filter
#                                                        (Q(name__icontains=department)),
#                                                        id__icontains=rollno
#                                                       )),
#                                                     programme=programme,
#                                                     cpi__gte=cpi)).filter(Q(pk__in=StudentPlacement.objects.filter(Q(debar=debar, placed_type=placed_type)).values('unique_id_id')))
#                 achievementcheck = request.POST.get('achievementcheck')
#                 educationcheck = request.POST.get('educationcheck')
#                 publicationcheck = request.POST.get('publicationcheck')
#                 patentcheck = request.POST.get('patentcheck')
#                 internshipcheck = request.POST.get('internshipcheck')
#                 projectcheck = request.POST.get('projectcheck')
#                 coursecheck = request.POST.get('coursecheck')
#                 skillcheck = request.POST.get('skillcheck')
#                 folder = 'media/placement_cell/'
#                 for the_file in os.listdir(folder):
#                     file_path = os.path.join(folder, the_file)
#                     if os.path.isfile(file_path):
#                         os.unlink(file_path)
#                 for student in students:
#                     profile1 = get_object_or_404(ExtraInfo, Q(pk=student.id.pk))
#                     user1 = get_object_or_404(User, Q(pk=profile1.user.pk))
#                     studentplacement = get_object_or_404(StudentPlacement, Q(unique_id=student))
#                     skills = Has.objects.filter(Q(unique_id=student))
#                     education = Education.objects.filter(Q(unique_id=student))
#                     course = Course.objects.filter(Q(unique_id=student))
#                     experience = Experience.objects.filter(Q(unique_id=student))
#                     project = Project.objects.filter(Q(unique_id=student))
#                     achievement = Achievement.objects.filter(Q(unique_id=student))
#                     publication = Publication.objects.filter(Q(unique_id=student))
#                     patent = Patent.objects.filter(Q(unique_id=student))
#                     render_to_pdf1('placementModule/cv.html',
#                                          {'pagesize': 'A4', 'user': user1, 'profile': profile1,
#                                           'projects': project, 'student': studentplacement,
#                                           'skills': skills, 'educations': education,
#                                           'courses': course, 'experiences': experience,
#                                           'achievements': achievement, 'records':records,
#                                           'publications': publication, 'patents': patent,
#                                           'achievementcheck': achievementcheck,
#                                           'educationcheck': educationcheck,
#                                           'publicationcheck': publicationcheck,
#                                           'patentcheck': patentcheck, 'skillcheck': skillcheck,
#                                           'internshipcheck': internshipcheck,
#                                           'projectcheck': projectcheck,
#                                           'coursecheck': coursecheck})
#                 download({'students': students})
#         if 'studenthigheraddsubmit' in request.POST:
#             officer_statistics_past_higher_add = 1
#             form = SearchHigherRecord(request.POST)
#             if form.is_valid():
#                 rollno = form.cleaned_data['roll']
#                 uname = form.cleaned_data['uname']
#                 test_score = form.cleaned_data['test_score']
#                 test_type = form.cleaned_data['test_type']
#                 year = form.cleaned_data['year']
#                 placementr = PlacementRecord.objects.create(year=year, name=uname,
#                                                                   placement_type="HIGHER STUDIES",
#                                                                   test_type=test_type,
#                                                                   test_score=test_score)
#                 studentr = StudentRecord.objects.create(record_id=placementr,
#                                                              unique_id=Student.objects.get
#                                                              ((Q(id=ExtraInfo.objects.get
#                                                                  (Q(id=rollno))))))
#                 studentr.save()
#                 placementr.save()
#         if 'studentpbiaddsubmit' in request.POST:
#             officer_statistics_past_pbi_add = 1
#             form = SearchPbiRecord(request.POST)
#             if form.is_valid():
#                 rollno = form.cleaned_data['roll']
#                 ctc = form.cleaned_data['ctc']
#                 year = form.cleaned_data['year']
#                 cname = form.cleaned_data['cname']
#                 placementr = PlacementRecord.objects.create(year=year, ctc=ctc,
#                                                                   placement_type="PBI",
#                                                                   name=cname)
#                 studentr = StudentRecord.objects.create(record_id=placementr,
#                                                              unique_id=Student.objects.get
#                                                              ((Q(id=ExtraInfo.objects.get
#                                                                  (Q(id=rollno))))))
#                 studentr.save()
#                 placementr.save()
#         if 'studentplacementaddsubmit' in request.POST:

#             officer_statistics_past_add = 1
#             form = SearchPlacementRecord(request.POST)
#             if form.is_valid():
#                 rollno = form.cleaned_data['roll']
#                 ctc = form.cleaned_data['ctc']
#                 year = form.cleaned_data['year']
#                 cname = form.cleaned_data['cname']
#                 placementr = PlacementRecord.objects.create(year=year, ctc=ctc,
#                                                                   placement_type="PLACEMENT",
#                                                                   name=cname)
#                 studentr = StudentRecord.objects.create(record_id=placementr,
#                                                              unique_id=Student.objects.get
#                                                              ((Q(id=ExtraInfo.objects.get
#                                                                  (Q(id=rollno))))))
#                 studentr.save()
#                 placementr.save()
#     else:
#         students = ''
#     form1 = SearchStudentRecord(initial={})
#     form = AddChairmanVisit(initial={})
#     form2 = SearchPlacementRecord(initial={})
#     form3 = SearchPbiRecord(initial={})
#     form4 = SearchHigherRecord(initial={})
#     form11 = ManagePlacementRecord(initial={})
#     form9 = ManagePbiRecord(initial={})
#     form10 = ManageHigherRecord(initial={})
#     form13 = SendInvite(initial={})
#     chairmanvisit = ChairmanVisit.objects.all()
#     notify = NotifyStudent.objects.all()
#     schedules = PlacementSchedule.objects.all()
#     studentplacement = StudentPlacement.objects.all()
#     # placementstatus = PlacementStatus.objects.filter(Q(notify_id__in=
#     #                                         notify)).order_by('-timestamp')
#     context = {'user': user, 'profile': profile, 'form':form, 'form1':form1, 'form5':form5,
#                'chairmanvisits':chairmanvisit, 'students':students, 'schedules':schedules,
#                'notify':notify, 'form2':form2, 'form3':form3, 'form4':form4, 'form9':form9,
#                'form10':form10, 'form11':form11, 'studentrecord':studentrecord, 'form13':form13,
#                'placementrecord':placementrecord, 'higherrecord':higherrecord, 'years':years,
#                'pbirecord':pbirecord, 'placementstatus':placementstatus, 'records':records,
#                'studentplacement':studentplacement, 'current1':current1, 'invitecheck':invitecheck,
#                'current2':current2, 'student_record_check': student_record_check,
#                'officer_manage': officer_manage, 'officer_manage_pbi': officer_manage_pbi,
#                'officer_statistics_past': officer_statistics_past, 'officer_statistics_past_add': officer_statistics_past_add,
#                'officer_statistics_past_pbi_search': officer_statistics_past_pbi_search, 'officer_statistics_past_pbi_add':
#                officer_statistics_past_pbi_add, 'officer_statistics_past_higher_add': officer_statistics_past_higher_add,
#                'officer_statistics_past_higher_search': officer_statistics_past_higher_search,
#                'chairman_visit_add': chairman_visit_add}
#     return render(request, "placementModule/placement.html", context)


# def render_to_pdf1(template_src, context_dict):
#     """
#     The function is used to generate the cv in the pdf format.
#     Embeds the data into the predefined template.
#     @param:
#             template_src - template of cv to be rendered
#             context_dict - data fetched from the dtatabase to be filled in the cv template
#     @variables:
#             output_filename - stores the filename of the generated pdf
#             template - stores the template
#             html - html rendered pdf
#             results - variable to store data in BytesIO
#             result - the opened pdf file object
#             pdf - storing encoded html of pdf version
#     """
#     output_filename = context_dict['profile'].id
#     template = get_template(template_src)
#     html = template.render(context_dict)
#     results = BytesIO()
#     result = open("media/placement_cell/"+output_filename+".pdf", "w+b")
#     pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), results)
#     if not pdf.err:
#         result.write(results.getvalue())
#     result.close()

# def cv(request, username):
#     # Retrieve data or whatever you need
#     """
#     The function is used to generate the cv in the pdf format.
#     Embeds the data into the predefined template.
#     @param:
#             request - trivial
#             username - name of user whose cv is to be generated
#     @variables:
#             user = stores current user
#             profile = stores extrainfo of user
#             current = Stores all working students from HoldsDesignation for the respective degignation
#             achievementcheck = variable for achievementcheck in form for cv generation
#             educationcheck = variable for educationcheck in form for cv generation
#             publicationcheck = variable for publicationcheck in form for cv generation
#             patentcheck = variable for patentcheck in form for cv generation
#             internshipcheck = variable for internshipcheck in form for cv generation
#             projectcheck = variable for projectcheck in form for cv generation
#             coursecheck = variable for coursecheck in form for cv generation
#             skillcheck = variable for skillcheck in form for cv generation
#             user = get_object_or_404(User, Q(username=username))
#             profile = get_object_or_404(ExtraInfo, Q(user=user))
#             import datetime
#             now = stores current timestamp
#             roll = roll of the user
#             student = variable storing the profile data
#             studentplacement = variable storing the placement data
#             skills = variable storing the skills data
#             education = variable storing the education data
#             course = variable storing the course data
#             experience = variable storing the experience data
#             project = variable storing the project data
#             achievement = variable storing the achievement data
#             publication = variable storing the publication data
#             patent = variable storing the patent data
#     """
#     user = request.user
#     profile = get_object_or_404(ExtraInfo, Q(user=user))

#     current = HoldsDesignation.objects.filter(Q(working=user, designation__name="student"))
#     if current:
#         if request.method == 'POST':
#             achievementcheck = request.POST.get('achievementcheck')
#             educationcheck = request.POST.get('educationcheck')
#             publicationcheck = request.POST.get('publicationcheck')
#             patentcheck = request.POST.get('patentcheck')
#             internshipcheck = request.POST.get('internshipcheck')
#             projectcheck = request.POST.get('projectcheck')
#             coursecheck = request.POST.get('coursecheck')
#             skillcheck = request.POST.get('skillcheck')
#     else:
#         achievementcheck = '1'
#         educationcheck = '1'
#         publicationcheck = '1'
#         patentcheck = '1'
#         internshipcheck = '1'
#         projectcheck = '1'
#         coursecheck = '1'
#         skillcheck = '1'

#     user = get_object_or_404(User, Q(username=username))
#     profile = get_object_or_404(ExtraInfo, Q(user=user))
#     import datetime
#     now = datetime.datetime.now()
#     if int(str(profile.id)[:2]) == 20:
#         if (now.month>4):
#           roll = 1+now.year-int(str(profile.id)[:4])
#         else:
#           roll = now.year-int(str(profile.id)[:4])
#     else:
#         if (now.month>4):
#           roll = 1+(now.year)-int("20"+str(profile.id)[0:2])
#         else:
#           roll = (now.year)-int("20"+str(profile.id)[0:2])

#     student = get_object_or_404(Student, Q(id=profile.id))
#     studentplacement = get_object_or_404(StudentPlacement, Q(unique_id=student))
#     skills = Has.objects.filter(Q(unique_id=student))
#     education = Education.objects.filter(Q(unique_id=student))
#     course = Course.objects.filter(Q(unique_id=student))
#     experience = Experience.objects.filter(Q(unique_id=student))
#     project = Project.objects.filter(Q(unique_id=student))
#     achievement = Achievement.objects.filter(Q(unique_id=student))
#     publication = Publication.objects.filter(Q(unique_id=student))
#     patent = Patent.objects.filter(Q(unique_id=student))
#     return render_to_pdf('placementModule/cv.html', {'pagesize': 'A4', 'user': user,
#                                                      'profile': profile, 'projects': project,
#                                                      'student': studentplacement,
#                                                      'skills': skills, 'educations': education,
#                                                      'courses': course, 'experiences': experience,
#                                                      'achievements': achievement,
#                                                      'publications': publication,
#                                                      'patents': patent, 'roll': roll,
#                                                      'achievementcheck': achievementcheck,
#                                                      'educationcheck': educationcheck,
#                                                      'publicationcheck': publicationcheck,
#                                                      'patentcheck': patentcheck,
#                                                      'internshipcheck': internshipcheck,
#                                                      'projectcheck': projectcheck,
#                                                      'coursecheck': coursecheck,
#                                                      'skillcheck': skillcheck})
