import os
import shutil
import zipfile
from cgi import escape
from datetime import date
from io import BytesIO
from wsgiref.util import FileWrapper

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template, render_to_string
from django.utils import timezone
from django.utils.encoding import smart_str
from xhtml2pdf import pisa

from applications.academic_information.models import Student
from applications.globals.models import (DepartmentInfo, ExtraInfo,
                                         HoldsDesignation)

from .forms import (AddAchievement, AddChairmanVisit, AddCourse, AddEducation,
                    AddExperience, AddPatent, AddProfile, AddProject,
                    AddPublication, AddSchedule, AddSkill, ManageHigherRecord,
                    ManagePbiRecord, ManagePlacementRecord, SearchHigherRecord,
                    SearchPbiRecord, SearchPlacementRecord,
                    SearchStudentRecord, SendInvite)
from .models import (Achievement, ChairmanVisit, Course, Education, Experience,
                     Has, NotifyStudent, Patent, PlacementRecord,
                     PlacementSchedule, PlacementStatus, Project, Publication,
                     Skill, StudentPlacement, StudentRecord)

# from weasyprint import HTML







@login_required
def placement(request):

    student_record_check = 0
    officer_manage = 0
    officer_manage_pbi = 0
    officer_statistics_past = 0
    officer_statistics_past_add = 0
    officer_statistics_past_pbi_search = 0
    officer_statistics_past_pbi_add = 0
    officer_statistics_past_higher_search = 0
    officer_statistics_past_higher_add = 0
    chairman_visit_add = 0
    invitecheck=0

    placementrecord = 1
    pbirecord = 1
    higherrecord = 1
    studentplacement = []
    page_range = ''
    paginator = ''
    is_disabled = 0
    no_pagination = 1

    if 'std' in cache:
        student_record_check= 1
        students = cache.get('std')
        total_query = students.count()
        print(total_query)
        # c = 1
        # while tq>20:
        #     tq=tq-60
        #     c = c + 1
        # print(c)

        if total_query > 30:
            paginator = Paginator(students, 30)
            page = request.GET.get('page', 1)
            students = paginator.page(page)
            print(paginator.num_pages)
            print(page)
            page = int(page)
            total_page = int(page + 3)
            #page_range = range(1,total_page)

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
        # print(contacts)
        # print(paginator.num_pages)
    else:
        students = ''

    user = request.user

    profile = get_object_or_404(ExtraInfo, Q(user=user))
    studentrecord = StudentRecord.objects.all()

    form5 = AddSchedule(initial={})

    # current = HoldsDesignation.objects.filter(Q(working=user, designation__name="student"))
    years = PlacementRecord.objects.filter(~Q(placement_type="HIGHER STUDIES")).values('year').annotate(Count('year'))
    records = PlacementRecord.objects.values('name', 'year', 'ctc', 'placement_type').annotate(Count('name'), Count('year'), Count('placement_type'), Count('ctc'))

    current1 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement chairman"))
    current2 = HoldsDesignation.objects.filter(Q(working=user, designation__name="placement officer"))
    schedules = PlacementSchedule.objects.all()


    invitecheck=0;
    if 'sendinvite' in request.POST:
        invitecheck=1;
        form13 = SendInvite(request.POST)
        if form13.is_valid():
            if form13.cleaned_data['company']:
                comp = form13.cleaned_data['company']
                com = [comp.company_name, comp.placement_type]
                notify = NotifyStudent.objects.get(company_name=com[0],
                                                   placement_type=com[1])
                if 'q' not in request.session:
                    stud = Student.objects.all()
                else:
                    q = request.session['q']
                    p = []
                    for w in q:
                        p.append(w['id_id'])
                        stud = Student.objects.filter(Q(id__in=p))
                for student in stud:
                    status = PlacementStatus.objects.create(notify_id=notify,
                                                            unique_id=student,
                                                            timestamp=timezone.now())
                    status.save()


    form1 = SearchStudentRecord(initial={})
    form = AddChairmanVisit(initial={})
    form2 = SearchPlacementRecord(initial={})
    form3 = SearchPbiRecord(initial={})
    form4 = SearchHigherRecord(initial={})
    form11 = ManagePlacementRecord(initial={})
    form9 = ManagePbiRecord(initial={})
    form10 = ManageHigherRecord(initial={})
    form13 = SendInvite(initial={})
    chairmanvisit = ChairmanVisit.objects.all()
    # notify = NotifyStudent.objects.all()
    # schedules = PlacementSchedule.objects.all()
    # studentplacement = StudentPlacement.objects.all()
    # placementstatus = PlacementStatus.objects.filter(Q(notify_id__in=notify)).order_by('-timestamp')
    context = {'user': user, 'form5':form5, 'form1': form1, 'form13': form13, 'form11': form11, 'form9': form9,
               'schedules':schedules,'studentrecord':studentrecord, 'form2': form2, 'form3':form3,
                'form4': form4, 'years': years, 'records': records, 'page_range': page_range, 'paginator': paginator,
               'placementrecord':placementrecord, 'higherrecord':higherrecord, 'students': students,
               'pbirecord':pbirecord, 'current1':current1, 'invitecheck':invitecheck, 'profile': profile,
               'current2':current2, 'student_record_check': student_record_check, 'is_disabled': is_disabled,
               'officer_manage': officer_manage, 'officer_manage_pbi': officer_manage_pbi,
               'officer_statistics_past': officer_statistics_past, 'officer_statistics_past_add': officer_statistics_past_add,
               'officer_statistics_past_pbi_search': officer_statistics_past_pbi_search, 'officer_statistics_past_pbi_add':
               officer_statistics_past_pbi_add, 'officer_statistics_past_higher_add': officer_statistics_past_higher_add,
               'officer_statistics_past_higher_search': officer_statistics_past_higher_search,
               'chairman_visit_add': chairman_visit_add, 'no_pagination': no_pagination
    }
    print('heer')
    return render(request, "placementModule/placement.html", context)




