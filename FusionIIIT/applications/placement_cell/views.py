import os
import shutil
import datetime
import decimal
import zipfile
import xlwt
import logging

from html import escape
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
from applications.academic_information.models import Student
from .forms import (AddAchievement, AddChairmanVisit, AddCourse, AddEducation,
                    AddExperience, AddReference, AddPatent, AddProfile, AddProject,
                    AddPublication, AddSchedule, AddSkill, ManageHigherRecord,
                    ManagePbiRecord, ManagePlacementRecord, SearchHigherRecord,
                    SearchPbiRecord, SearchPlacementRecord,
                    SearchStudentRecord, SendInvite,
                    CompanyRegistrationForm, JobPostingForm, JobOfferForm,
                    AnnouncementForm, InterviewScheduleForm, ReportFilterForm)

from .models import (Achievement, ChairmanVisit, Course, Education, Experience, Conference,
                     Has, NotifyStudent, Patent, PlacementRecord, Extracurricular, Reference,
                     PlacementSchedule, PlacementStatus, Project, Publication,
                     Skill, StudentPlacement, StudentRecord, Role, CompanyDetails,
                     Company, JobPosting, JobApplication, InterviewSchedule,
                     InterviewPanel, JobOffer, Announcement, PlacementPolicy, Constants as PlacementConstants)

from .utils import (check_eligibility, check_duplicate_application,
                    check_placement_policy, get_placement_statistics,
                    get_student_application_summary, expire_pending_offers)
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

logger = logging.getLogger('django.server')
@login_required
def placement__Statistics(request):
    '''
    logic of the view shown under Placement Statistics tab
    '''
    user = request.user


    statistics_tab = 1
    strecord_tab=1
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
    studentrecord = StudentRecord.objects.select_related('unique_id','record_id').all()

    years = PlacementRecord.objects.filter(~Q(placement_type="HIGHER STUDIES")).values('year').annotate(Count('year'))
    records = PlacementRecord.objects.values('name', 'year', 'ctc', 'placement_type').annotate(Count('name'), Count('year'), Count('placement_type'), Count('ctc'))




    #working here to fetch all placement record
    all_records=PlacementRecord.objects.all()
    print(all_records)






    invitecheck=0
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
    if len(current) == 0:
        current = None
    pbirecord= ''
    placementrecord= ''
    higherrecord= ''
    total_query=0
    total_query1 = 0
    total_query2= 0
    p=""
    p1=""
    p2=""
    placement_search_record=" "
    pbi_search_record=" "
    higher_search_record=" "
    # results of the searched query under placement tab
    if 'studentplacementrecordsubmit' in request.POST:
        officer_statistics_past = 1
        form = SearchPlacementRecord(request.POST)
        if form.is_valid():




            print("IS VALID")



            #for student name
            if form.cleaned_data['stuname']:
                stuname = form.cleaned_data['stuname']
                try:
                    first_name = stuname.split(" ")[0]
                    last_name = stuname.split(" ")[1]
                except Exception as e:
                    print("Error")
                    print(e)
                    first_name = stuname
                    last_name = ''
            else:
                stuname = ''
                first_name = ''
                last_name = ''


            # for student CTC
            if form.cleaned_data['ctc']:
                ctc = form.cleaned_data['ctc']
            else:
                ctc = 0

            #for company name
            if form.cleaned_data['cname']:
                cname = form.cleaned_data['cname']
            else:
                cname = ''

            #for student roll
            if form.cleaned_data['roll']:
                rollno = form.cleaned_data['roll']
            else:
                rollno = ''

            #for admission year
            if form.cleaned_data['year']:
                year = form.cleaned_data['year']
                s = Student.objects.filter((Q(id__in=ExtraInfo.objects.filter(
                    Q(user__in=User.objects.filter(
                        first_name__icontains=first_name,
                        last_name__icontains=last_name),
                       id__icontains=rollno))
                    )))

                p = PlacementRecord.objects.filter(Q(placement_type="PLACEMENT", name__icontains=stuname, ctc__icontains=ctc, year__icontains=year))




            """placementrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
                    Q(record_id__in=PlacementRecord.objects.filter(
                        Q(placement_type="PLACEMENT", name__icontains=cname, ctc__gte=ctc, year=year)),
                    unique_id__in=Student.objects.filter(
                        (Q(id__in=ExtraInfo.objects.filter(
                            Q(user__in=User.objects.filter(
                                first_name__icontains=first_name,
                                last_name__icontains=last_name,
                            id__icontains=rollno))))))))
                #print("In if:", placementrecord)
            else:
                s = Student.objects.filter((Q(id__in=ExtraInfo.objects.filter(
                    Q(user__in=User.objects.filter(
                        first_name__icontains=first_name,
                        last_name__icontains=last_name),
                        id__icontains=rollno))
                    )))

                p = PlacementRecord.objects.filter(Q(placement_type="PLACEMENT", name__icontains=cname, ctc__gte=ctc))
                print("Agein p:",p)
                placementrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
            request.session['year'] = form.cleaned_data['year']"""

            print(p)


            total_query = p.count()

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
        if request.GET.get('page') != None:
            try:
                if request.session['year']:
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


                    placementrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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

                    placementrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
                no_records=1
            print(placementrecord)
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

    if total_query!=0:
        placement_search_record=p
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
                pbirecord = StudentRecord.objects.select_related('unique_id','record_id').filter(Q(record_id__in=PlacementRecord.objects.filter
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
                p1 = PlacementRecord.objects.filter(
                    Q(placement_type="PBI", name__icontains=stuname, ctc__icontains=ctc, year__icontains=year))
            """else:
                pbirecord = StudentRecord.objects.select_related('unique_id','record_id').filter(Q(record_id__in=PlacementRecord.objects.filter
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
"""
            total_query1 = p1.count()

            if total_query1 > 30:
                pagination_pbi = 1
                paginator = Paginator(pbirecord, 30)
                page = request.GET.get('page', 1)
                pbirecord = paginator.page(page)
                page = int(page)
                total_page = int(page + 3)

                if page<(paginator.num_pages-3):
                    if total_query1 > 30 and total_query1 <=60:
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
            try:
                if request.session['year']:
                    pbirecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
                    pbirecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
    if total_query1!=0:
        pbi_search_record=p1

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
                higherrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(Q(record_id__in=PlacementRecord.objects.filter
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

                p2 = PlacementRecord.objects.filter(
                    Q(placement_type="HIGHER STUDIES", name__icontains=stuname, year__icontains=year))

            """else:
                # result of the query when year is not given
                higherrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
            request.session['year'] = form.cleaned_data['year']"""

            total_query2 = p2.count()

            if total_query2 > 30:
                pagination_higher = 1
                paginator = Paginator(p2, 30)
                page = request.GET.get('page', 1)
                p2 = paginator.page(page)
                page = int(page)
                total_page = int(page+3)

                if page < (paginator.num_pages-3):
                    if total_query2 > 30 and total_query2 <= 60:
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
                    higherrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
                    higherrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
    if total_query2!=0:
        higher_search_record=p2

    context = {
        'form2'             :            form2,
        'form3'             :            form3,
        'form4'             :            form4,
        'current'           :          current,
        'current1'          :         current1,
        'current2'          :         current2,


        'all_records':          all_records,   #for flashing all placement Schedule

        'placement_search_record': placement_search_record,
        'pbi_search_record': pbi_search_record,
        'higher_search_record': higher_search_record,



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



def get_reference_list(request):
    if request.method == 'POST':
        # arr = request.POST.getlist('arr[]')
        # print(arr)
        # print(type(arr))
        user = request.user
        profile = get_object_or_404(ExtraInfo, Q(user=user))
        student = get_object_or_404(Student, Q(id=profile.id))
        print(student)
        reference_objects = Reference.select_related('unique_id').objects.filter(unique_id=student)
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
def Placement__Schedule(request):
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
    print(current)

    # If the user is Student
    if current:
        student = get_object_or_404(Student, Q(id=profile.id))

        # Student view for showing accepted or declined schedule
        if request.method == 'POST':
            if 'studentapprovesubmit' in request.POST:
                status = PlacementStatus.objects.select_related('unique_id','notify_id').filter(
                    pk=request.POST['studentapprovesubmit']).update(
                    invitation='ACCEPTED',
                    timestamp=timezone.now())
            if 'studentdeclinesubmit' in request.POST:
                status = PlacementStatus.objects.select_related('unique_id','notify_id').filter(
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
                    education_obj = Education.objects.select_related('unique_id').create(
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
                    has_obj = Has.objects.select_related('skill_id','unique_id').create(unique_id=student,
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
                    achievement_obj = Achievement.objects.select_related('unique_id').create(unique_id=student,
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
                    publication_obj = Publication.objects.select_related('unique_id').create(unique_id=student,
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
                    patent_obj = Patent.objects.select_related('unique_id').create(unique_id=student, patent_name=patent_name,
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
                    course_obj = Course.objects.select_related('unique_id').create(unique_id=student, course_name=course_name,
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
                    experience_obj = Experience.objects.select_related('unique_id').create(unique_id=student, title=title,
                                                               company=company, location=location,
                                                               status=status,
                                                               description=description,
                                                               sdate=sdate, edate=edate)
                    experience_obj.save()

            if 'deleteskill' in request.POST:
                hid = request.POST['deleteskill']
                hs = Has.objects.select_related('skill_id','unique_id').get(Q(pk=hid))
                hs.delete()
            if 'deleteedu' in request.POST:
                hid = request.POST['deleteedu']
                hs = Education.objects.select_related('unique_id').get(Q(pk=hid))
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
                hs = Publication.objects.select_related('unique_id').get(Q(pk=hid))
                hs.delete()
            if 'deletepat' in request.POST:
                hid = request.POST['deletepat']
                hs = Patent.objects.get(Q(pk=hid))
                hs.delete()

        placementschedule = PlacementSchedule.objects.select_related('notify_id').filter(
            Q(placement_date__gte=date.today())).values_list('notify_id', flat=True)

        placementstatus = PlacementStatus.objects.select_related('unique_id','notify_id').filter(
            Q(unique_id=student,
            notify_id__in=placementschedule)).order_by('-timestamp')


        check_invitation_date(placementstatus)

    # facult and other staff view only statistics
    if not (current or current1 or current2):
        return redirect('/placement/statistics/')

    # delete the schedule
    if 'deletesch' in request.POST:
        delete_sch_key = request.POST['delete_sch_key']
        try:
            placement_schedule = PlacementSchedule.objects.select_related('notify_id').get(pk = delete_sch_key)
            NotifyStudent.objects.get(pk=placement_schedule.notify_id.id).delete()
            placement_schedule.delete()
            messages.success(request, 'Schedule Deleted Successfully')
        except Exception as e:
            messages.error(request, 'Problem Occurred for Schedule Delete!!!')

    # saving all the schedule details
    if 'schedulesubmit' in request.POST:
        form5 = AddSchedule(request.POST, request.FILES)
        if form5.is_valid():
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

            schedule = PlacementSchedule.objects.select_related('notify_id').create(notify_id=notify,
                                                        title=company_name,
                                                        description=description,
                                                        placement_date=placement_date,
                                                        attached_file = attached_file,
                                                        role=role,
                                                        location=location, time=time)

            notify.save()
            schedule.save()
            messages.success(request, "Schedule Added Successfull!!")


    schedules = PlacementSchedule.objects.select_related('notify_id').all()


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



def invite_status(request):
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

            placementstatus_placement = PlacementStatus.objects.select_related('unique_id','notify_id').filter(Q(notify_id__in=NotifyStudent.objects.filter
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
                placementstatus_placement = PlacementStatus.objects.select_related('unique_id','notify_id').filter(Q(notify_id__in=NotifyStudent.objects.filter
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
            placementstatus_pbi = PlacementStatus.objects.select_related('unique_id','notify_id').filter(
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

            if total_query > 30:
                no_pagination = 1
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
    else:
        if request.GET.get('pbi_page') != None:
            mnpbi_tab = 1
            mnpbi_post = 1
            no_pagination = 1
            try:
                placementstatus_pbi = PlacementStatus.objects.select_related('unique_id','notify_id').filter(
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

        placementstatus = None
        if 'pdf_gen_invitation_status_placement' in request.POST:
            stuname = request.session['mn_stuname']
            ctc = request.session['mn_ctc']
            cname = request.session['mn_cname']
            rollno = request.session['mn_rollno']

            placementstatus = PlacementStatus.objects.select_related('unique_id','notify_id').filter(Q(notify_id__in=NotifyStudent.objects.filter
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

            placementstatus = PlacementStatus.objects.select_related('unique_id','notify_id').filter(
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

        return render_to_pdf('placementModule/pdf_invitation_status.html', context)

    if 'excel_gen_invitation_status' in request.POST:

        placementstatus = None
        if 'excel_gen_invitation_status_placement' in request.POST:
            stuname = request.session['mn_stuname']
            ctc = request.session['mn_ctc']
            cname = request.session['mn_cname']
            rollno = request.session['mn_rollno']

            placementstatus = PlacementStatus.objects.select_related('unique_id','notify_id').filter(Q(notify_id__in=NotifyStudent.objects.filter
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

            placementstatus = PlacementStatus.objects.select_related('unique_id','notify_id').filter(
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


        years = PlacementRecord.objects.filter(~Q(placement_type="HIGHER STUDIES")).values('year').annotate(Count('year'))
        records = PlacementRecord.objects.values('name', 'year', 'ctc', 'placement_type').annotate(Count('name'), Count('year'), Count('placement_type'), Count('ctc'))


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







    invitecheck=0
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
    print(current)

    if len(current1)!=0 or len(current2)!=0:
        delete_operation = 1
    if len(current) == 0:
        current = None
    pbirecord= ''
    placementrecord= ''
    higherrecord= ''
    total_query=0
    total_query1 = 0
    total_query2= 0
    p=""
    p1=""
    p2=""
    placement_search_record=" "
    pbi_search_record=" "
    higher_search_record=" "
    # results of the searched query under placement tab
    if 'studentplacementrecordsubmit' in request.POST:
        officer_statistics_past = 1
        form = SearchPlacementRecord(request.POST)
        if form.is_valid():




            print("IS VALID")



            #for student name
            if form.cleaned_data['stuname']:
                stuname = form.cleaned_data['stuname']
                try:
                    first_name = stuname.split(" ")[0]
                    last_name = stuname.split(" ")[1]
                except Exception as e:
                    print("Error")
                    print(e)
                    first_name = stuname
                    last_name = ''
            else:
                stuname = ''
                first_name = ''
                last_name = ''


            # for student CTC
            if form.cleaned_data['ctc']:
                ctc = form.cleaned_data['ctc']
            else:
                ctc = 0

            #for company name
            if form.cleaned_data['cname']:
                cname = form.cleaned_data['cname']
            else:
                cname = ''

            #for student roll
            if form.cleaned_data['roll']:
                rollno = form.cleaned_data['roll']
            else:
                rollno = ''

            #for admission year
            if form.cleaned_data['year']:
                year = form.cleaned_data['year']
                s = Student.objects.filter((Q(id__in=ExtraInfo.objects.filter(
                    Q(user__in=User.objects.filter(
                        first_name__icontains=first_name,
                        last_name__icontains=last_name),
                       id__icontains=rollno))
                    )))

                p = PlacementRecord.objects.filter(Q(placement_type="PLACEMENT", name__icontains=stuname, ctc__icontains=ctc, year__icontains=year))




            """placementrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
                    Q(record_id__in=PlacementRecord.objects.filter(
                        Q(placement_type="PLACEMENT", name__icontains=cname, ctc__gte=ctc, year=year)),
                    unique_id__in=Student.objects.filter(
                        (Q(id__in=ExtraInfo.objects.filter(
                            Q(user__in=User.objects.filter(
                                first_name__icontains=first_name,
                                last_name__icontains=last_name,
                            id__icontains=rollno))))))))
                #print("In if:", placementrecord)
            else:
                s = Student.objects.filter((Q(id__in=ExtraInfo.objects.filter(
                    Q(user__in=User.objects.filter(
                        first_name__icontains=first_name,
                        last_name__icontains=last_name),
                        id__icontains=rollno))
                    )))

                p = PlacementRecord.objects.filter(Q(placement_type="PLACEMENT", name__icontains=cname, ctc__gte=ctc))
                print("Agein p:",p)
                placementrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
            request.session['year'] = form.cleaned_data['year']"""

            print(p)


            total_query = p.count()

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
        if request.GET.get('page') != None:
            try:
                if request.session['year']:
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


                    placementrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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

                    placementrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
                no_records=1
            print(placementrecord)
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

    if total_query!=0:
        placement_search_record=p
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
                pbirecord = StudentRecord.objects.select_related('unique_id','record_id').filter(Q(record_id__in=PlacementRecord.objects.filter
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
                p1 = PlacementRecord.objects.filter(
                    Q(placement_type="PBI", name__icontains=stuname, ctc__icontains=ctc, year__icontains=year))
            """else:
                pbirecord = StudentRecord.objects.select_related('unique_id','record_id').filter(Q(record_id__in=PlacementRecord.objects.filter
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
"""
            total_query1 = p1.count()

            if total_query1 > 30:
                pagination_pbi = 1
                paginator = Paginator(pbirecord, 30)
                page = request.GET.get('page', 1)
                pbirecord = paginator.page(page)
                page = int(page)
                total_page = int(page + 3)

                if page<(paginator.num_pages-3):
                    if total_query1 > 30 and total_query1 <=60:
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
            try:
                if request.session['year']:
                    pbirecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
                    pbirecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
    if total_query1!=0:
        pbi_search_record=p1

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
                higherrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(Q(record_id__in=PlacementRecord.objects.filter
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

                p2 = PlacementRecord.objects.filter(
                    Q(placement_type="HIGHER STUDIES", name__icontains=stuname, year__icontains=year))

            """else:
                # result of the query when year is not given
                higherrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
            request.session['year'] = form.cleaned_data['year']"""

            total_query2 = p2.count()

            if total_query2 > 30:
                pagination_higher = 1
                paginator = Paginator(p2, 30)
                page = request.GET.get('page', 1)
                p2 = paginator.page(page)
                page = int(page)
                total_page = int(page+3)

                if page < (paginator.num_pages-3):
                    if total_query2 > 30 and total_query2 <= 60:
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
                    higherrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
                    higherrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
    if total_query2!=0:
        higher_search_record=p2

    context = {
        'form2'             :            form2,
        'form3'             :            form3,
        'form4'             :            form4,
        'current'           :          current,
        'current1'          :         current1,
        'current2'          :         current2,


        'all_records':          all_records,   #for flashing all placement Schedule

        'placement_search_record': placement_search_record,
        'pbi_search_record': pbi_search_record,
        'higher_search_record': higher_search_record,



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



def get_reference_list(request):
    if request.method == 'POST':

        user = request.user
        profile = get_object_or_404(ExtraInfo, Q(user=user))
        student = get_object_or_404(Student, Q(id=profile.id))
        print(student)
        reference_objects = Reference.select_related('unique_id').objects.filter(unique_id=student)
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
def Placement__Schedule(request):
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
    print(current)

    # If the user is Student
    if current:
        student = get_object_or_404(Student, Q(id=profile.id))

        # Student view for showing accepted or declined schedule
        if request.method == 'POST':
            if 'studentapprovesubmit' in request.POST:
                status = PlacementStatus.objects.select_related('unique_id','notify_id').filter(
                    pk=request.POST['studentapprovesubmit']).update(
                    invitation='ACCEPTED',
                    timestamp=timezone.now())
            if 'studentdeclinesubmit' in request.POST:
                status = PlacementStatus.objects.select_related('unique_id','notify_id').filter(
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
                    education_obj = Education.objects.select_related('unique_id').create(
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
                    has_obj = Has.objects.select_related('skill_id','unique_id').create(unique_id=student,
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
                    achievement_obj = Achievement.objects.select_related('unique_id').create(unique_id=student,
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
                    publication_obj = Publication.objects.select_related('unique_id').create(unique_id=student,
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
                    patent_obj = Patent.objects.select_related('unique_id').create(unique_id=student, patent_name=patent_name,
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
                    course_obj = Course.objects.select_related('unique_id').create(unique_id=student, course_name=course_name,
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
                    experience_obj = Experience.objects.select_related('unique_id').create(unique_id=student, title=title,
                                                               company=company, location=location,
                                                               status=status,
                                                               description=description,
                                                               sdate=sdate, edate=edate)
                    experience_obj.save()

            if 'deleteskill' in request.POST:
                hid = request.POST['deleteskill']
                hs = Has.objects.select_related('skill_id','unique_id').get(Q(pk=hid))
                hs.delete()
            if 'deleteedu' in request.POST:
                hid = request.POST['deleteedu']
                hs = Education.objects.select_related('unique_id').get(Q(pk=hid))
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
                hs = Publication.objects.select_related('unique_id').get(Q(pk=hid))
                hs.delete()
            if 'deletepat' in request.POST:
                hid = request.POST['deletepat']
                hs = Patent.objects.get(Q(pk=hid))
                hs.delete()

        placementschedule = PlacementSchedule.objects.select_related('notify_id').filter(
            Q(placement_date__gte=date.today())).values_list('notify_id', flat=True)

        placementstatus = PlacementStatus.objects.select_related('unique_id','notify_id').filter(
            Q(unique_id=student,
            notify_id__in=placementschedule)).order_by('-timestamp')


        check_invitation_date(placementstatus)

    # facult and other staff view only statistics
    if not (current or current1 or current2):
        return redirect('/placement/statistics/')

    # delete the schedule
    if 'deletesch' in request.POST:
        delete_sch_key = request.POST['delete_sch_key']
        try:
            placement_schedule = PlacementSchedule.objects.select_related('notify_id').get(pk = delete_sch_key)
            NotifyStudent.objects.get(pk=placement_schedule.notify_id.id).delete()
            placement_schedule.delete()
            messages.success(request, 'Schedule Deleted Successfully')
        except Exception as e:
            messages.error(request, 'Problem Occurred for Schedule Delete!!!')

    # saving all the schedule details
    if 'schedulesubmit' in request.POST:
        form5 = AddSchedule(request.POST, request.FILES)
        if form5.is_valid():
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

            schedule = PlacementSchedule.objects.select_related('notify_id').create(notify_id=notify,
                                                        title=company_name,
                                                        description=description,
                                                        placement_date=placement_date,
                                                        attached_file = attached_file,
                                                        role=role,
                                                        location=location, time=time)

            notify.save()
            schedule.save()
            messages.success(request, "Schedule Added Successfull!!")


    schedules = PlacementSchedule.objects.select_related('notify_id').all()


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



def invite_status(request):
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

            placementstatus_placement = PlacementStatus.objects.select_related('unique_id','notify_id').filter(Q(notify_id__in=NotifyStudent.objects.filter
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
                placementstatus_placement = PlacementStatus.objects.select_related('unique_id','notify_id').filter(Q(notify_id__in=NotifyStudent.objects.filter
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
            placementstatus_pbi = PlacementStatus.objects.select_related('unique_id','notify_id').filter(
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

            if total_query > 30:
                no_pagination = 1
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
    else:
        if request.GET.get('pbi_page') != None:
            mnpbi_tab = 1
            mnpbi_post = 1
            no_pagination = 1
            try:
                placementstatus_pbi = PlacementStatus.objects.select_related('unique_id','notify_id').filter(
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

        placementstatus = None
        if 'pdf_gen_invitation_status_placement' in request.POST:
            stuname = request.session['mn_stuname']
            ctc = request.session['mn_ctc']
            cname = request.session['mn_cname']
            rollno = request.session['mn_rollno']

            placementstatus = PlacementStatus.objects.select_related('unique_id','notify_id').filter(Q(notify_id__in=NotifyStudent.objects.filter
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

            placementstatus = PlacementStatus.objects.select_related('unique_id','notify_id').filter(
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

        return render_to_pdf('placementModule/pdf_invitation_status.html', context)

    if 'excel_gen_invitation_status' in request.POST:

        placementstatus = None
        if 'excel_gen_invitation_status_placement' in request.POST:
            stuname = request.session['mn_stuname']
            ctc = request.session['mn_ctc']
            cname = request.session['mn_cname']
            rollno = request.session['mn_rollno']

            placementstatus = PlacementStatus.objects.select_related('unique_id','notify_id').filter(Q(notify_id__in=NotifyStudent.objects.filter
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

            placementstatus = PlacementStatus.objects.select_related('unique_id','notify_id').filter(
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
    print(current)

    # If the user is Student
    if current:
        student = get_object_or_404(Student, Q(id=profile.id))

        # Student view for showing accepted or declined schedule
        if request.method == 'POST':
            if 'studentapprovesubmit' in request.POST:
                status = PlacementStatus.objects.select_related('unique_id','notify_id').filter(
                    pk=request.POST['studentapprovesubmit']).update(
                    invitation='ACCEPTED',
                    timestamp=timezone.now())
            if 'studentdeclinesubmit' in request.POST:
                status = PlacementStatus.objects.select_related('unique_id','notify_id').filter(
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
                    education_obj = Education.objects.select_related('unique_id').create(
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
                    has_obj = Has.objects.select_related('skill_id','unique_id').create(unique_id=student,
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
                    achievement_obj = Achievement.objects.select_related('unique_id').create(unique_id=student,
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
                    publication_obj = Publication.objects.select_related('unique_id').create(unique_id=student,
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
                    patent_obj = Patent.objects.select_related('unique_id').create(unique_id=student, patent_name=patent_name,
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
                    course_obj = Course.objects.select_related('unique_id').create(unique_id=student, course_name=course_name,
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
                    experience_obj = Experience.objects.select_related('unique_id').create(unique_id=student, title=title,
                                                               company=company, location=location,
                                                               status=status,
                                                               description=description,
                                                               sdate=sdate, edate=edate)
                    experience_obj.save()

            if 'deleteskill' in request.POST:
                hid = request.POST['deleteskill']
                hs = Has.objects.select_related('skill_id','unique_id').get(Q(pk=hid))
                hs.delete()
            if 'deleteedu' in request.POST:
                hid = request.POST['deleteedu']
                hs = Education.objects.select_related('unique_id').get(Q(pk=hid))
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
                hs = Publication.objects.select_related('unique_id').get(Q(pk=hid))
                hs.delete()
            if 'deletepat' in request.POST:
                hid = request.POST['deletepat']
                hs = Patent.objects.get(Q(pk=hid))
                hs.delete()

        placementschedule = PlacementSchedule.objects.select_related('notify_id').filter(
            Q(placement_date__gte=date.today())).values_list('notify_id', flat=True)

        placementstatus = PlacementStatus.objects.select_related('unique_id','notify_id').filter(
            Q(unique_id=student,
            notify_id__in=placementschedule)).order_by('-timestamp')


        check_invitation_date(placementstatus)

    # facult and other staff view only statistics
    if not (current or current1 or current2):
        return redirect('/placement/statistics/')

    # delete the schedule
    if 'deletesch' in request.POST:
        delete_sch_key = request.POST['delete_sch_key']
        try:
            placement_schedule = PlacementSchedule.objects.select_related('notify_id').get(pk = delete_sch_key)
            NotifyStudent.objects.get(pk=placement_schedule.notify_id.id).delete()
            placement_schedule.delete()
            messages.success(request, 'Schedule Deleted Successfully')
        except Exception as e:
            messages.error(request, 'Problem Occurred for Schedule Delete!!!')

    # saving all the schedule details
    if 'schedulesubmit' in request.POST:
        form5 = AddSchedule(request.POST, request.FILES)
        if form5.is_valid():
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

            schedule = PlacementSchedule.objects.select_related('notify_id').create(notify_id=notify,
                                                        title=company_name,
                                                        description=description,
                                                        placement_date=placement_date,
                                                        attached_file = attached_file,
                                                        role=role,
                                                        location=location, time=time)

            notify.save()
            schedule.save()
            messages.success(request, "Schedule Added Successfull!!")


    schedules = PlacementSchedule.objects.select_related('notify_id').all()


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
            PlacementStatus.objects.select_related('unique_id','notify_id').get(pk=delete_invit_status_key).delete()
            messages.success(request, 'Invitation Deleted Successfully')
        except Exception as e:
            logger.error(e)

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
        # 'current':current,
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

            placementstatus_placement = PlacementStatus.objects.select_related('unique_id','notify_id').filter(Q(notify_id__in=NotifyStudent.objects.filter
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
                placementstatus_placement = PlacementStatus.objects.select_related('unique_id','notify_id').filter(Q(notify_id__in=NotifyStudent.objects.filter
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
            placementstatus_pbi = PlacementStatus.objects.select_related('unique_id','notify_id').filter(
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

            if total_query > 30:
                no_pagination = 1
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
    else:
        if request.GET.get('pbi_page') != None:
            mnpbi_tab = 1
            mnpbi_post = 1
            no_pagination = 1
            try:
                placementstatus_pbi = PlacementStatus.objects.select_related('unique_id','notify_id').filter(
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

        placementstatus = None
        if 'pdf_gen_invitation_status_placement' in request.POST:
            stuname = request.session['mn_stuname']
            ctc = request.session['mn_ctc']
            cname = request.session['mn_cname']
            rollno = request.session['mn_rollno']

            placementstatus = PlacementStatus.objects.select_related('unique_id','notify_id').filter(Q(notify_id__in=NotifyStudent.objects.filter
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

            placementstatus = PlacementStatus.objects.select_related('unique_id','notify_id').filter(
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

        return render_to_pdf('placementModule/pdf_invitation_status.html', context)

    if 'excel_gen_invitation_status' in request.POST:

        placementstatus = None
        if 'excel_gen_invitation_status_placement' in request.POST:
            stuname = request.session['mn_stuname']
            ctc = request.session['mn_ctc']
            cname = request.session['mn_cname']
            rollno = request.session['mn_rollno']

            placementstatus = PlacementStatus.objects.select_related('unique_id','notify_id').filter(Q(notify_id__in=NotifyStudent.objects.filter
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

            placementstatus = PlacementStatus.objects.select_related('unique_id','notify_id').filter(
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
    if request.user.is_staff==True:
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
            student_record_check = 1
            form1 = SearchStudentRecord(request.POST)
            if form1.is_valid():
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


            return render_to_pdf('placementModule/pdf_student_record.html', context)

        # excel generation logic
        if 'excel_gen_std_record' in request.POST:

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


            return export_to_xls_std_records(students)


        # for sending the invite to students for particular schedule
        if 'sendinvite' in request.POST:
            # invitecheck=1;

            form13 = SendInvite(request.POST)

            if form13.is_valid():
                if form13.cleaned_data['company']:
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
                    ).exclude(id__in = PlacementStatus.objects.select_related('unique_id','notify_id').filter(
                        notify_id=notify).values_list('unique_id', flat=True))

                    PlacementStatus.objects.bulk_create( [PlacementStatus(notify_id=notify,
                                unique_id=student, no_of_days=no_of_days) for student in students] )

                    for st in students:
                        placement_cell_notif(request.user, st.id.user, "")

                    students = ''
                    messages.success(request, 'Notification Sent')
                else:
                    messages.error(request, 'Problem Occurred!! Please Try Again!!')

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

        return render(request, 'placementModule/studentrecords.html', context)
    return redirect('/placement')


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
                studentr = StudentRecord.objects.select_related('unique_id','record_id').create(record_id=placementr,
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
                studentr = StudentRecord.objects.select_related('unique_id','record_id').create(record_id=placementr,
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
                studentr = StudentRecord.objects.select_related('unique_id','record_id').create(record_id=placementr,
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
                    year = form.cleaned_data['year']
                    s = Student.objects.filter((Q(id__in=ExtraInfo.objects.filter
                        (Q(user__in=User.objects.filter
                           (Q(first_name__icontains=stuname)),
                           id__icontains=rollno))
                        )))

                    p = PlacementRecord.objects.filter(Q(placement_type="PLACEMENT", name__icontains=cname, ctc__gte=ctc, year=year))

                    placementrecord = StudentRecord.objects.select_related('unique_id','record_id').select_related('unique_id','record_id').filter(Q(record_id__in=PlacementRecord.objects.filter(Q(placement_type="PLACEMENT", name__icontains=cname, ctc__gte=ctc, year=year)), unique_id__in=Student.objects.filter((Q(id__in=ExtraInfo.objects.filter(Q(user__in=User.objects.filter(Q(first_name__icontains=stuname)),id__icontains=rollno)))))))
                else:
                    s = Student.objects.filter((Q(id__in=ExtraInfo.objects.filter
                        (Q(user__in=User.objects.filter
                           (Q(first_name__icontains=stuname)),
                           id__icontains=rollno))
                        )))

                    p = PlacementRecord.objects.filter(Q(placement_type="PLACEMENT", name__icontains=cname, ctc__gte=ctc))

                    placementrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
            if request.GET.get('page') != None:
                try:
                    if request.session['year']:
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

                        placementrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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

                        placementrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
                    pbirecord = StudentRecord.objects.select_related('unique_id','record_id').filter(Q(record_id__in=PlacementRecord.objects.filter
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
                    pbirecord = StudentRecord.objects.select_related('unique_id','record_id').filter(Q(record_id__in=PlacementRecord.objects.filter
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
                try:
                    if request.session['year']:
                        pbirecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
                        pbirecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
                    higherrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(Q(record_id__in=PlacementRecord.objects.filter
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
                    higherrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
                try:
                    if request.session['year']:
                        higherrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
                        higherrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
def delete_invite_status(request):
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
            PlacementStatus.objects.select_related('unique_id','notify_id').get(pk=delete_invit_status_key).delete()
            messages.success(request, 'Invitation Deleted Successfully')
        except Exception as e:
            logger.error(e)

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
        # 'current':current,
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
def placement_statistics(request):
    '''
    logic of the view shown under Placement Statistics tab
    '''
    user = request.user

    statistics_tab = 1
    strecord_tab=1
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
    studentrecord = StudentRecord.objects.select_related('unique_id','record_id').all()

    years = PlacementRecord.objects.filter(~Q(placement_type="HIGHER STUDIES")).values('year').annotate(Count('year'))
    records = PlacementRecord.objects.values('name', 'year', 'ctc', 'placement_type').annotate(Count('name'), Count('year'), Count('placement_type'), Count('ctc'))




    #working here to fetch all placement record
    all_records=PlacementRecord.objects.all()
    print(all_records)






    invitecheck=0
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
    if len(current) == 0:
        current = None
    pbirecord= ''
    placementrecord= ''
    higherrecord= ''
    total_query=0
    total_query1 = 0
    total_query2= 0
    p=""
    p1=""
    p2=""
    placement_search_record=" "
    pbi_search_record=" "
    higher_search_record=" "
    # results of the searched query under placement tab
    if 'studentplacementrecordsubmit' in request.POST:
        officer_statistics_past = 1
        form = SearchPlacementRecord(request.POST)
        if form.is_valid():




            print("IS VALID")



            #for student name
            if form.cleaned_data['stuname']:
                stuname = form.cleaned_data['stuname']
                try:
                    first_name = stuname.split(" ")[0]
                    last_name = stuname.split(" ")[1]
                except Exception as e:
                    print("Error")
                    print(e)
                    first_name = stuname
                    last_name = ''
            else:
                stuname = ''
                first_name = ''
                last_name = ''


            # for student CTC
            if form.cleaned_data['ctc']:
                ctc = form.cleaned_data['ctc']
            else:
                ctc = 0

            #for company name
            if form.cleaned_data['cname']:
                cname = form.cleaned_data['cname']
            else:
                cname = ''

            #for student roll
            if form.cleaned_data['roll']:
                rollno = form.cleaned_data['roll']
            else:
                rollno = ''

            #for admission year
            if form.cleaned_data['year']:
                year = form.cleaned_data['year']
                s = Student.objects.filter((Q(id__in=ExtraInfo.objects.filter(
                    Q(user__in=User.objects.filter(
                        first_name__icontains=first_name,
                        last_name__icontains=last_name),
                       id__icontains=rollno))
                    )))

                p = PlacementRecord.objects.filter(Q(placement_type="PLACEMENT",name__icontains=stuname, ctc__icontains=ctc, year__icontains=year))

            print(p)


            total_query = p.count()

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
        if request.GET.get('page') != None:
            try:
                if request.session['year']:
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


                    placementrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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

                    placementrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
                no_records=1
            print(placementrecord)
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

    if total_query!=0:
        placement_search_record=p
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
                pbirecord = StudentRecord.objects.select_related('unique_id','record_id').filter(Q(record_id__in=PlacementRecord.objects.filter
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
                p1 = PlacementRecord.objects.filter(
                    Q(placement_type="PBI", name__icontains=stuname, ctc__icontains=ctc, year__icontains=year))
            """else:
                pbirecord = StudentRecord.objects.select_related('unique_id','record_id').filter(Q(record_id__in=PlacementRecord.objects.filter
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
"""
            total_query1 = p1.count()

            if total_query1 > 30:
                pagination_pbi = 1
                paginator = Paginator(pbirecord, 30)
                page = request.GET.get('page', 1)
                pbirecord = paginator.page(page)
                page = int(page)
                total_page = int(page + 3)

                if page<(paginator.num_pages-3):
                    if total_query1 > 30 and total_query1 <=60:
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
            try:
                if request.session['year']:
                    pbirecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
                    pbirecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
    if total_query1!=0:
        pbi_search_record=p1

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
                higherrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(Q(record_id__in=PlacementRecord.objects.filter
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

                p2 = PlacementRecord.objects.filter(
                    Q(placement_type="HIGHER STUDIES", name__icontains=stuname, year__icontains=year))

            """else:
                # result of the query when year is not given
                higherrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
            request.session['year'] = form.cleaned_data['year']"""

            total_query2 = p2.count()

            if total_query2 > 30:
                pagination_higher = 1
                paginator = Paginator(p2, 30)
                page = request.GET.get('page', 1)
                p2 = paginator.page(page)
                page = int(page)
                total_page = int(page+3)

                if page < (paginator.num_pages-3):
                    if total_query2 > 30 and total_query2 <= 60:
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
                    higherrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
                    higherrecord = StudentRecord.objects.select_related('unique_id','record_id').filter(
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
    if total_query2!=0:
        higher_search_record=p2

    context = {
        'form2'             :            form2,
        'form3'             :            form3,
        'form4'             :            form4,
        'current'           :          current,
        'current1'          :         current1,
        'current2'          :         current2,


        'all_records':          all_records,   #for flashing all placement Schedule

        'placement_search_record': placement_search_record,
        'pbi_search_record': pbi_search_record,
        'higher_search_record': higher_search_record,



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
    if 'deleterecord' in request.POST or 'deleterecordmanaged' in request.POST:
        try:
            if 'deleterecord' in request.POST:
                record_id = int(request.POST['deleterecord'])
            elif 'deleterecordmanaged' in request.POST:
                record_id = int(request.POST['deleterecordmanaged'])

            student_record =  StudentRecord.objects.get(pk=record_id)
            PlacementRecord.objects.get(id=student_record.record_id.id).delete()
            student_record.delete()
            messages.success(request, 'Placement Statistics deleted Successfully!!')

        except Exception as e:
            messages.error(request, 'Problem Occurred!! Please Try Again!!')
            print(e)


    if 'deleterecordmanaged' in request.POST:
        return redirect('/placement/manage_records/')

    return redirect('/placement/statistics/')


def cv(request, username):
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



    user = get_object_or_404(User, Q(username=username))
    profile = get_object_or_404(ExtraInfo, Q(user=user))
    student_info=get_object_or_404(Student,Q(id=user.username))

    batch=student_info.batch

    now = datetime.datetime.now()
    print("year----->",now.year)
    if now.year-batch<=4:
        roll=now.year-batch
    else:
        roll=4
    

    student = get_object_or_404(Student, Q(id=profile.id))
    skills = Has.objects.select_related('skill_id','unique_id').filter(Q(unique_id=student))
    education = Education.objects.select_related('unique_id').filter(Q(unique_id=student))
    reference = Reference.objects.filter(id__in=reference_list)
    course = Course.objects.select_related('unique_id').filter(Q(unique_id=student))
    experience = Experience.objects.select_related('unique_id').filter(Q(unique_id=student))
    project = Project.objects.select_related('unique_id').filter(Q(unique_id=student))
    achievement = Achievement.objects.select_related('unique_id').filter(Q(unique_id=student))
    extracurricular = Extracurricular.objects.select_related('unique_id').filter(Q(unique_id=student))
    conference = Conference.objects.select_related('unique_id').filter(Q(unique_id=student))
    publication = Publication.objects.select_related('unique_id').filter(Q(unique_id=student))
    patent = Patent.objects.select_related('unique_id').filter(Q(unique_id=student))
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

    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Roll No.', 'Name', 'CPI', 'Department', 'Discipline', 'Placed', 'Debarred' ]

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

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
def resume(request, username):
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
    skills = Has.objects.select_related('skill_id','unique_id').filter(Q(unique_id=student))
    education = Education.objects.select_related('unique_id').filter(Q(unique_id=student))
    reference = Reference.objects.filter(id__in=reference_list)
    course = Course.objects.select_related('unique_id').filter(Q(unique_id=student))
    experience = Experience.objects.select_related('unique_id').filter(Q(unique_id=student))
    project = Project.objects.select_related('unique_id').filter(Q(unique_id=student))
    achievement = Achievement.objects.select_related('unique_id').filter(Q(unique_id=student))
    extracurricular = Extracurricular.objects.select_related('unique_id').filter(Q(unique_id=student))
    conference = Conference.objects.select_related('unique_id').filter(Q(unique_id=student))
    publication = Publication.objects.select_related('unique_id').filter(Q(unique_id=student))
    patent = Patent.objects.select_related('unique_id').filter(Q(unique_id=student))
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



def export_to_xls_invitation_status(qs):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="report.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Report')


    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Roll No.', 'Name', 'Company', 'CTC', 'Invitation Status']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)


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
                    ps.invitation = 'IGNORE'
                    ps.save()
    except Exception as e:
        print('---------------------Error Occurred ---------------')
        print(e)

    return

def add_placement_schedule(request):
    add_schedule_tab=1
    user = request.user
    isStaff=user.is_staff
    current1 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement chairman"))
    current2 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement officer"))
    current = HoldsDesignation.objects.filter(Q(working=user, designation__name="student"))

    all_schedule_data=PlacementSchedule.objects.all()
    students=NotifyStudent.objects.all()

    print(students)
    apply_for=Role.objects.all()
    print(all_schedule_data)
    context={
        'isStaff': isStaff,
        'current': current,
        'current1':current1,
        'current2':current2,
        'add_schedule_tab': add_schedule_tab,
        'students': students,
        'apply_for':apply_for,
    }
    return render(request, 'placementModule/add_placement_schedule.html', context)

def placement_schedule_save(request):
    if request.method!="POST":
        return HttpResponse("Method Not Allowed")
    else:
        placement_type=request.POST.get("placement_type")
        company_name=request.POST.get("company_name")
        ctc=request.POST.get("ctc")
        description=request.POST.get("description")
        timestamp=request.POST.get("time_stamp")
        title=request.POST.get("title")
        location = request.POST.get("location")
        role = request.POST.get("role")
        resume = request.POST.get("resume")
        schedule_at = request.POST.get("schedule_at")
        date = request.POST.get("placement_date")
        try:
            role_create=Role.objects.create(role=role)
            notify = NotifyStudent.objects.create(placement_type=placement_type,
                                                      company_name=company_name,
                                                      description=description,
                                                      ctc=ctc,
                                                      timestamp=timestamp)

            schedule = PlacementSchedule.objects.create(notify_id=notify,
                                                                                        title=company_name,
                                                                                        description=description,
                                                                                        placement_date=date,
                                                                                        attached_file=resume,
                                                                                        role=role_create,
                                                                                        location=location, time=schedule_at)
            print(schedule)
            notify.save()
            schedule.save()
            messages.success(request,"Successfully Added Schedule")
            return redirect("/placement/add_placement_schedule/")
        except:
            messages.error(request,"Failed to Add Schedule")
            return redirect("/placement/add_placement_schedule/")


def delete_placement_record(request):
    if 'delete_stats' in request.POST and request.POST['delete_stats']:
        try:
            if 'delete_stats' in request.POST:
                record_id = int(request.POST['delete_stats'])


            PlacementRecord.objects.filter(id=record_id).delete()

            messages.success(request, 'Placement Statistics deleted Successfully!!')

        except Exception as e:
            messages.error(request, 'Problem Occurred!! Please Try Again!!')
            print(e)


    return redirect('/placement/statistics/')

def add_placement_record(request):
    add_record_tab = 1
    user=request.user
    current2 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement officer"))
    current = HoldsDesignation.objects.filter(Q(working=user, designation__name="student"))

    #print(all_record_data)
    context = {
        'add_record_tab': add_record_tab,
        'current':current,
        'current2':current2,
    }
    return render(request, 'placementModule/add_placement_record.html', context)


def placement_record_save(request):
    if request.method!="POST":
        return HttpResponse("Method Not Allowed")
    else:
        placement_type=request.POST.get("placement_type")
        print(placement_type)
        student_name=request.POST.get("student_name")
        ctc=request.POST.get("ctc")
        year=request.POST.get("year")
        test_type=request.POST.get("test_type")
        test_score=request.POST.get("test_score")
        try:
            print("In try!!!")
            record = PlacementRecord.objects.create(placement_type=placement_type,name=student_name,ctc=ctc,year=year,test_type=test_type,test_score=test_score)
            print(record)
            record.save()
            messages.success(request,"Successfully Added Record")
            return redirect("/placement/add_placement_record/")
        except:
            messages.error(request,"Failed to Add Schedule")
            return redirect("/placement/add_placement_record/")

def add_placement_visit(request):
    add_visit_tab = 1
    user=request.user
    current1 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement chairman"))


    all_placement_visits=ChairmanVisit.objects.all()
    context = {
        'add_visit_tab': add_visit_tab,
        'all_placement_visits':all_placement_visits,
        'current1':current1,

    }
    return render(request, 'placementModule/add_placement_visits.html', context)

def update_placement_data(request):
    add_record_tab = 1
    user=request.user
    current2 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement officer"))
    current = HoldsDesignation.objects.filter(Q(working=user, designation__name="student"))

    #print(all_record_data)
    context = {
        'add_record_tab': add_record_tab,
        'current':current,
        'current2':current2,
    }
    return render(request, 'placementModule/add_placement_record.html', context)
def placement_visit_save(request):
    if request.method!="POST":
        return HttpResponse("Method Not Allowed")
    else:
        company_name=request.POST.get("cname")
        location=request.POST.get("location")
        desc=request.POST.get("desc")
        date=request.POST.get("date")
        timestamp=request.POST.get("timed")

        try:
            print("In try!!!")
            record = ChairmanVisit.objects.create(company_name=company_name,location=location,visiting_date=date,description=desc,timestamp=timestamp)

            record.save()
            messages.success(request,"Successfully Added Chairman Visit")
            return redirect("/placement/add_placement_visit/")
        except:
            messages.error(request,"Failed to Add Chairman Visit")
            return redirect("/placement/add_placement_visit/")


# =============================================
# PCMS NEW VIEWS
# =============================================

def _get_user_roles(user):
    """Helper to determine user's placement roles."""
    is_chairman = HoldsDesignation.objects.filter(
        Q(working=user, designation__name="placement chairman")
    ).exists()
    is_officer = HoldsDesignation.objects.filter(
        Q(working=user, designation__name="placement officer")
    ).exists()
    is_student = HoldsDesignation.objects.filter(
        Q(working=user, designation__name="student")
    ).exists()
    return is_chairman, is_officer, is_student


# ---------- Company Management ----------

@login_required
def company_list(request):
    """List all registered companies."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)

    if is_officer or is_chairman:
        companies = Company.objects.all()
    else:
        companies = Company.objects.filter(approval_status='APPROVED')

    context = {
        'companies': companies,
        'is_chairman': is_chairman,
        'is_officer': is_officer,
        'is_student': is_student,
    }
    return render(request, 'placementModule/pcms/company_list.html', context)


@login_required
def register_company(request):
    """TPO registers a new company."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)

    if not (is_officer or is_chairman):
        messages.error(request, "You are not authorized to register companies.")
        return redirect('/placement/')

    if request.method == 'POST':
        form = CompanyRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                company = Company.objects.create(
                    name=form.cleaned_data['name'],
                    website=form.cleaned_data.get('website', ''),
                    description=form.cleaned_data.get('description', ''),
                    domain=form.cleaned_data.get('domain', ''),
                    contact_person_name=form.cleaned_data.get('contact_person_name', ''),
                    contact_email=form.cleaned_data['contact_email'],
                    contact_phone=form.cleaned_data.get('contact_phone', ''),
                    address=form.cleaned_data.get('address', ''),
                    logo=form.cleaned_data.get('logo'),
                    approval_status='APPROVED',
                    approved_by=user,
                    registered_by=user,
                )
                messages.success(request, "Company '{}' registered successfully.".format(company.name))
                return redirect('/placement/companies/')
            except Exception as e:
                messages.error(request, "Failed to register company: {}".format(str(e)))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CompanyRegistrationForm()

    context = {
        'form': form,
        'is_chairman': is_chairman,
        'is_officer': is_officer,
    }
    return render(request, 'placementModule/pcms/register_company.html', context)


@login_required
def approve_company(request, company_id):
    """TPO approves or rejects a company registration."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)

    if not (is_officer or is_chairman):
        messages.error(request, "Not authorized.")
        return redirect('/placement/')

    company = get_object_or_404(Company, id=company_id)

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'approve':
            company.approval_status = 'APPROVED'
            company.approved_by = user
            company.save()
            messages.success(request, "Company '{}' approved.".format(company.name))
        elif action == 'reject':
            company.approval_status = 'REJECTED'
            company.approved_by = user
            company.save()
            messages.success(request, "Company '{}' rejected.".format(company.name))

    return redirect('/placement/companies/')


@login_required
def company_detail(request, company_id):
    """View company details and its job postings."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)
    company = get_object_or_404(Company, id=company_id)
    job_postings = company.job_postings.filter(is_active=True).order_by('-created_at')

    context = {
        'company': company,
        'job_postings': job_postings,
        'is_chairman': is_chairman,
        'is_officer': is_officer,
        'is_student': is_student,
    }
    return render(request, 'placementModule/pcms/company_detail.html', context)


# ---------- Job Posting Management ----------

@login_required
def job_posting_list(request):
    """List all active job postings. Students see only eligible ones."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)
    profile = get_object_or_404(ExtraInfo, Q(user=user))

    if is_officer or is_chairman:
        postings = JobPosting.objects.select_related('company').all()
    else:
        postings = JobPosting.objects.select_related('company').filter(is_active=True)

    # Pagination
    paginator = Paginator(postings, 10)
    page = request.GET.get('page', 1)
    postings_page = paginator.get_page(page)

    context = {
        'postings': postings_page,
        'is_chairman': is_chairman,
        'is_officer': is_officer,
        'is_student': is_student,
    }
    return render(request, 'placementModule/pcms/job_posting_list.html', context)


@login_required
def create_job_posting(request):
    """TPO creates a new job posting."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)

    if not (is_officer or is_chairman):
        messages.error(request, "Not authorized to create job postings.")
        return redirect('/placement/')

    if request.method == 'POST':
        form = JobPostingForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                posting = JobPosting.objects.create(
                    company=form.cleaned_data['company'],
                    title=form.cleaned_data['title'],
                    description=form.cleaned_data['description'],
                    job_type=form.cleaned_data['job_type'],
                    location=form.cleaned_data.get('location', ''),
                    ctc=form.cleaned_data['ctc'],
                    bond_details=form.cleaned_data.get('bond_details', ''),
                    min_cpi=form.cleaned_data.get('min_cpi', 0.0) or 0.0,
                    eligible_programmes=','.join(form.cleaned_data.get('eligible_programmes', [])),
                    eligible_branches=','.join(form.cleaned_data.get('eligible_branches', [])),
                    eligible_batch_from=form.cleaned_data.get('eligible_batch_from'),
                    eligible_batch_to=form.cleaned_data.get('eligible_batch_to'),
                    backlog_allowed=form.cleaned_data.get('backlog_allowed', False),
                    application_deadline=form.cleaned_data['application_deadline'],
                    posted_by=user,
                    attached_file=form.cleaned_data.get('attached_file'),
                )
                # Set required skills M2M
                skills = form.cleaned_data.get('required_skills')
                if skills:
                    posting.required_skills.set(skills)

                # Notify eligible students
                _notify_eligible_students(posting, user)

                messages.success(request, "Job posting '{}' created successfully.".format(posting.title))
                return redirect('/placement/jobs/')
            except Exception as e:
                messages.error(request, "Failed to create job posting: {}".format(str(e)))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = JobPostingForm()

    context = {
        'form': form,
        'is_chairman': is_chairman,
        'is_officer': is_officer,
    }
    return render(request, 'placementModule/pcms/create_job_posting.html', context)


def _notify_eligible_students(posting, sender_user):
    """Send notifications to students who may be eligible for the posting."""
    try:
        from notification.views import placement_cell_notif
        students = Student.objects.select_related('id', 'id__user', 'id__department').all()
        for student in students:
            is_eligible, _ = check_eligibility(student, posting)
            if is_eligible:
                placement_cell_notif(
                    sender=sender_user,
                    recipient=student.id.user,
                    type='new_job_posting'
                )
    except Exception as e:
        logger.error("Error notifying students: {}".format(str(e)))


@login_required
def job_posting_detail(request, posting_id):
    """View details of a job posting. Students can check eligibility and apply."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)
    profile = get_object_or_404(ExtraInfo, Q(user=user))
    posting = get_object_or_404(JobPosting, id=posting_id)

    eligibility_result = None
    has_applied = False
    application = None

    if is_student:
        try:
            student = Student.objects.get(id=profile)
            is_eligible, reasons = check_eligibility(student, posting)
            eligibility_result = {'eligible': is_eligible, 'reasons': reasons}
            has_applied = check_duplicate_application(student, posting)
            if has_applied:
                application = JobApplication.objects.filter(
                    student=student, job_posting=posting
                ).first()
        except Student.DoesNotExist:
            pass

    applications = None
    if is_officer or is_chairman:
        applications = posting.applications.select_related(
            'student', 'student__id', 'student__id__user'
        ).all()

    context = {
        'posting': posting,
        'eligibility_result': eligibility_result,
        'has_applied': has_applied,
        'application': application,
        'applications': applications,
        'is_chairman': is_chairman,
        'is_officer': is_officer,
        'is_student': is_student,
    }
    return render(request, 'placementModule/pcms/job_posting_detail.html', context)


@login_required
def edit_job_posting(request, posting_id):
    """TPO edits an existing job posting."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)

    if not (is_officer or is_chairman):
        messages.error(request, "Not authorized.")
        return redirect('/placement/')

    posting = get_object_or_404(JobPosting, id=posting_id)

    if request.method == 'POST':
        form = JobPostingForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                posting.company = form.cleaned_data['company']
                posting.title = form.cleaned_data['title']
                posting.description = form.cleaned_data['description']
                posting.job_type = form.cleaned_data['job_type']
                posting.location = form.cleaned_data.get('location', '')
                posting.ctc = form.cleaned_data['ctc']
                posting.bond_details = form.cleaned_data.get('bond_details', '')
                posting.min_cpi = form.cleaned_data.get('min_cpi', 0.0) or 0.0
                posting.eligible_programmes = ','.join(form.cleaned_data.get('eligible_programmes', []))
                posting.eligible_branches = ','.join(form.cleaned_data.get('eligible_branches', []))
                posting.eligible_batch_from = form.cleaned_data.get('eligible_batch_from')
                posting.eligible_batch_to = form.cleaned_data.get('eligible_batch_to')
                posting.backlog_allowed = form.cleaned_data.get('backlog_allowed', False)
                posting.application_deadline = form.cleaned_data['application_deadline']
                if form.cleaned_data.get('attached_file'):
                    posting.attached_file = form.cleaned_data['attached_file']
                posting.save()

                skills = form.cleaned_data.get('required_skills')
                if skills:
                    posting.required_skills.set(skills)

                messages.success(request, "Job posting updated successfully.")
                return redirect('/placement/jobs/{}/'.format(posting.id))
            except Exception as e:
                messages.error(request, "Failed to update: {}".format(str(e)))
    else:
        initial_data = {
            'company': posting.company,
            'title': posting.title,
            'description': posting.description,
            'job_type': posting.job_type,
            'location': posting.location,
            'ctc': posting.ctc,
            'bond_details': posting.bond_details,
            'min_cpi': posting.min_cpi,
            'eligible_programmes': posting.eligible_programmes.split(',') if posting.eligible_programmes else [],
            'eligible_branches': posting.eligible_branches.split(',') if posting.eligible_branches else [],
            'eligible_batch_from': posting.eligible_batch_from,
            'eligible_batch_to': posting.eligible_batch_to,
            'backlog_allowed': posting.backlog_allowed,
            'application_deadline': posting.application_deadline,
            'required_skills': posting.required_skills.all(),
        }
        form = JobPostingForm(initial=initial_data)

    context = {
        'form': form,
        'posting': posting,
        'is_chairman': is_chairman,
        'is_officer': is_officer,
        'editing': True,
    }
    return render(request, 'placementModule/pcms/create_job_posting.html', context)


@login_required
def toggle_job_posting(request, posting_id):
    """Activate/deactivate a job posting."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)

    if not (is_officer or is_chairman):
        messages.error(request, "Not authorized.")
        return redirect('/placement/')

    posting = get_object_or_404(JobPosting, id=posting_id)
    posting.is_active = not posting.is_active
    posting.save()
    status = "activated" if posting.is_active else "deactivated"
    messages.success(request, "Job posting {} {}.".format(posting.title, status))
    return redirect('/placement/jobs/')


# ---------- Job Application Management ----------

@login_required
def apply_for_job(request, posting_id):
    """Student applies for a job posting."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)

    if not is_student:
        messages.error(request, "Only students can apply for jobs.")
        return redirect('/placement/')

    profile = get_object_or_404(ExtraInfo, Q(user=user))
    posting = get_object_or_404(JobPosting, id=posting_id)

    try:
        student = Student.objects.get(id=profile)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('/placement/jobs/')

    # Check duplicate
    if check_duplicate_application(student, posting):
        messages.warning(request, "You have already applied for this position.")
        return redirect('/placement/jobs/{}/'.format(posting_id))

    # Check eligibility
    is_eligible, reasons = check_eligibility(student, posting)
    if not is_eligible:
        for reason in reasons:
            messages.error(request, reason)
        return redirect('/placement/jobs/{}/'.format(posting_id))

    # Check placement policy
    can_apply, policy_reason = check_placement_policy(student, posting)
    if not can_apply:
        messages.error(request, policy_reason)
        return redirect('/placement/jobs/{}/'.format(posting_id))

    if request.method == 'POST':
        try:
            resume = request.FILES.get('resume', None)
            application = JobApplication.objects.create(
                job_posting=posting,
                student=student,
                status='APPLIED',
                resume_link=resume,
            )
            messages.success(request, "Successfully applied for '{}' at '{}'.".format(
                posting.title, posting.company.name
            ))

            # Notify TPO
            try:
                from notification.views import placement_cell_notif
                tpo_designations = HoldsDesignation.objects.filter(
                    designation__name="placement officer"
                )
                for hd in tpo_designations:
                    placement_cell_notif(
                        sender=user,
                        recipient=hd.working,
                        type='new_application'
                    )
            except Exception:
                pass

            return redirect('/placement/my-applications/')
        except Exception as e:
            messages.error(request, "Failed to submit application: {}".format(str(e)))

    return redirect('/placement/jobs/{}/'.format(posting_id))


@login_required
def my_applications(request):
    """Student views their application history and status."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)

    if not is_student:
        messages.error(request, "Only students can view their applications.")
        return redirect('/placement/')

    profile = get_object_or_404(ExtraInfo, Q(user=user))

    try:
        student = Student.objects.get(id=profile)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('/placement/')

    summary = get_student_application_summary(student)

    context = {
        'summary': summary,
        'is_student': True,
    }
    return render(request, 'placementModule/pcms/my_applications.html', context)


@login_required
def manage_applications(request, posting_id):
    """TPO manages applications for a job posting (shortlist, reject, etc.)."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)

    if not (is_officer or is_chairman):
        messages.error(request, "Not authorized.")
        return redirect('/placement/')

    posting = get_object_or_404(JobPosting, id=posting_id)
    applications = posting.applications.select_related(
        'student', 'student__id', 'student__id__user', 'student__id__department'
    ).all()

    if request.method == 'POST':
        app_id = request.POST.get('application_id')
        new_status = request.POST.get('new_status')
        remarks = request.POST.get('remarks', '')

        if app_id and new_status:
            try:
                app = JobApplication.objects.get(id=app_id, job_posting=posting)
                valid_statuses = [s[0] for s in PlacementConstants.APPLICATION_STATUS]
                if new_status in valid_statuses:
                    app.status = new_status
                    if remarks:
                        app.remarks = remarks
                    app.save()

                    # Notify student of status change
                    try:
                        from notification.views import placement_cell_notif
                        placement_cell_notif(
                            sender=user,
                            recipient=app.student.id.user,
                            type='application_status_update'
                        )
                    except Exception:
                        pass

                    messages.success(request, "Application status updated to '{}'.".format(new_status))
                else:
                    messages.error(request, "Invalid status.")
            except JobApplication.DoesNotExist:
                messages.error(request, "Application not found.")

    # Filter options
    status_filter = request.GET.get('status', '')
    if status_filter:
        applications = applications.filter(status=status_filter)

    context = {
        'posting': posting,
        'applications': applications,
        'status_choices': PlacementConstants.APPLICATION_STATUS,
        'status_filter': status_filter,
        'is_chairman': is_chairman,
        'is_officer': is_officer,
    }
    return render(request, 'placementModule/pcms/manage_applications.html', context)


@login_required
def bulk_shortlist(request, posting_id):
    """TPO bulk shortlists multiple applications."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)

    if not (is_officer or is_chairman):
        messages.error(request, "Not authorized.")
        return redirect('/placement/')

    if request.method == 'POST':
        app_ids = request.POST.getlist('application_ids')
        if app_ids:
            updated = JobApplication.objects.filter(
                id__in=app_ids, job_posting_id=posting_id, status='APPLIED'
            ).update(status='SHORTLISTED')

            # Notify shortlisted students
            try:
                from notification.views import placement_cell_notif
                shortlisted_apps = JobApplication.objects.filter(
                    id__in=app_ids, job_posting_id=posting_id
                ).select_related('student__id__user')
                for app in shortlisted_apps:
                    placement_cell_notif(
                        sender=user,
                        recipient=app.student.id.user,
                        type='shortlisted'
                    )
            except Exception:
                pass

            messages.success(request, "{} application(s) shortlisted.".format(updated))

    return redirect('/placement/jobs/{}/applications/'.format(posting_id))


# ---------- Interview Management ----------

@login_required
def schedule_interview(request, posting_id):
    """TPO schedules an interview for a job posting."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)

    if not (is_officer or is_chairman):
        messages.error(request, "Not authorized.")
        return redirect('/placement/')

    posting = get_object_or_404(JobPosting, id=posting_id)

    if request.method == 'POST':
        form = InterviewScheduleForm(request.POST)
        if form.is_valid():
            try:
                interview = InterviewSchedule.objects.create(
                    job_posting=posting,
                    date=form.cleaned_data['date'],
                    time_slot=form.cleaned_data['time_slot'],
                    mode=form.cleaned_data['mode'],
                    venue_or_link=form.cleaned_data.get('venue_or_link', ''),
                    description=form.cleaned_data.get('description', ''),
                    created_by=user,
                )

                # Add shortlisted students to interview panel
                shortlisted = posting.applications.filter(status='SHORTLISTED')
                for app in shortlisted:
                    InterviewPanel.objects.create(
                        interview=interview,
                        application=app,
                    )
                    app.status = 'INTERVIEW_SCHEDULED'
                    app.save()

                # Notify students
                try:
                    from notification.views import placement_cell_notif
                    for app in shortlisted:
                        placement_cell_notif(
                            sender=user,
                            recipient=app.student.id.user,
                            type='interview_scheduled'
                        )
                except Exception:
                    pass

                messages.success(request, "Interview scheduled for {} on {}.".format(
                    posting.title, form.cleaned_data['date']
                ))
                return redirect('/placement/jobs/{}/'.format(posting_id))
            except Exception as e:
                messages.error(request, "Failed to schedule interview: {}".format(str(e)))
    else:
        form = InterviewScheduleForm()

    shortlisted_count = posting.applications.filter(status='SHORTLISTED').count()
    interviews = posting.interviews.all()

    context = {
        'form': form,
        'posting': posting,
        'shortlisted_count': shortlisted_count,
        'interviews': interviews,
        'is_chairman': is_chairman,
        'is_officer': is_officer,
    }
    return render(request, 'placementModule/pcms/schedule_interview.html', context)


@login_required
def interview_detail(request, interview_id):
    """View interview details and panelist results."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)

    interview = get_object_or_404(InterviewSchedule, id=interview_id)
    panelists = interview.panelists.select_related(
        'application', 'application__student', 'application__student__id__user'
    ).all()

    if request.method == 'POST' and (is_officer or is_chairman):
        panel_id = request.POST.get('panel_id')
        result = request.POST.get('result')
        remarks = request.POST.get('remarks', '')
        if panel_id and result:
            try:
                panel = InterviewPanel.objects.get(id=panel_id, interview=interview)
                panel.result = result
                panel.remarks = remarks
                panel.save()

                if result == 'SELECTED':
                    panel.application.status = 'OFFER_EXTENDED'
                    panel.application.save()
                elif result == 'REJECTED':
                    panel.application.status = 'REJECTED'
                    panel.application.save()

                messages.success(request, "Interview result updated.")
            except InterviewPanel.DoesNotExist:
                messages.error(request, "Panel entry not found.")

    context = {
        'interview': interview,
        'panelists': panelists,
        'is_chairman': is_chairman,
        'is_officer': is_officer,
        'is_student': is_student,
    }
    return render(request, 'placementModule/pcms/interview_detail.html', context)


# ---------- Offer Management ----------

@login_required
def extend_offer(request, application_id):
    """TPO extends a job offer to a selected student."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)

    if not (is_officer or is_chairman):
        messages.error(request, "Not authorized.")
        return redirect('/placement/')

    application = get_object_or_404(JobApplication, id=application_id)

    # Check if offer already exists
    if hasattr(application, 'offer'):
        messages.warning(request, "An offer has already been extended for this application.")
        return redirect('/placement/jobs/{}/applications/'.format(application.job_posting.id))

    if request.method == 'POST':
        form = JobOfferForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                offer = JobOffer.objects.create(
                    application=application,
                    ctc_offered=form.cleaned_data['ctc_offered'],
                    designation_offered=form.cleaned_data.get('designation_offered', ''),
                    joining_date=form.cleaned_data.get('joining_date'),
                    offer_letter=form.cleaned_data.get('offer_letter'),
                    response_deadline=form.cleaned_data['response_deadline'],
                )
                application.status = 'OFFER_EXTENDED'
                application.save()

                # Notify student
                try:
                    from notification.views import placement_cell_notif
                    placement_cell_notif(
                        sender=user,
                        recipient=application.student.id.user,
                        type='offer_extended'
                    )
                except Exception:
                    pass

                messages.success(request, "Offer extended to {}.".format(
                    application.student.id.user.get_full_name()
                ))
                return redirect('/placement/jobs/{}/applications/'.format(application.job_posting.id))
            except Exception as e:
                messages.error(request, "Failed to extend offer: {}".format(str(e)))
    else:
        form = JobOfferForm(initial={
            'ctc_offered': application.job_posting.ctc,
        })

    context = {
        'form': form,
        'application': application,
        'is_chairman': is_chairman,
        'is_officer': is_officer,
    }
    return render(request, 'placementModule/pcms/extend_offer.html', context)


@login_required
def my_offers(request):
    """Student views their job offers."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)

    if not is_student:
        messages.error(request, "Only students can view offers.")
        return redirect('/placement/')

    profile = get_object_or_404(ExtraInfo, Q(user=user))
    try:
        student = Student.objects.get(id=profile)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('/placement/')

    # Expire stale offers first
    expire_pending_offers()

    offers = JobOffer.objects.filter(
        application__student=student
    ).select_related(
        'application', 'application__job_posting', 'application__job_posting__company'
    ).all()

    context = {
        'offers': offers,
        'is_student': True,
    }
    return render(request, 'placementModule/pcms/my_offers.html', context)


@login_required
def respond_to_offer(request, offer_id):
    """Student accepts or rejects a job offer."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)

    if not is_student:
        messages.error(request, "Only students can respond to offers.")
        return redirect('/placement/')

    offer = get_object_or_404(JobOffer, id=offer_id)
    profile = get_object_or_404(ExtraInfo, Q(user=user))

    try:
        student = Student.objects.get(id=profile)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('/placement/')

    # Verify the offer belongs to this student
    if offer.application.student != student:
        messages.error(request, "This offer does not belong to you.")
        return redirect('/placement/')

    if offer.status != 'PENDING':
        messages.warning(request, "This offer has already been {}.".format(offer.status.lower()))
        return redirect('/placement/my-offers/')

    if offer.is_deadline_passed:
        offer.status = 'EXPIRED'
        offer.save()
        messages.error(request, "The response deadline has passed. Offer expired.")
        return redirect('/placement/my-offers/')

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'accept':
            offer.status = 'ACCEPTED'
            offer.responded_at = timezone.now()
            offer.save()

            offer.application.status = 'OFFER_ACCEPTED'
            offer.application.save()

            # Update StudentPlacement record
            sp, created = StudentPlacement.objects.get_or_create(unique_id=student)
            sp.placed_type = 'PLACED'
            sp.placement_date = datetime.date.today()
            sp.package = offer.ctc_offered
            sp.save()

            messages.success(request, "Offer from '{}' accepted!".format(
                offer.application.job_posting.company.name
            ))

            # Notify TPO
            try:
                from notification.views import placement_cell_notif
                tpo_designations = HoldsDesignation.objects.filter(
                    designation__name="placement officer"
                )
                for hd in tpo_designations:
                    placement_cell_notif(
                        sender=user,
                        recipient=hd.working,
                        type='offer_accepted'
                    )
            except Exception:
                pass

        elif action == 'reject':
            offer.status = 'REJECTED'
            offer.responded_at = timezone.now()
            offer.save()

            offer.application.status = 'OFFER_REJECTED'
            offer.application.save()

            messages.success(request, "Offer from '{}' rejected.".format(
                offer.application.job_posting.company.name
            ))

    return redirect('/placement/my-offers/')


@login_required
def all_offers(request):
    """TPO views all offers across all companies."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)

    if not (is_officer or is_chairman):
        messages.error(request, "Not authorized.")
        return redirect('/placement/')

    offers = JobOffer.objects.select_related(
        'application', 'application__student', 'application__student__id',
        'application__student__id__user', 'application__job_posting',
        'application__job_posting__company'
    ).all()

    status_filter = request.GET.get('status', '')
    if status_filter:
        offers = offers.filter(status=status_filter)

    context = {
        'offers': offers,
        'offer_status_choices': PlacementConstants.OFFER_STATUS,
        'status_filter': status_filter,
        'is_chairman': is_chairman,
        'is_officer': is_officer,
    }
    return render(request, 'placementModule/pcms/all_offers.html', context)


# ---------- Reports & Analytics ----------

@login_required
def placement_reports(request):
    """Generate placement reports and analytics."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)

    form = ReportFilterForm(request.GET or None)

    year_filter = request.GET.get('year')
    dept_filter = request.GET.get('department')
    prog_filter = request.GET.get('programme')
    job_type_filter = request.GET.get('job_type')

    stats = get_placement_statistics(year=year_filter)

    # Additional filtered data
    offers_qs = JobOffer.objects.filter(status='ACCEPTED').select_related(
        'application__student__id__department',
        'application__student',
        'application__job_posting__company'
    )

    if year_filter:
        offers_qs = offers_qs.filter(application__job_posting__created_at__year=year_filter)
    if dept_filter:
        offers_qs = offers_qs.filter(application__student__id__department__name=dept_filter)
    if prog_filter:
        offers_qs = offers_qs.filter(application__student__programme=prog_filter)
    if job_type_filter:
        offers_qs = offers_qs.filter(application__job_posting__job_type=job_type_filter)

    # Company participation
    companies_participated = Company.objects.filter(
        approval_status='APPROVED',
        job_postings__is_active=True
    ).distinct().count()

    total_students = Student.objects.count()
    placed_students = JobOffer.objects.filter(status='ACCEPTED').values(
        'application__student'
    ).distinct().count()

    placement_rate = (placed_students / total_students * 100) if total_students > 0 else 0

    context = {
        'form': form,
        'stats': stats,
        'offers': offers_qs,
        'companies_participated': companies_participated,
        'total_students': total_students,
        'placed_students': placed_students,
        'placement_rate': round(placement_rate, 2),
        'is_chairman': is_chairman,
        'is_officer': is_officer,
        'is_student': is_student,
    }
    return render(request, 'placementModule/pcms/reports.html', context)


# ---------- Announcements ----------

@login_required
def announcement_list(request):
    """View all active announcements."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)

    announcements = Announcement.objects.filter(is_active=True)

    # Pagination
    paginator = Paginator(announcements, 10)
    page = request.GET.get('page', 1)
    announcements_page = paginator.get_page(page)

    context = {
        'announcements': announcements_page,
        'is_chairman': is_chairman,
        'is_officer': is_officer,
        'is_student': is_student,
    }
    return render(request, 'placementModule/pcms/announcement_list.html', context)


@login_required
def create_announcement(request):
    """TPO or Placement Chairman creates an announcement."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)

    if not (is_officer or is_chairman):
        messages.error(request, "Not authorized to create announcements.")
        return redirect('/placement/')

    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                announcement = Announcement.objects.create(
                    title=form.cleaned_data['title'],
                    content=form.cleaned_data['content'],
                    announcement_type=form.cleaned_data['announcement_type'],
                    target_audience=form.cleaned_data.get('target_audience', 'ALL'),
                    attached_file=form.cleaned_data.get('attached_file'),
                    created_by=user,
                )

                # Notify all students
                try:
                    from notification.views import placement_cell_notif
                    students = Student.objects.select_related('id__user').all()
                    for student in students:
                        placement_cell_notif(
                            sender=user,
                            recipient=student.id.user,
                            type='announcement'
                        )
                except Exception:
                    pass

                messages.success(request, "Announcement '{}' published.".format(announcement.title))
                return redirect('/placement/announcements/')
            except Exception as e:
                messages.error(request, "Failed to create announcement: {}".format(str(e)))
    else:
        form = AnnouncementForm()

    context = {
        'form': form,
        'is_chairman': is_chairman,
        'is_officer': is_officer,
    }
    return render(request, 'placementModule/pcms/create_announcement.html', context)


@login_required
def announcement_detail(request, announcement_id):
    """View a single announcement."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)
    announcement = get_object_or_404(Announcement, id=announcement_id)

    context = {
        'announcement': announcement,
        'is_chairman': is_chairman,
        'is_officer': is_officer,
        'is_student': is_student,
    }
    return render(request, 'placementModule/pcms/announcement_detail.html', context)


@login_required
def delete_announcement(request, announcement_id):
    """Deactivate an announcement."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)

    if not (is_officer or is_chairman):
        messages.error(request, "Not authorized.")
        return redirect('/placement/')

    announcement = get_object_or_404(Announcement, id=announcement_id)
    announcement.is_active = False
    announcement.save()
    messages.success(request, "Announcement '{}' removed.".format(announcement.title))
    return redirect('/placement/announcements/')


# ---------- Placement Policy Management ----------

@login_required
def manage_policies(request):
    """TPO manages placement policies."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)

    if not (is_officer or is_chairman):
        messages.error(request, "Not authorized.")
        return redirect('/placement/')

    policies = PlacementPolicy.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'create':
            name = request.POST.get('name', '')
            description = request.POST.get('description', '')
            max_offers = int(request.POST.get('max_offers_allowed', 1))
            allow_dream = request.POST.get('allow_dream_company') == 'on'
            dream_threshold = request.POST.get('dream_ctc_threshold', 0)

            try:
                # Deactivate all existing policies first
                PlacementPolicy.objects.update(is_active=False)

                PlacementPolicy.objects.create(
                    name=name,
                    description=description,
                    max_offers_allowed=max_offers,
                    allow_dream_company=allow_dream,
                    dream_ctc_threshold=dream_threshold or 0,
                    is_active=True,
                )
                messages.success(request, "Policy '{}' created and activated.".format(name))
            except Exception as e:
                messages.error(request, "Failed to create policy: {}".format(str(e)))
        elif action == 'toggle':
            policy_id = request.POST.get('policy_id')
            try:
                policy = PlacementPolicy.objects.get(id=policy_id)
                if not policy.is_active:
                    PlacementPolicy.objects.update(is_active=False)
                    policy.is_active = True
                else:
                    policy.is_active = False
                policy.save()
                messages.success(request, "Policy '{}' updated.".format(policy.name))
            except PlacementPolicy.DoesNotExist:
                messages.error(request, "Policy not found.")

    context = {
        'policies': policies,
        'is_chairman': is_chairman,
        'is_officer': is_officer,
    }
    return render(request, 'placementModule/pcms/manage_policies.html', context)


# ---------- PCMS Dashboard / Hub ----------

@login_required
def pcms_dashboard(request):
    """Central PCMS dashboard combining all PCMS features."""
    user = request.user
    is_chairman, is_officer, is_student = _get_user_roles(user)
    profile = get_object_or_404(ExtraInfo, Q(user=user))

    context = {
        'is_chairman': is_chairman,
        'is_officer': is_officer,
        'is_student': is_student,
    }

    if is_student:
        try:
            student = Student.objects.get(id=profile)
            active_postings = JobPosting.objects.filter(is_active=True).count()
            my_apps = JobApplication.objects.filter(student=student).count()
            my_offers_count = JobOffer.objects.filter(
                application__student=student, status='PENDING'
            ).count()
            announcements = Announcement.objects.filter(is_active=True)[:5]

            context.update({
                'student': student,
                'active_postings': active_postings,
                'my_apps': my_apps,
                'my_offers_count': my_offers_count,
                'recent_announcements': announcements,
            })
        except Student.DoesNotExist:
            pass

    elif is_officer or is_chairman:
        total_companies = Company.objects.filter(approval_status='APPROVED').count()
        pending_companies = Company.objects.filter(approval_status='PENDING').count()
        active_postings = JobPosting.objects.filter(is_active=True).count()
        total_applications = JobApplication.objects.count()
        pending_offers = JobOffer.objects.filter(status='PENDING').count()
        accepted_offers = JobOffer.objects.filter(status='ACCEPTED').count()

        recent_applications = JobApplication.objects.select_related(
            'student__id__user', 'job_posting__company'
        ).order_by('-applied_at')[:10]

        context.update({
            'total_companies': total_companies,
            'pending_companies': pending_companies,
            'active_postings': active_postings,
            'total_applications': total_applications,
            'pending_offers': pending_offers,
            'accepted_offers': accepted_offers,
            'recent_applications': recent_applications,
        })

    return render(request, 'placementModule/pcms/dashboard.html', context)