def ScheduleSubmit(request):
    print('\n\n coming--add schedule\n\n')
    # add company schedule
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
            description = form5.cleaned_data['description']
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
                                                        location=location, time=time)
            notify.save()
            schedule.save()

    # delete company schedule
    else:
        # print('not in schedulesubmit \n\n')
        if 'delete_sch_key' in request.POST:
            # print("\n\n--delete schedule key "request.POST['delete_sch_key'])
            delete_sch_key = request.POST['delete_sch_key']
            try:
                PlacementSchedule.objects.get(pk = delete_sch_key).delete()
                NotifyStudent.objects.get(pk = delete_sch_key).delete()
            except Exception as e:
                print('---- \n\n record not found')

    return redirect('/placement/')


def SearchRecord(request):

    if 'recordsubmit' in request.POST:
        print('search')
        student_record_check = 1
        form1 = SearchStudentRecord(request.POST)
        if form1.is_valid():
            print('valid')
            if form1.cleaned_data['name']:
                name = form1.cleaned_data['name']
            else:
                name = ''
            if form1.cleaned_data['rollno']:
                rollno = form1.cleaned_data['rollno']
            else:
                rollno = ''
            programme = form1.cleaned_data['programme']
            if form1.cleaned_data['department']:
                department = form1.cleaned_data['department']
            else:
                department = ''
            if form1.cleaned_data['cpi']:
                cpi = form1.cleaned_data['cpi']
            else:
                cpi = 0
            debar = form1.cleaned_data['debar']
            placed_type = form1.cleaned_data['placed_type']

            students = Student.objects.filter(Q(id__in=ExtraInfo.objects.filter(Q(user__in=User.objects.filter(Q(first_name__icontains=name)),
                department__in=DepartmentInfo.objects.filter(Q(name__icontains=department)),
                id__icontains=rollno)),
                programme=programme,
                cpi__gte=cpi)).filter(Q(pk__in=StudentPlacement.objects.filter(Q(debar=debar, placed_type=placed_type)).values('unique_id_id'))).order_by('id')

            st = students

            cache.set('std', students)

            return redirect('/placement/')



def html_to_pdf_view(request):
    students = cache.get('std')
    #paragraphs = ['first paragraph', 'second paragraph', 'third paragraph']
    context = {
        'students': students,
    }
    template = get_template('placementModule/pdf_demo.html')
    html = template.render(context)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse('We had some errors<pre>%s</pre>' % escape(html))



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
