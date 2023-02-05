import datetime
import json
import os
import xlrd
import logging
from io import BytesIO
from xlsxwriter.workbook import Workbook
from xhtml2pdf import pisa

from itertools import chain

from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required

from applications.academic_procedures.models import MinimumCredits, Register, InitialRegistration, course_registration, AssistantshipClaim,Assistantship_status
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation, DepartmentInfo)

from .forms import AcademicTimetableForm, ExamTimetableForm, MinuteForm
from .models import (Calendar, Course, Exam_timetable, Grades, Curriculum_Instructor,Constants,
                     Meeting, Student, Student_attendance, Timetable,Curriculum)
from applications.programme_curriculum.models import (CourseSlot, Course as Courses, Batch, Semester, Programme, Discipline)                     



from applications.academic_procedures.views import acad_proced_global_context
from applications.programme_curriculum.models import Batch



@login_required
def user_check(request):
    """
    This function is used to check the type of user.
    It checkes the authentication of the user.

    @param:
        request - contains metadata about the requested page

    @variables:
        current_user - get user from request 
        user_details - extract details of user from database
        desig_id - check for designation
        acadadmin - designation for Acadadmin
        final_user - final designation of request user

    """
    try:
        current_user = get_object_or_404(User, username=request.user.username)
        user_details = ExtraInfo.objects.all().select_related('user','department').filter(user=current_user).first()
        desig_id = Designation.objects.all().filter(name='Upper Division Clerk')
        temp = HoldsDesignation.objects.all().select_related().filter(designation = desig_id).first()
        acadadmin = temp.working
        k = str(user_details).split()
        final_user = k[2]
    except Exception as e:
        acadadmin=""
        final_user=""
        pass

    if (str(acadadmin) != str(final_user)):
        return True
    else:
        return False


def get_context(request):
    """
    This function gets basic gata from database to send to template

    @param:
        request - contains metadata about the requested page

    @variables:
        acadTtForm - the form to add academic calender
        examTtForm - the form required to add exam timetable
        exam_t - all the exam timetable objects
        timetable - all the academic timetable objects
        calendar - all the academic calender objects
        context - the datas to be displayed in the webpage
        this_sem_course - tha data of thsi semester courses
        next_sem_courses - the data of next semester courses
        courses - all the courses in curriculum
        course_type - list the type of courses

    """
    if user_check(request):
        return HttpResponseRedirect('/academic-procedures/')

    course_list = sem_for_generate_sheet()
    if(course_list[0]==1):
        course_list_2 = [2, 4, 6, 8]
    else:
        course_list_2 = [1, 3, 5, 7]

    # examTtForm = ExamTimetableForm()
    # acadTtForm = AcademicTimetableForm()
    # calendar = Calendar.objects.all()    
    # this_sem_courses = Curriculum.objects.all().filter(sem__in=course_list).filter(floated=True)
    # next_sem_courses = Curriculum.objects.all().filter(sem__in=course_list).filter(floated=True)
    # courses = Course.objects.all()
    # course_type = Constants.COURSE_TYPE
    # timetable = Timetable.objects.all()
    # exam_t = Exam_timetable.objects.all()

    procedures_context = acad_proced_global_context()

    try:
        examTtForm = ExamTimetableForm()
        acadTtForm = AcademicTimetableForm()
        calendar = Calendar.objects.all()
        this_sem_courses = Curriculum.objects.all().select_related().filter(sem__in=course_list).filter(floated=True)
        next_sem_courses = Curriculum.objects.all().select_related().filter(sem__in=course_list_2).filter(floated=True)
        courses = Course.objects.all()
        courses_list = Courses.objects.all()
        course_type = Constants.COURSE_TYPE
        timetable = Timetable.objects.all()
        exam_t = Exam_timetable.objects.all()
        pgstudent = Student.objects.filter(programme = "M.Tech") | Student.objects.filter(programme = "PhD")
        assistant_list = AssistantshipClaim.objects.filter(ta_supervisor_remark = True).filter(thesis_supervisor_remark = True).filter(hod_approval =True).filter(acad_approval = False)
        assistant_approve_list = AssistantshipClaim.objects.filter(ta_supervisor_remark = True).filter(thesis_supervisor_remark = True).filter(hod_approval =True).filter(hod_approval = True)
        assistant_list_length = len(assistant_list.filter(acad_approval = False))
        assis_stat = Assistantship_status.objects.all()
        assistant_flag =""
        hod_flag = ""
        account_flag = ""

        for obj in assis_stat:
            assistant_flag = obj.student_status
            hod_flag = obj.hod_status
            account_flag = obj.account_status
            
    except Exception as e:
        examTtForm = ""
        acadTtForm = ""
        calendar = ""
        this_sem_courses = ""
        next_sem_courses = ""
        courses = ""
        course_type = ""
        timetable = ""
        exam_t = ""
        pass

    context = {
        'acadTtForm': acadTtForm,
        'examTtForm': examTtForm,
        'courses': courses,
        'courses_list': courses_list,
        'course_type': course_type,
        'exam': exam_t,
        'timetable': timetable,
        'academic_calendar': calendar,
        'next_sem_course': next_sem_courses,
        'this_sem_course': this_sem_courses,
        'curriculum': curriculum,
        'pgstudent' : pgstudent,
        'assistant_list' : assistant_list,
        'assistant_approve_list' : assistant_approve_list,
        'assistant_list_length' : assistant_list_length,
        'tab_id': ['1','1'],
        'context': procedures_context['context'],
        'lists': procedures_context['lists'],
        'date': procedures_context['date'],
        'query_option1': procedures_context['query_option1'],
        'query_option2': procedures_context['query_option2'],
        'course_verification_date' : procedures_context['course_verification_date'],
        'submitted_course_list' : procedures_context['submitted_course_list'],
        'result_year' : procedures_context['result_year'],
        'batch_grade_data' : procedures_context['batch_grade_data'],
        'batch_branch_data' : procedures_context['batch_branch_data'],
        'assistant_flag' : assistant_flag,
        'hod_flag' : hod_flag,
        'account_flag' : account_flag
    }

    return context


@login_required
def homepage(request):
    """
    This function is used to set up the homepage of the application.
    It checkes the authentication of the user and also fetches the available
    data from the databases to display it on the page.

    @param:
        request - contains metadata about the requested page

    @variables:
        senates - the extraInfo objects that holds the designation as a senator
        students - all the objects in the Student class
        Convenor - the extraInfo objects that holds the designation as a convenor
        CoConvenor - the extraInfo objects that holds the designation as a coconvenor
        meetings - the all meeting objects held in senator meetings
        minuteForm - the form to add a senate meeting minutes
        acadTtForm - the form to add academic calender
        examTtForm - the form required to add exam timetable
        Dean - the extraInfo objects that holds the designation as a dean
        student - the students as a senator
        extra - all the extraInfor objects
        exam_t - all the exam timetable objects
        timetable - all the academic timetable objects
        calendar - all the academic calender objects
        department - all the departments in the college
        attendance - all the attendance objects of the students
        context - the datas to be displayed in the webpage

    """
    if user_check(request):
        return HttpResponseRedirect('/academic-procedures/')

    context = get_context(request)

    return render(request, "ais/ais.html", context)



# ####################################
# #         curriculum               #
# ####################################


@login_required
def curriculum(request):
    """
    This function is used to see curriculum and edit entries in a curriculum.
    It checkes the authentication of the user and also fetches the available
    data from the databases to display it on the page.

    @param:
        request - contains metadata about the requested page

    @variables:
        request_batch - Batch from form 
        request_branch - Branch from form
        request_programme - Programme from form
        request_sem - Semester from form
        curriculum - Get data about curriculum from database
        courses - get courses from database
        courses_type - get course types from database

    """

    if user_check(request):
        return HttpResponseRedirect('/academic-procedures/')
    
    context = get_context(request)
    context['tab_id'][0]='6'

    if request.method == 'POST':
        try:
            request_batch = request.POST['batch']
            request_branch = request.POST['branch']
            request_programme = request.POST['programme']
            request_sem = request.POST['sem']
        except Exception as e:
            request_batch = ""
            request_branch = ""
            request_programme = ""
            request_sem = ""
        #for checking if the user has searched for any particular curriculum
        if request_batch == "" and request_branch == "" and request_programme=="" and request_sem=="":
            curriculum = None   #Curriculum.objects.all()
        else:
            if int(request_sem) == 0:
                curriculum = Curriculum.objects.select_related().filter(branch = request_branch).filter(batch = request_batch).filter(programme= request_programme).order_by('sem')
            else:
                curriculum = Curriculum.objects.select_related().filter(branch = request_branch).filter(batch = request_batch).filter(programme= request_programme).filter(sem= request_sem)
        # context={
        #     'courses' : courses,
        #     'course_type' : course_type,
        #     'curriculum' : curriculum,
        #     'tab_id' :['3','1']
        # }
        courses = Course.objects.all()
        course_type = Constants.COURSE_TYPE
        html = render_to_string('ais/curr_list.html',{'curriculum':curriculum,'courses':courses,'course_type':course_type},request)
        obj = json.dumps({'html':html})
        #return render(request, "ais/ais.html", context)
        return HttpResponse(obj,content_type='application/json')
    else:
        return render(request, "ais/ais.html", context)


@login_required
def add_curriculum(request):
    """
    This function is used to add new curriculum in database
    It checkes the authentication of the user and also fetches the available
    data from the databases to display it on the page.

    @param:
        request - contains metadata about the requested page

    @variables:
        programme - programme from form.REQUEST
        batch - batch from form.REQUEST
        branch - branch from form.REQUEST
        sem - semester from form.REQUEST
        course_code - course_code from form.REQUEST
        course_name - course-name from form.REQUEST
        course_id - course_id from database
        credits - credits from form.REQUEST
        optional - optional from form.REQUEST
        course_type - course_type from form.REQUEST
        ins - data is stored in database

    """

    if user_check(request):
        return HttpResponseRedirect('/academic-procedures/')

    context={
            'tab_id' :['3','2']
        }
    if request.method == 'POST':
        i=0
        new_curr=[]
        while True:
            if "semester_"+str(i) in request.POST:
                try:
                    programme=request.POST['AddProgramme']
                    batch=request.POST['AddBatch']
                    branch=request.POST['AddBranch']
                    sem=request.POST["semester_"+str(i)]
                    course_code=request.POST["course_code_"+str(i)]
                    course_name=request.POST["course_name_"+str(i)]
                    course_id=Course.objects.get(course_name=course_name)
                    credits=request.POST["credits_"+str(i)]
                    if "optional_"+str(i) in request.POST:
                        optional=True
                    else:
                        optional=False
                    course_type=request.POST["course_type_"+str(i)]
                except Exception as e:
                    programme=""
                    batch=""
                    branch=""
                    sem=""
                    course_code=""
                    course_name=""
                    course_id=""
                    credits=""
                    optional=""
                    course_type=""
                    pass
                ins=Curriculum(
                    programme=programme,
                    batch=batch,
                    branch=branch,
                    sem=sem,
                    course_code=course_code,
                    course_id=course_id,
                    credits=credits,
                    optional=optional,
                    course_type=course_type,
                )
                new_curr.append(ins)
            else:
                break
            i+=1
        Curriculum.objects.bulk_create(new_curr)
        curriculum = Curriculum.objects.select_related().filter(branch = branch).filter(batch = batch).filter(programme= programme)
        courses = Course.objects.all()
        course_type = Constants.COURSE_TYPE
        context= {
            'courses': courses,
            'course_type': course_type,
            'curriculum': curriculum,
            'tab_id' :['3','2']
        }
        return render(request, "ais/ais.html", context)
    else:
        return render(request, "ais/ais.html", context)


@login_required
def edit_curriculum(request):
    """
    This function is used to edit curriculum in database
    It checkes the authentication of the user and also fetches the available
    data from the databases to display it on the page.

    @param:
        request - contains metadata about the requested page

    @variables:
        programme - programme from form.REQUEST
        batch - batch from form.REQUEST
        branch - branch from form.REQUEST
        sem - semester from form.REQUEST
        course_code - course_code from form.REQUEST
        course_name - course-name from form.REQUEST
        course_id - course_id from database
        credits - credits from form.REQUEST
        optional - optional from form.REQUEST
        course_type - course_type from form.REQUEST
        ins - data is stored in database

    """
    if user_check(request):
        return HttpResponseRedirect('/academic-procedures/')
        
    context={
            'tab_id' :['3','1']
        }
    if request.method == 'POST':
        try:
            id=request.POST['id']
            programme=request.POST['programme']
            batch=request.POST['batch']
            branch=request.POST['branch']
            sem=request.POST["sem"]
            course_code=request.POST["course_code"]
            course_name=request.POST["course_id"]
            course_id=Course.objects.get(course_name=course_name)
            credits=request.POST["credits"]
            if request.POST['optional'] == "on":
                optional=True
            else:
                optional=False
            course_type=request.POST["course_type"]
        except Exception as e:
            id=""
            programme=""
            batch=""
            branch=""
            sem=""
            course_code=""
            course_name=""
            course_id=""
            credits=""
            optional=""
            course_type=""
            pass

        entry=Curriculum.objects.all().select_related().filter(curriculum_id=id).first()
        entry.programme=programme
        entry.batch=batch
        entry.branch=branch
        entry.sem=sem
        entry.course_code=course_code
        entry.course_id=course_id
        entry.credits=credits
        entry.optional=optional
        entry.course_type=course_type
        entry.save()
        curriculum = Curriculum.objects.select_related().filter(branch = branch).filter(batch = batch).filter(programme= programme)
        courses = Course.objects.all()
        course_type = Constants.COURSE_TYPE
        context= {
            'courses': courses,
            'course_type': course_type,
            'curriculum': curriculum,
            'tab_id' :['3','1']
        }
        return render(request, "ais/ais.html", context)
    else:
        return render(request, "ais/ais.html", context)


@login_required
def delete_curriculum(request):
    """
    This function is used to delete curriculum entry in database
    It checkes the authentication of the user and also fetches the available
    data from the databases to display it on the page.

    @param:
        request - contains metadata about the requested page

    @variables:
        dele - data being deleted from database

    """
    if user_check(request):
        return HttpResponseRedirect('/academic-procedures/')
        
    context={
            'tab_id' :['3','1']
        }
    if request.method == "POST":
        dele = Curriculum.objects.select_related().filter(curriculum_id=request.POST['id'])
        dele.delete()
        curriculum = Curriculum.objects.select_related().filter(branch = request.POST['branch']).filter(batch = request.POST['batch']).filter(programme= request.POST['programme'])
        courses = Course.objects.all()
        course_type = Constants.COURSE_TYPE
        context= {
            'courses': courses,
            'course_type': course_type,
            'curriculum': curriculum,
            'tab_id' :['3','1']
        }
        return render(request, "ais/ais.html", context)
    return render(request, 'ais/ais.html', context)


@login_required
def next_curriculum(request):
    """
    This function is used to decide curriculum for new batch.
    It checkes the authentication of the user and also fetches the available
    data from the databases to display it on the page.

    @param:
        request - contains metadata about the requested page

    @variables:
        programme - programme from form.REQUEST
        now - current date from system
        year - current year
        batch - batch form form
        curriculum - curriculum details form database
        ins - Inster data in database

    """
    if user_check(request):
        return HttpResponseRedirect('/academic-procedures/')
        
    if request.method == 'POST':
        programme = request.POST['programme']
        now = datetime.datetime.now()
        year = int(now.year)
        batch = year-1
        curriculum = Curriculum.objects.all().select_related().filter(batch = batch).filter(programme = programme)
        if request.POST['option'] == '1':
            new_curriculum=[]
            for i in curriculum:
                ins=Curriculum(
                    programme=i.programme,
                    batch=i.batch+1,
                    branch=i.branch,
                    sem=i.sem,
                    course_code=i.course_code,
                    course_id=i.course_id,
                    credits=i.credits,
                    optional=i.optional,
                    course_type=i.course_type,
                )
                new_curriculum.append(ins)
            try:
                Curriculum.objects.bulk_create(new_curriculum)
            except Exception as e:
                print("Exception occured",e)
            

        elif request.POST['option'] == '2':
            new_curriculum=[]
            for i in curriculum:
                ins=Curriculum(
                    programme=i.programme,
                    batch=i.batch+1,
                    branch=i.branch,
                    sem=i.sem,
                    course_code=i.course_code,
                    course_id=i.course_id,
                    credits=i.credits,
                    optional=i.optional,
                    course_type=i.course_type,
                )
                new_curriculum.append(ins)
            try:
                Curriculum.objects.bulk_create(new_curriculum)
            except Exception as e:
                print("Exception occured!",e)
            finally:
                batch=batch+1
                curriculum = Curriculum.objects.all().select_related().filter(batch = batch).filter(programme = programme)
                context= {
                    'curriculumm' :curriculum,
                    'tab_id' :['3','3']
                }
                return render(request, "ais/ais.html", context)
        else:
            context= {
            'tab_id' :['3','2']
            }
            return render(request, "ais/ais.html", context)
    context= {
    'tab_id' :['3','1']
    }
    return render(request, "ais/ais.html", context)


@login_required
def add_timetable(request):
    """
    acad-admin can upload the time table(any type of) of the semester.

    @param:
        request - contains metadata about the requested page.

    @variables:
        acadTtForm - data of delete dictionary in post request
        timetable - all timetable from database
        exam_t - all exam timetable from database
    """
    if user_check(request):
        return HttpResponseRedirect('/academic-procedures/')
    timetable = Timetable.objects.all()
    exam_t = Exam_timetable.objects.all()
    context= {
        'exam': exam_t,
        'timetable': timetable,
        'tab_id' :['10','1']
    }
    acadTtForm = AcademicTimetableForm()
    if request.method == 'POST' and request.FILES:
        acadTtForm = AcademicTimetableForm(request.POST, request.FILES)
        if acadTtForm.is_valid():
             acadTtForm.save()
        return render(request, "ais/ais.html", context)
    else:
        return render(request, "ais/ais.html", context)


@login_required
def add_exam_timetable(request):
    """
    acad-admin can upload the exam timtable of the ongoing semester.

    @param:
        request - contains metadata about the requested page.

    @variables:
        examTtForm - data of delete dictionary in post request
        timetable - all timetable from database
        exam_t - all exam timetable from database
    """
    if user_check(request):
        return HttpResponseRedirect('/academic-procedures/')
        
    timetable = Timetable.objects.all()
    exam_t = Exam_timetable.objects.all()
    context= {
        'exam': exam_t,
        'timetable': timetable,
        'tab_id' :['10','2']
    }
    examTtForm = ExamTimetableForm()
    if request.method == 'POST' and request.FILES:
        examTtForm = ExamTimetableForm(request.POST, request.FILES)
        if examTtForm.is_valid():
            examTtForm.save()
        return render(request, "ais/ais.html", context)
    else:
        return render(request, "ais/ais.html", context)
    return render(request, "ais/ais.html", context)


@login_required
def delete_timetable(request):
    """
    acad-admin can delete the outdated timetable from the server.

    @param:
        request - contains metadata about the requested page.

    @variables:
        data - data of delete dictionary in post request
        t - Object of time table to be deleted
    """
    if user_check(request):
        return HttpResponseRedirect('/academic-procedures/')
        
    if request.method == "POST":
        data = request.POST['delete']
        t = Timetable.objects.get(time_table=data)
        t.delete()
        return HttpResponse("TimeTable Deleted")


@login_required
def delete_exam_timetable(request):
    """
    acad-admin can delete the outdated exam timetable.

    @param:
        request - contains metadata about the requested page.

    @variables:
        data - data of delete dictionary in post request
        t - Object of Exam time table to be deleted
    """
    if user_check(request):
        return HttpResponseRedirect('/academic-procedures/')
        
    if request.method == "POST":
        data = request.POST['delete']
        t = Exam_timetable.objects.get(exam_time_table=data)
        t.delete()
        return HttpResponse("TimeTable Deleted")


@login_required
def add_calendar(request):
    """
    to add an entry to the academic calendar to be uploaded

    @param:
        request - contains metadata about the requested page.

    @variables:
        from_date - The starting date for the academic calendar event.
        to_date - The ending date for the academic caldendar event.
        desc - Description for the academic calendar event.
        c = object to save new event to the academic calendar.
    """
    if user_check(request):
        return HttpResponseRedirect('/academic-procedures/')
        
    calendar = Calendar.objects.all()
    context= {
        'academic_calendar' :calendar,
        'tab_id' :['4','1']
    }
    if request.method == "POST":
        try:
            from_date = request.POST.getlist('from_date')
            to_date = request.POST.getlist('to_date')
            desc = request.POST.getlist('description')[0]
            from_date = from_date[0].split('-')
            from_date = [int(i) for i in from_date]
            from_date = datetime.datetime(*from_date).date()
            to_date = to_date[0].split('-')
            to_date = [int(i) for i in to_date]
            to_date = datetime.datetime(*to_date).date()
        except Exception as e:
            from_date=""
            to_date=""
            desc=""
            pass
        c = Calendar(
            from_date=from_date,
            to_date=to_date,
            description=desc)
        c.save()
        HttpResponse("Calendar Added")

    return render(request, "ais/ais.html", context)


@login_required
def update_calendar(request):
    """
    to update an entry to the academic calendar to be updated.

    @param:
        request - contains metadata about the requested page.

    @variables:
        from_date - The starting date for the academic calendar event.
        to_date - The ending date for the academic caldendar event.
        desc - Description for the academic calendar event.
        prev_desc - Description for the previous event which is to be updated.
        get_calendar_details = Get the object of the calendar instance from the database for the previous Description.

    """
    if user_check(request):
        return HttpResponseRedirect('/academic-procedures/')
        
    calendar = Calendar.objects.all()
    context= {
        'academic_calendar' :calendar,
        'tab_id' :['4','1']
    }
    if request.method == "POST":
        try:
            from_date = request.POST.getlist('from_date')
            to_date = request.POST.getlist('to_date')
            desc = request.POST.getlist('description')[0]
            prev_desc = request.POST.getlist('prev_desc')[0]
            from_date = from_date[0].split('-')
            from_date = [int(i) for i in from_date]
            from_date = datetime.datetime(*from_date).date()
            to_date = to_date[0].split('-')
            to_date = [int(i) for i in to_date]
            to_date = datetime.datetime(*to_date).date()
            get_calendar_details = Calendar.objects.all().filter(description=prev_desc).first()
            get_calendar_details.description = desc
            get_calendar_details.from_date = from_date
            get_calendar_details.to_date = to_date
            get_calendar_details.save()
        except Exception as e:
            from_date=""
            to_date=""
            desc=""
        return render(request, "ais/ais.html", context)
    return render(request, "ais/ais.html", context)


#Generate Attendance Sheet
def sem_for_generate_sheet():
    """
    This function generates semester grade sheet
    @variables:
        now - current datetime
        month - current month
    """

    now = datetime.datetime.now()
    month = int(now.month)
    if month >= 7 and month <= 12:
        return [1, 3, 5, 7]
    else:
        return [2, 4, 6, 8]


@login_required
def generatexlsheet(request):
    """
    to generate Course List of Registered Students

    @param:
        request - contains metadata about the requested page

    @variables:
        batch - gets the batch
        course - gets the course
        curr_key - gets the curriculum from database
        obj - get stdents data from database
        ans - Formatted Array to be converted to xlsx
        k -temporary array to add data to formatted array/variable
        output - io Bytes object to write to xlsx file
        book - workbook of xlsx file
        title - formatting variable of title the workbook
        subtitle - formatting variable of subtitle the workbook
        normaltext - formatting variable for normal text
        sheet - xlsx sheet to be rendered
        titletext - formatting variable of title text
        dep - temporary variables
        z - temporary variables for final output
        b - temporary variables for final output
        c - temporary variables for final output
        st - temporary variables for final output
    """
    if user_check(request):
        return HttpResponseRedirect('/academic-procedures/')
    
    try:
        batch = request.POST['batch']
        course = Courses.objects.get(id = request.POST['course'])
        obj = course_registration.objects.all().filter(course_id = course)
    except Exception as e:
        batch=""
        course=""
        curr_key=""
        obj=""

    registered_courses = []
    for i in obj:
        if i.student_id.batch_id.year == int(batch):
            registered_courses.append(i)
    ans = []
    for i in registered_courses:
        k = []
        k.append(i.student_id.id.id)
        k.append(i.student_id.id.user.first_name)
        k.append(i.student_id.id.user.last_name)
        k.append(i.student_id.id.department)
        ans.append(k)
    ans.sort()
    output = BytesIO()

    book = Workbook(output,{'in_memory':True})
    title = book.add_format({'bold': True,
                                'font_size': 22,
                                'align': 'center',
                                'valign': 'vcenter'})
    subtitle = book.add_format({'bold': True,
                                'font_size': 15,
                                'align': 'center',
                                'valign': 'vcenter'})
    normaltext = book.add_format({'bold': False,
                                'font_size': 15,
                                'align': 'center',
                                'valign': 'vcenter'})
    sheet = book.add_worksheet()

    title_text = ((str(course.name)+" : "+str(str(batch))))
    sheet.set_default_row(25)

    sheet.merge_range('A2:E2', title_text, title)
    sheet.write_string('A3',"Sl. No",subtitle)
    sheet.write_string('B3',"Roll No",subtitle)
    sheet.write_string('C3',"Name",subtitle)
    sheet.write_string('D3',"Discipline",subtitle)
    sheet.write_string('E3','Signature',subtitle)
    sheet.set_column('A:A',20)
    sheet.set_column('B:B',20)
    sheet.set_column('C:C',60)
    sheet.set_column('D:D',15)
    sheet.set_column('E:E',30)
    k = 4
    num = 1
    for i in ans:
        sheet.write_number('A'+str(k),num,normaltext)
        num+=1
        z,b,c = str(i[0]),i[1],i[2]
        name = str(b)+" "+str(c)
        temp = str(i[3]).split()
        dep = str(temp[len(temp)-1])
        sheet.write_string('B'+str(k),z,normaltext)
        sheet.write_string('C'+str(k),name,normaltext)
        sheet.write_string('D'+str(k),dep,normaltext)
        k+=1
    book.close()
    output.seek(0)
    response = HttpResponse(output.read(),content_type = 'application/vnd.ms-excel')
    st = 'attachment; filename = ' + course.code + '.xlsx'
    response['Content-Disposition'] = st
    return response


@login_required
def generate_preregistration_report(request):
    """
    to generate preresgistration report after pre-registration

    @param:
        request - contains metadata about the requested page

    @variables:
        sem - get current semester from current time
        now - get current time
        year - getcurrent year
        batch - gets the batch from form
        sem - stores the next semester
        obj - All the registration details appended into one
        data - Formated data for context
        m - counter for Sl. No (in formated data)
        z - temporary array to add data to variable data
        k -temporary array to add data to formatted array/variable
        output - io Bytes object to write to xlsx file
        book - workbook of xlsx file
        title - formatting variable of title the workbook
        subtitle - formatting variable of subtitle the workbook
        normaltext - formatting variable for normal text
        sheet - xlsx sheet to be rendered
        titletext - formatting variable of title text
        dep - temporary variables
        z - temporary variables for final output
        b - temporary variables for final output
        c - temporary variables for final output
        st - temporary variables for final output

    """
    if user_check(request):
        return HttpResponseRedirect('/academic-procedures/')
        
    if request.method == "POST":
        sem = request.POST.get('semester_no')
        batch_id=request.POST.get('batch_branch')
        batch = Batch.objects.filter(id = batch_id).first()
        obj = InitialRegistration.objects.filter(student_id__batch_id=batch_id, semester_id__semester_no=sem)



        registered_students = set()
        unregistered_students = set()

        # registered students contains objects of type InitialRegistration
        for stu in obj:
            registered_students.add(stu.student_id)

        students = Student.objects.filter(batch_id = batch_id)

        for stu in students:
            if stu not in registered_students:
                unregistered_students.add(stu)
        

        # for stu in obj:
        #     registered_students.add(stu.student_id)
        # students = Student.objects.filter(batch_id = batch_id)
        # for stu in students:
        #     if stu not in registered_students:
        #         unregistered_students.add(stu)



        data = []
        m = 1
        for i in unregistered_students:
            # z is a row in excel
            z = []
            z.append(m)
            m += 1
            z.append(i.id.user.username)
            z.append(str(i.id.user.first_name)+" "+str(i.id.user.last_name))
            z.append(i.id.department.name)
            z.append('Not Registered')
            data.append(z)

        sem_id = Semester.objects.get(curriculum = batch.curriculum, semester_no = sem)
        course_slots = CourseSlot.objects.all().filter(semester = sem_id)
        max_width = 1
        for student in registered_students:
            #z = []
            # z.append(m)
            # m += 1
            # z.append(i.id.user.username)
            # z.append(str(i.id.user.first_name)+" "+str(i.id.user.last_name))
            # z.append(i.id.department.name)
            # z.append('Registered')
            # data.append(z)
            current_student_registered_courses = InitialRegistration.objects.filter(student_id=student, semester_id__semester_no=sem).all()
            timestamp = current_student_registered_courses.first().timestamp
            #print("current student is ",student.id.user.username)
            #print("timstamp value ",timestamp)
            for slot in course_slots:
                #print("current slot belongs to ",slot)
                z = []
                z.append(m)
                z.append(student.id.user.username)
                z.append(str(student.id.user.first_name)+" "+str(student.id.user.last_name))
                z.append(student.id.department.name)
                z.append('Registered')
                z.append(str(timestamp))
                z.append(str(slot.name))
                
                choices_of_current_student = InitialRegistration.objects.filter(student_id=student, semester_id__semester_no=sem,course_slot_id = slot).all()
                max_width = max(max_width,len(choices_of_current_student))

                for choice in range(1,len(choices_of_current_student)+1):
                    current_choice = InitialRegistration.objects.get(student_id=student, semester_id__semester_no=sem,course_slot_id = slot,priority = choice)
                    # #print("current choice is ",current_choice)
                    z.append(str(current_choice.course_id.code)+"-"+str(current_choice.course_id.name))
                
                data.append(z)
                m+=1
        output = BytesIO()

        book = Workbook(output,{'in_memory':True})
        title = book.add_format({'bold': True,
                                    'font_size': 22,
                                    'align': 'center',
                                    'valign': 'vcenter'})
        subtitle = book.add_format({'bold': True,
                                    'font_size': 15,
                                    'align': 'center',
                                    'valign': 'vcenter'})
        normaltext = book.add_format({'bold': False,
                                    'font_size': 15,
                                    'align': 'center',
                                    'valign': 'vcenter'})
        sheet = book.add_worksheet()

        # add semester too in title text
        title_text = ("Pre-registeration : "+ batch.name + str(" ") + batch.discipline.acronym + str(" ") + str(batch.year) + " Semester : "+str(sem))
        # ??
        sheet.set_default_row(25)
        characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        # text, formatting
        sheet.merge_range('A2:E2', title_text, title)
        sheet.write_string('A3',"Sl. No",subtitle)
        sheet.write_string('B3',"Roll No",subtitle)
        sheet.write_string('C3',"Name",subtitle)
        sheet.write_string('D3',"Discipline",subtitle)
        sheet.write_string('E3','Status',subtitle)
        sheet.write_string('F3','TimeStamp',subtitle)
        sheet.write_string('G3','Course Slot ID',subtitle)
        for choice_num  in range(7,7+max_width):
            sheet.write_string(characters[choice_num]+'3','Choice '+str(choice_num-6),subtitle)

        
        # Width of column
        sheet.set_column('A:A',20)
        sheet.set_column('B:B',20)
        sheet.set_column('C:C',50)
        sheet.set_column('D:D',15)
        sheet.set_column('E:E',20)
        sheet.set_column('F:F',40)
        sheet.set_column('G:G',30)
        sheet.set_column('H:H',70)
        sheet.set_column('I:I',70)
        sheet.set_column('J:J',70)
        sheet.set_column('K:K',70)
        sheet.set_column('L:L',70)
        sheet.set_column('M:M',70)
        #rows numbers
        k = 4
        # SERIAL numbers S.no 1,2,3...
        num = 1
        for i in data:
            sheet.write_number('A'+str(k),num,normaltext)
            num+=1
            z,b,c = str(i[0]),i[1],i[2]
            if(len(i) > 5):
                a,b,c,d,e,f,g = str(i[0]),str(i[1]),str(i[2]),str(i[3]),str(i[4]),str(i[5]),str(i[6])
                temp = str(i[3]).split()
                sheet.write_string('B'+str(k),b,normaltext)
                sheet.write_string('C'+str(k),c,normaltext)
                sheet.write_string('D'+str(k),d,normaltext)
                sheet.write_string('E'+str(k),e,normaltext)
                sheet.write_string('F'+str(k),f,normaltext)
                sheet.write_string('G'+str(k),g,normaltext)
                characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                # for character in characters
                for temp_num in range(7,len(i)):
                    sheet.write_string(characters[temp_num]+str(k),str(i[temp_num]),normaltext)
            else:
                a,b,c,d,e= str(i[0]),str(i[1]),str(i[2]),str(i[3]),str(i[4])
                temp = str(i[3]).split()
                sheet.write_string('B'+str(k),b,normaltext)
                sheet.write_string('C'+str(k),c,normaltext)
                sheet.write_string('D'+str(k),d,normaltext)
                sheet.write_string('E'+str(k),e,normaltext)

            k+=1
        book.close()
        # ?? 
        output.seek(0)
        response = HttpResponse(output.read(),content_type = 'application/vnd.ms-excel')
        st = 'attachment; filename = ' + batch.name + batch.discipline.acronym + str(batch.year) + '-preresgistration.xlsx'
        response['Content-Disposition'] = st
        return response


@login_required
def add_new_profile (request):
    """
    To add details of new upcoming students in the database.User must be logged in and must be acadadmin

    @param:
        request - contains metadata about the requested page.

    @variables:
        profiles - gets the excel file having data
        excel - excel file
        sheet - sheet no in excel file
        roll_no - details of student from file
        first_name - details of student from file
        last_name - details of student from file
        email - details of student from file
        sex - details of student from file
        title - details of student from file
        dob - details of student from file
        fathers_name - details of student from file
        mothers_name - details of student from file
        category - details of student from file
        phone_no - details of student from file
        address - details of student from file
        department - details of student from file
        specialization - details of student from file
        hall_no - details of student from file
        programme - details of student from file
        batch - details of student from file
        user - new user created in database
        einfo - new extrainfo object created in database
        stud_data - new student object created in database
        desig - get designation object of student
        holds_desig - get hold_desig object of student
        currs - get curriculum details
        reg - create registeration object in registeration table

    """
    if user_check(request):
        return HttpResponseRedirect('/academic-procedures/')
        
    context= {
        'tab_id' :['2','1']
    }
    if request.method == 'POST' and request.FILES:
        profiles=request.FILES['profiles']
        excel = xlrd.open_workbook(file_contents=profiles.read())
        sheet=excel.sheet_by_index(0)
        for i in range(sheet.nrows):
            roll_no=sheet.cell(i,0).value
            first_name=str(sheet.cell(i,1).value)
            last_name=str(sheet.cell(i,2).value)
            email=roll_no+'@iiitdmj.ac.in'
            sex=str(sheet.cell(i,4).value)
            if sex == 'Female':
                title='Ms.'
                sex='F'
            else:
                title='Mr.'
                sex='M'
            #dob_tmp=sheet.cell(i,5).value
            #dob_tmp=sheet.cell_value(rowx=i,colx=5)
            dob=datetime.datetime.now()
            fathers_name=""
            mothers_name=""
            category=""
            phone_no=0
            address=""
            dept=str(sheet.cell(i,12).value)
            specialization=str(sheet.cell(i,12).value)
            hall_no=None

            department=DepartmentInfo.objects.all().filter(name=dept).first()

            if specialization == "":
                specialization="None"

            if hall_no == None:
                hall_no=3
            else:
                hall_no=int(hall_no)

            programme_name=request.POST['Programme']
            batch_year=request.POST['Batch']

            batch = Batch.objects.all().filter(name = programme_name, discipline__acronym = dept, year = batch_year).first()

            user = User.objects.create_user(
                username=roll_no,
                password='hello123',
                first_name=first_name,
                last_name=last_name,
                email=email,
            )

            einfo = ExtraInfo.objects.create(
                id=roll_no,
                user=user,
                title=title,
                sex=sex,
                date_of_birth=dob,
                address=address,
                phone_no=phone_no,
                user_type='student',
                department=department,
            )

            sem=1

            stud_data = Student.objects.create(
                id=einfo,
                programme = programme_name,
                batch=batch_year,
                batch_id = batch,
                father_name = fathers_name,
                mother_name = mothers_name,
                cpi = 0,
                category = category,
                hall_no = hall_no,
                specialization = specialization,
                curr_semester_no=sem,
                
            )

            desig = Designation.objects.get(name='student')
            hold_des = HoldsDesignation.objects.create(
                user=user,
                working=user,
                designation=desig,
            )

            sem_id = Semester.objects.get(curriculum = batch.curriculum, semester_no = sem)
            course_slots = CourseSlot.objects.all().filter(semester = sem_id)
            courses = []
            for course_slot in course_slots:
                courses += course_slot.courses.all()
            new_reg=[]
            '''for c in courses:
                reg=course_registration(
                    course_id = c,
                    semester_id=sem_id,
                    student_id=stud_data
                )
                new_reg.append(reg)
            course_registration.objects.bulk_create(new_reg)'''

    else:
        return render(request, "ais/ais.html", context)
    return render(request, "ais/ais.html", context)


def get_faculty_list():
    """
    to get faculty list from database

    @param:
        request - contains metadata about the requested page.

    @variables:
        f1,f2,f3 - temporary varibles
        faculty - details of faculty of data
        faculty_list - list of faculty

    """
    try:
        f1 = HoldsDesignation.objects.select_related().filter(designation=Designation.objects.get(name = "Assistant Professor"))
        f2 = HoldsDesignation.objects.select_related().filter(designation=Designation.objects.get(name = "Professor"))
        f3 = HoldsDesignation.objects.select_related().filter(designation=Designation.objects.get(name = "Associate Professor"))
    except Exception as e:
        f1=f2=f3=""
        pass
    faculty = list(chain(f1,f2,f3))
    faculty_list = []
    for i in faculty:
        faculty_list.append(i)
    return faculty_list

@login_required
def float_course(request):
    """
    to float courses for the next sem and store data in databsae.
    User must be logged in and must be acadadmin

    @param:
        request - contains metadata about the requested page.

    @variables:
        request_batch - Batch from form 
        request_branch - Branch from form
        request_programme - Programme from form
        request_sem - Semester from form

    """
    if user_check(request):
        return HttpResponseRedirect('/academic-procedures/')
        
    context= {
        'tab_id' :['5','1']
    }
    if request.method == 'POST':
        try:
            request_batch = request.POST['batch']
            request_branch = request.POST['branch']
            request_programme = request.POST['programme']
        except Exception as e:
            request_batch = ""
            request_branch = ""
            request_programme = ""

        if request_batch == "" and request_branch == "" and request_programme=="":
            curriculum = None   #Curriculum.objects.all()
        else:
            sem = sem_for_generate_sheet()
            now = datetime.datetime.now()
            year = int(now.year)
            if sem[0] == 2:
                sem = sem[year-int(request_batch)-1]
            else:
                sem = sem[year-int(request_batch)]
            sem+=1
            curriculum = Curriculum.objects.select_related().filter(branch = request_branch).filter(batch = request_batch).filter(programme= request_programme).filter(sem=sem).order_by('course_code')
        faculty_list = get_faculty_list()
        courses = Course.objects.all()
        course_type = Constants.COURSE_TYPE
        context= {
            'courses': courses,
            'course_type': course_type,
            'curriculum': curriculum,
            'faculty_list': faculty_list,
            'tab_id' :['5','1']
        }
        return render(request, "ais/ais.html", context)
    else:
        return render(request, "ais/ais.html", context)
    return render(request, "ais/ais.html", context)


@login_required
def float_course_submit(request):
    """
    to float courses for the next sem and store data in databsae.
    User must be logged in and must be acadadmin

    @param:
        request - contains metadata about the requested page.

    @variables:
        request_batch - Batch from form 
        request_branch - Branch from form
        request_programme - Programme from form
        request_sem - Semester from form
        
    """
    if user_check(request):
        return HttpResponseRedirect('/academic-procedures/')
        
    context= {
        'tab_id' :['5','1']
    }
    if request.method == "POST":
        i=1
        while True:
            if str(i)+"_ccode" in request.POST:
                if str(i)+"_fac" in request.POST:
                    if request.POST[str(i)+"_fac"] == "" :
                        logging.warning("No faculty")
                    else:
                        flot = Curriculum.objects.select_related().get(curriculum_id=request.POST[str(i)+"_ccode"])
                        flot.floated = True
                        flot.save()
                        new_curr_inst=[]
                        for c,i in enumerate(request.POST.getlist(str(i)+'_fac')):
                            inst = get_object_or_404(User, username = i)
                            inst = ExtraInfo.objects.select_related('user','department').get(user=inst)
                            if c==0:
                                ins=Curriculum_Instructor(
                                    curriculum_id=flot,
                                    instructor_id=inst,
                                    chief_inst=True,
                                )
                                new_curr_inst.append(ins)
                            else:
                                ins=Curriculum_Instructor(
                                    curriculum_id=flot,
                                    instructor_id=inst,
                                    chief_inst=False,
                                )
                                new_curr_inst.append(ins)
                        Curriculum_Instructor.objects.bulk_create(new_curr_inst)
            else:
                break
            i+=1
    return render(request, "ais/ais.html", context)












# # ---------------------senator------------------
# @csrf_exempt
def senator(request):
#     """
#     to add a new student senator

#     @param:
#         request - contains metadata about the requested page

#     @variables:
#         current_user - gets the data of current user.
#         user_details - gets the details of the required user.
#         desig_id - used to check the designation ID.
#         extraInfo - extraInfo object of the student with that rollno
#         s - designation object of senator
#         hDes - holdsDesignation object to store that the particualr student is holding the senator designation
#         student - the student object of the new senator
#         data - data of the student to be displayed in teh webpage

#     """
#     current_user = get_object_or_404(User, username=request.user.username)
#     user_details = ExtraInfo.objects.all().filter(user=current_user).first()
#     desig_id = Designation.objects.all().filter(name='Upper Division Clerk')
    temp = HoldsDesignation.objects.all().select_related().filter(designation = desig_id).first()
    #print (temp)
#     #print (current_user)
#     acadadmin = temp.working
#     k = str(user_details).split()
#     #print(k)
#     final_user = k[2]

#     if (str(acadadmin) != str(final_user)):
#         return HttpResponseRedirect('/academic-procedures/')
#     if request.method == 'POST':
#         #print(request.POST, ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
#         rollno = request.POST.getlist('Roll Number')[0]
#         # #print(request.POST.get('rollno'))
#         extraInfo = ExtraInfo.objects.get(id=rollno)
#         s = Designation.objects.get(name='Senator')
#         hDes = HoldsDesignation()
#         hDes.user = extraInfo.user
#         hDes.working = extraInfo.user
#         hDes.designation = s
#         hDes.save()
#         student = Student.objects.get(id=extraInfo)
#         data = {
#             'name': extraInfo.user.username,
#             'rollno': extraInfo.id,
#             'programme': student.programme,
#             'branch': extraInfo.department.name
#         }
#         return HttpResponseRedirect('/aims/')
#         # return JsonResponse(data)
#     else:
#         return HttpResponseRedirect('/aims/')

# @csrf_exempt
def deleteSenator(request, pk):
#     """
#     to remove a senator from the position

#     @param:
#         request - contains metadata about the requested page

#     @variables:
#         s - the designation object that contains senator
#         student - the list students that is a senator
#         hDes - the holdDesignation object that stores the
#                information that the particular student is a senator

#     """
    pass
#     if request.POST:
#         s = get_object_or_404(Designation, name="Senator")
#         student = get_object_or_404(ExtraInfo, id=request.POST.getlist("senate_id")[0])
#         hDes = get_object_or_404( HoldsDesignation, user = student.user)
#         hDes.delete()
#         return HttpResponseRedirect('/aims/')
#     else:
#         return HttpResponseRedirect('/aims/')# ####################################################


# # ##########covenors and coconvenors##################
# @csrf_exempt
def add_convenor(request):
#     """
#     to add a new student convenor/coconvenor

#     @param:
#         request - contains metadata about the requested page

#     @variables:
#         rollno - rollno of the student to become the convenor/coconvenor
#         extraInfo - extraInfo object of the student with that rollno
#         s - designation object of Convenor
#         p - designation object of Co Convenor
#         result - the data that contains where the student will become
#                  convenor or coconvenor
#         hDes - holdsDesignation object to store that the particualr student is
#                holding the convenor/coconvenor designation
#         student - the student object of the new convenor/coconvenor
#         data - data of the student to be displayed in the webpage

#     """
    s = Designation.objects.get(name='Convenor')
#     p = Designation.objects.get(name='Co Convenor')
#     if request.method == 'POST':
#         rollno = request.POST.get('rollno_convenor')
#         extraInfo = ExtraInfo.objects.get(id=rollno)
#         s = Designation.objects.get(name='Convenor')
#         p = Designation.objects.get(name='Co Convenor')
#         result = request.POST.get('designation')
#         hDes = HoldsDesignation()
#         hDes.user = extraInfo.user
#         hDes.working = extraInfo.user
#         if result == "Convenor":
#             hDes.designation = s
#         else:
#             hDes.designation = p
#         hDes.save()
#         data = {
#             'name': extraInfo.user.username,
#             'rollno_convenor': extraInfo.id,
#             'designation': hDes.designation.name,
#         }
#         return JsonResponse(data)
#     else:
#         data = {}
#         return JsonResponse(data)

# @csrf_exempt
def deleteConvenor(request, pk):
#     """
#     to remove a convenor/coconvenor from the position

#     @param:
#         request - contains metadata about the requested page
#         pk - the primary key of that particular student field

#     @variables:
#         s - the designation object that contains convenor
#         c - the designation object that contains co convenor
#         student - the student object with the given pk
#         hDes - the holdDesignation object that stores the
#                information that the particular student is a convenor/coconvenor to be deleted
#         data - data of the student to be hidden in the webpage

#     """
#     s = get_object_or_404(Designation, name="Convenor")
    c = get_object_or_404(Designation, name="Co Convenor")
#     student = get_object_or_404(ExtraInfo, id=pk)
#     hDes = HoldsDesignation.objects.filter(user = student.user)
#     designation = []
#     for des in hDes:
#         if des.designation == s or des.designation == c:
#             designation = des.designation.name
#             des.delete()
#     data = {
#         'id': pk,
#         'designation': designation,
#     }
#     return JsonResponse(data)# ######################################################


# # ##########Senate meeting Minute##################
# @csrf_exempt
def addMinute(request):
#     """
#     to add a new senate meeting minute object to the database.

#     @param:
#         request - contains metadata about the requested page

#     @variables:
#         current_user - details of the current user.
#         desig_id - to check the designation of the user.
#         user_details - to get the details of the required user.

#     """
#     current_user = get_object_or_404(User, username=request.user.username)
#     user_details = ExtraInfo.objects.all().filter(user=current_user).first()
#     desig_id = Designation.objects.all().filter(name='Upper Division Clerk')
    temp = HoldsDesignation.objects.all().select_related().filter(designation = desig_id).first()
#     #print (temp)
#     #print (current_user)
#     acadadmin = temp.working
#     k = str(user_details).split()
#     #print(k)
#     final_user = k[2]

#     if (str(acadadmin) != str(final_user)):
#         return HttpResponseRedirect('/academic-procedures/')
#     if request.method == 'POST' and request.FILES:
#         form = MinuteForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()
#             return HttpResponse('sucess')
#         else:
#             return HttpResponse('not uploaded')
#         return render(request, "ais/ais.html", {})


def deleteMinute(request):
#     """
#     to delete an existing senate meeting minute object from the database.

#     @param:
#         request - contains metadata about the requested page

#     @variables:
#         data - the id of the minute object to be deleted
#         t - the minute object received from id to be deleted

#     """
#     if request.method == "POST":
#         data = request.POST['delete']
#         t = Meeting.objects.get(id=data)
#         t.delete()

    return HttpResponseRedirect('/aims/')
# # ######################################################


# # ##########Student basic profile##################
# @csrf_exempt
def add_basic_profile(request):
#     """
#     It adds the basic profile information like username,password, name,
#     rollno, etc of a student

#     @param:
#         request - contains metadata about the requested page

#     @variables:
#         name - the name of the student
#         roll - the rollno of the student
#         batch - the current batch of the student
#         programme - the programme the student is enrolled in
#         ph - the phone number of the student

#     """
    if request.method == "POST":
        name = request.POST.get('name')
#         roll = ExtraInfo.objects.get(id=request.POST.get('rollno'))
#         programme = request.POST.get('programme')
#         batch = request.POST.get('batch')
#         ph = request.POST.get('phoneno')
#         if not Student.objects.filter(id=roll).exists():
#             db = Student()
#             st = ExtraInfo.objects.get(id=roll.id)
#             db.name = name.upper()
#             db.id = roll
#             db.batch = batch
#             db.programme = programme
#             st.phone_no = ph
#             db.save()
#             st.save()
#             data = {
#                 'name': name,
#                 'rollno': roll.id,
#                 'programme': programme,
#                 'phoneno': ph,
#                 'batch': batch
#             }
#             #print(data)
#             return JsonResponse(data)
#         else:
#             data = {}
#             return JsonResponse(data)
#     else:
#         data = {}
#         return JsonResponse(data)


# @csrf_exempt
def delete_basic_profile(request, pk):
#     """
#     Deletes the student from the database

#     @param:
#         request - contains metadata about the requested page
#         pk - the primary key of the student's record in the database table

#     @variables:
#         e - the extraInfo objects of the student
#         user - the User object of the student
#         s - the student object of the student

#     """
    e = get_object_or_404(ExtraInfo, id=pk)
#     user = get_object_or_404(User, username = e.user.username)
#     s = get_object_or_404(Student, id=e)
#     data = {
#         'rollno': pk,
#     }
#     s.delete()
#     e.delete()
#     u.delete()
#     return JsonResponse(data)# #########################################################

# '''
# # view to add attendance data to database
# def curriculum(request):

# '''

def delete_advanced_profile(request):
#     """
#     to delete the advance information of the student

#     @param:
#         request - contains metadata about the requested page

#     @variables:
#         current_user - the username of the logged in user
#         user_details - the details of the current user
#         desig_id - checking the designation of the current user
#         acadadmin - deatils of the acad admin
#         s - the student object from the requested rollno

#     """
    current_user = get_object_or_404(User, username=request.user.username)
#     user_details = ExtraInfo.objects.all().filter(user=current_user).first()
#     desig_id = Designation.objects.all().filter(name='Upper Division Clerk')
#     temp = HoldsDesignation.objects.all().filter(designation = desig_id).first()
#     #print (temp)
#     #print (current_user)
#     acadadmin = temp.working
#     k = str(user_details).split()
#     #print(k)
#     final_user = k[2]

#     if (str(acadadmin) != str(final_user)):
#         return HttpResponseRedirect('/academic-procedures/')
#     if request.method == "POST":
#         st = request.POST['delete']
#         arr = st.split("-")
#         stu = arr[0]
#         if Student.objects.get(id=stu):
#             s = Student.objects.get(id=stu)
#             s.father_name = ""
#             s.mother_name = ""
#             s.hall_no = 1
#             s.room_no = ""
#             s.save()
#         else:
#             return HttpResponse("Data Does Not Exist")

#     return HttpResponse("Data Deleted Successfully")


def add_advanced_profile(request):
#     """
#     It adds the advance profile information like hall no, room no,
#     profile picture, about me etc of a student

#     @param:
#         request - contains metadata about the requested page

#     @variables:
#         current_user - the username of the logged in user
#         user_details - the details of the current user
#         desig_id - checking the designation of the current user
#         acadadmin - deatils of the acad admin
#         father - father's name of the student
#         rollno - the rollno of the student required to check if the student is available
#         mother - mother's name of the student
#         add - student's address
#         cpi - student's cpi
#         hall - hall no of where the student stays
#         room no - hostel room no

#     """
    current_user = get_object_or_404(User, username=request.user.username)
#     user_details = ExtraInfo.objects.all().filter(user=current_user).first()
#     desig_id = Designation.objects.all().filter(name='Upper Division Clerk')
#     temp = HoldsDesignation.objects.all().filter(designation = desig_id).first()
#     #print (temp)
#     #print (current_user)
#     acadadmin = temp.working
#     k = str(user_details).split()
#     #print(k)
#     final_user = k[2]

#     if (str(acadadmin) != str(final_user)):
#         return HttpResponseRedirect('/academic-procedures/')
#     if request.method == "POST":
#         #print(request.POST)
#         rollno=request.POST.get('roll')
#         #print(rollno)
#         student = ExtraInfo.objects.get(id=rollno)
#         #print(student.address)
#         if not student:
#             data = {}
#             return JsonResponse(data)
#         else:
#             father = request.POST.get('father')
#             mother = request.POST.get('mother')
#             add = request.POST.get('address')
#             hall = request.POST.get('hall')
#             room = request.POST.get('room')
#             cpi = request.POST.get('cpi')
#             student.address = str(hall) + " " + str(room)
#             student.save()
#             s = Student.objects.get(id=student)
#             s.father_name=father
#             s.mother_name=mother
#             s.hall_no = hall
#             s.room_no = room
#             s.save()

#             return HttpResponseRedirect('/academic-procedures/')
#     return HttpResponseRedirect('/academic-procedures/')



def add_optional(request):
#     """
#     acadmic admin to update the additional courses

#     @param:
#         request - contains metadata about the requested page.

#     @variables:
#         choices - selected addtional courses by the academic person.
#         course - Course details which is selected by the academic admin.
#     """
    if request.method == "POST":
        pass
        # #print(request.POST)
#         choices = request.POST.getlist('choice')
#         for i in choices:
#             course = Course.objects.all().filter(course_id=i).first()
#             course.acad_selection = True
#             course.save()
#         courses = Course.objects.all()
#         for i in courses:
#             if i.course_id not in choices:
#                 i.acad_selection = False
#                 i.save()
#         return HttpResponseRedirect('/academic-procedures/')


def min_cred(request):
#     """
#     to set minimum credit for a current semester that a student must take

#     @param:
#         request - contains metadata about the requested page.

#     @variables:
#         sem_cred = Get credit details from forms and the append it to an array.
#         sem - Get the object for the minimum credits from the database and the update it.
#     """
    if request.method=="POST":
        sem_cred = []
#         sem_cred.append(0)
#         for i in range(1, 10):
#             sem = "sem_"+"1"
#             sem_cred.append(request.POST.getlist(sem)[0])

#         for i in range(1, 9):
#             sem = MinimumCredits.objects.all().filter(semester=i).first()
#             sem.credits = sem_cred[i+1]
#             sem.save()
#         return HttpResponse("Worked")


def view_course(request):
#     if request.method == "POST":
#         programme=request.POST['programme']
#         batch=request.POST['batch']
#         branch=request.POST['branch']
#         sem=request.POST['sem']

#         curriculum_courses = Curriculum.objects.filter(branch = branch).filter(batch = batch).filter(programme= programme).filter(sem = sem)
#         #print(curriculum_courses)
#         courses = Course.objects.all()
#         course_type = Constants.COURSE_TYPE
#         context= {
#             'courses': courses,
#             'course_type': course_type,
#             'curriculum_course': curriculum_courses,
#         }
#         return render(request, "ais/ais.html", context)
#     else:
#         return render(request, "ais/ais.html")
    return render(request, "ais/ais.html")
    


def delete_grade(request):
#     """
#     It deletes the grade of the student

#     @param:
#         request - contains metadata about the requested page

#     @variables:
#         current_user - father's name of the student
#         user_details - the rollno of the student required to check if the student is available
#         desig_id - mother 's name of the student
#         acadadmin - student's address
#         final_user - details of the user
#         sem - current semester of the student
#         data - tag whether to delete it or not
#         course - get the course details
#     """
#     current_user = get_object_or_404(User, username=request.user.username)
#     user_details = ExtraInfo.objects.all().filter(user=current_user).first()
#     desig_id = Designation.objects.all().filter(name='Upper Division Clerk')
#     temp = HoldsDesignation.objects.all().filter(designation = desig_id).first()
#     #print (temp)
#     #print (current_user)
#     acadadmin = temp.working
#     k = str(user_details).split()
#     #print(k)
#     final_user = k[2]

#     if (str(acadadmin) != str(final_user)):
#         return HttpResponseRedirect('/academic-procedures/')
#     #print(request.POST['delete'])
#     data = request.POST['delete']
#     d = data.split("-")
#     id = d[0]
#     course = d[2]
#     sem = int(d[3])
#     if request.method == "POST":
#         if(Grades.objects.filter(student_id=id, sem=sem)):
#             s = Grades.objects.filter(student_id=id, sem=sem)
#             for p in s:
#                 if (str(p.course_id) == course):
#                     #print(p.course_id)
#                     p.delete()
#         else:
#             return HttpResponse("Unable to delete data")
    return HttpResponse("Data Deleted SuccessFully")



@login_required
def verify_grade(request):
    """
    It verify the grades of the student

    @param:
        request - contains metadata about the requested page

    @variables:
        current_user - father's name of the student
        user_details - the rollno of the student required to check if the student is available
        desig_id - mother's name of the student
        acadadmin - student's address
        subject - subject of which the grade has to be added
        sem - semester of the student
        grade - grade to be added in the student
        course - course ofwhich the grade is added
    """
    # if user_check(request):
    #     return HttpResponseRedirect('/academic-procedures/')
        

    # if request.method == "POST":
    #     curr_id=request.POST['course']
    #     #print(curr_id)
    #     curr_course = Curriculum.objects.filter(curriculum_id=curr_id)
    #     grades = Grades.objects.filter(curriculum_id=curr_course)
    #     context= {
    #         'grades': grades,
    #         'tab_id' :"2"
    #     }
    #     return render(request,"ais/ais.html", context)
    # else:
    #     return HttpResponseRedirect('/aims/')
    return HttpResponseRedirect('/aims/')


def confirm_grades(request):
    # if user_check(request):
    #     return HttpResponseRedirect('/academic-procedures/')
        
    # if request.method == "POST":
    #     #print("confirm hone wala hai")
    #     #print(request.POST)
    return HttpResponseRedirect('/aims/')


@login_required()       
def view_all_student_data(request):
    """ views all the students """


    data = []
    #students = Student.objects.select_related('batch_id', 'id__user', 'batch_id__discipline', 'id') .filter(batch=2019).order_by('id').all().only('batch', 'id__id', 'id__user', 'programme', 'batch_id__discipline__acronym', 'specialization', 'id__sex', 'category', 'id__phone_no', 'id__date_of_birth', 'id__user__first_name', 'id__user__last_name', 'id__user__email', 'father_name', 'mother_name', 'id__address')[0:20]
    
    context = get_context(request)
    context['tab_id'][0]='9'

    filter_names = {}
    if request.method == 'POST':
        try:
            filter_names['batch'] = request.POST['batch']
            filter_names['programme'] = request.POST['programme']
            if(request.POST['branch']!='Common'):
                filter_names['batch_id__discipline__acronym'] = request.POST['branch']
            if(request.POST['category']!='ALL'):
                filter_names['category'] = request.POST['category']
            request_batch = request.POST['batch']
            request_branch = request.POST['branch']
            request_programme = request.POST['programme']
            request_rollno = request.POST['Roll_number']
            request_category = request.POST['category']
        except Exception as e:
            request_batch = ""
            request_branch = ""
            request_programme = ""
            request_rollno = ""
            request_category = ""
        if request_batch == "" and request_branch == "" and request_programme=="" and request_rollno=="" and request_category=="":
            data = None
        else:
            if(request_rollno != ""):
                students = Student.objects.select_related('batch_id', 'id__user', 'batch_id__discipline', 'id').filter(id = request_rollno).only('batch', 'id__id', 'id__user', 'programme', 'batch_id__discipline__acronym', 'specialization', 'id__sex', 'category', 'id__phone_no', 'id__date_of_birth', 'id__user__first_name', 'id__user__last_name', 'id__user__email', 'father_name', 'mother_name', 'id__address')
            else:
                students = Student.objects.select_related('batch_id', 'id__user', 'batch_id__discipline', 'id').filter(**filter_names).order_by('id').all().only('batch', 'id__id', 'id__user', 'programme','pwd_status', 'father_mobile_no', 'mother_mobile_no', 'batch_id__discipline__acronym', 'specialization', 'id__sex', 'category', 'id__phone_no', 'id__date_of_birth', 'id__user__first_name', 'id__user__last_name', 'id__user__email', 'father_name', 'mother_name', 'id__address')
            for student in students:
                obj = {
                    "admissionYear" : student.batch,
                    "RollNo" : student.id.id,
                    "name" : student.id.user.get_full_name(),
                    "program": student.programme,
                    "discipline": student.batch_id.discipline.acronym,
                    "specailization": student.specialization,
                    "gender" : student.id.sex,
                    "category": student.category,
                    "pwd_status": student.pwd_status,
                    "Mobile": student.id.phone_no,
                    "dob" : student.id.date_of_birth,
                    "emailid" : student.id.user.email,
                    "father_name": student.father_name,
                    "father_mobile_no": student.father_mobile_no,
                    "mother_name": student.mother_name,
                    "mother_mobile_no": student.mother_mobile_no,
                    "address": student.id.address
                }
                data.append(obj)
        html = render_to_string('ais/stud_list.html',{'students': data,'batch': request_batch,'branch': request_branch,'programme': request_programme,'Roll_number': request_rollno,'category':request_category},request)
        obj = json.dumps({'html':html})
        #context['students'] = data
        return HttpResponse(obj,content_type='application/json')
    else:
        return render(request, "ais/ais.html", context)

@login_required
def generatestudentxlsheet(request):
    """
    to generate Course List of Students

    @param:
        request - contains metadata about the requested page

    @variables:
        batch - gets the batch
        course - gets the course
        curr_key - gets the curriculum from database
        obj - get stdents data from database
        ans - Formatted Array to be converted to xlsx
        k -temporary array to add data to formatted array/variable
        output - io Bytes object to write to xlsx file
        book - workbook of xlsx file
        title - formatting variable of title the workbook
        subtitle - formatting variable of subtitle the workbook
        normaltext - formatting variable for normal text
        sheet - xlsx sheet to be rendered
        titletext - formatting variable of title text
        dep - temporary variables
        z - temporary variables for final output
        b - temporary variables for final output
        c - temporary variables for final output
        st - temporary variables for final output
    """
    if user_check(request):
        return HttpResponseRedirect('/academic-procedures/')
    
    data = []
    filter_names = {}
    try:
        filter_names['batch'] = request.POST['batch']
        filter_names['programme'] = request.POST['programme']
        if(request.POST['branch']!='Common'):
            filter_names['batch_id__discipline__acronym'] = request.POST['branch']
        if(request.POST['category']!='ALL'):
            filter_names['category'] = request.POST['category']
        request_batch = request.POST['batch']
        request_branch = request.POST['branch']
        request_programme = request.POST['programme']
        request_rollno = request.POST['Roll_number']
        request_category = request.POST['category']
    except Exception as e:
        request_batch = ""
        request_branch = ""
        request_programme = ""
        request_rollno = ""
        request_category = ""
    print(request_batch)
    print(request_branch)
    print(request_category)
    print(request_programme)
    if request_batch == "" and request_branch == "" and request_programme=="" and request_rollno=="" and request_category=="":
        data = None
    else:
        if(request_rollno != ""):
            students = Student.objects.select_related('batch_id', 'id__user', 'batch_id__discipline', 'id').filter(id = request_rollno).only('batch', 'id__id', 'id__user', 'programme','pwd_status', 'father_mobile_no', 'mother_mobile_no', 'batch_id__discipline__acronym', 'specialization', 'id__sex', 'category', 'id__phone_no', 'id__date_of_birth', 'id__user__first_name', 'id__user__last_name', 'id__user__email', 'father_name', 'mother_name', 'id__address')
        else:
            students = Student.objects.select_related('batch_id', 'id__user', 'batch_id__discipline', 'id').filter(**filter_names).order_by('id').all().only('batch', 'id__id', 'id__user', 'programme','pwd_status', 'father_mobile_no', 'mother_mobile_no', 'batch_id__discipline__acronym', 'specialization', 'id__sex', 'category', 'id__phone_no', 'id__date_of_birth', 'id__user__first_name', 'id__user__last_name', 'id__user__email', 'father_name', 'mother_name', 'id__address')
        for i in students:
            obj = []
            obj.append(i.batch)
            obj.append(i.id.id)
            obj.append(i.id.user.get_full_name())
            obj.append(i.programme)
            obj.append(i.batch_id.discipline.acronym)
            obj.append(i.specialization)
            obj.append(i.id.sex)
            obj.append(i.category)
            obj.append(i.pwd_status)
            obj.append(i.id.phone_no)
            obj.append(i.id.date_of_birth)
            obj.append(i.id.user.email)
            obj.append(i.father_name)
            obj.append(i.father_mobile_no)
            obj.append(i.mother_name)
            obj.append(i.mother_mobile_no)
            obj.append(i.id.address)
            data.append(obj)
    data.sort()
    output = BytesIO()

    book = Workbook(output,{'in_memory':True})
    title = book.add_format({'bold': True,
                                'font_size': 22,
                                'align': 'center',
                                'valign': 'vcenter'})
    subtitle = book.add_format({'bold': True,
                                'font_size': 15,
                                'align': 'center',
                                'valign': 'vcenter'})
    normaltext = book.add_format({'bold': False,
                                'font_size': 15,
                                'align': 'center',
                                'valign': 'vcenter'})
    sheet = book.add_worksheet()

    title_text = ((str(str(request_batch))))
    sheet.set_default_row(25)

    sheet.merge_range('A2:S2', title_text, title)
    sheet.write_string('A3',"Sl. No",subtitle)
    sheet.write_string('B3',"Admission Year",subtitle)
    sheet.write_string('C3',"Roll No",subtitle)
    sheet.write_string('D3',"Full Name",subtitle)
    sheet.write_string('E3',"Program",subtitle)
    sheet.write_string('F3',"Discipline",subtitle)
    sheet.write_string('G3',"Specialization",subtitle)
    sheet.write_string('H3',"Gender",subtitle)
    sheet.write_string('I3',"Category",subtitle)
    sheet.write_string('J3',"PWD Status",subtitle)
    sheet.write_string('K3',"Mobile Number",subtitle)
    sheet.write_string('L3',"DOB",subtitle)
    sheet.write_string('M3',"Email ID",subtitle)
    sheet.write_string('N3',"Father's Name",subtitle)
    sheet.write_string('O3',"Father's Mobile Number",subtitle)
    sheet.write_string('P3',"Mother's Name",subtitle)
    sheet.write_string('Q3',"Mother's Mobile Number",subtitle)
    sheet.write_string('R3',"Full Address with Pin code",subtitle)
    sheet.write_string('S3','Remarks',subtitle)
    sheet.set_column('A:A',20)
    sheet.set_column('B:B',20)
    sheet.set_column('C:C',15)
    sheet.set_column('D:D',60)
    sheet.set_column('E:E',30)
    sheet.set_column('F:F',30)
    sheet.set_column('G:G',30)
    sheet.set_column('H:H',30)
    sheet.set_column('I:I',30)
    sheet.set_column('J:J',30)
    sheet.set_column('K:K',30)
    sheet.set_column('L:L',30)
    sheet.set_column('M:M',30)
    sheet.set_column('N:N',30)
    sheet.set_column('O:O',30)
    sheet.set_column('P:P',30)
    sheet.set_column('Q:Q',30)
    sheet.set_column('R:R',30)
    sheet.set_column('S:S',30)
    k = 4
    num = 1
    for i in data:
        sheet.write_number('A'+str(k),num,normaltext)
        num+=1
        sheet.write_string('B'+str(k),str(i[0]),normaltext)
        sheet.write_string('C'+str(k),i[1],normaltext)
        sheet.write_string('D'+str(k),i[2],normaltext)
        sheet.write_string('E'+str(k),i[3],normaltext)
        sheet.write_string('F'+str(k),i[4],normaltext)
        sheet.write_string('G'+str(k),i[5],normaltext)
        sheet.write_string('H'+str(k),i[6],normaltext)
        sheet.write_string('I'+str(k),i[7],normaltext)
        sheet.write_string('J'+str(k),str(i[8]),normaltext)
        sheet.write_string('K'+str(k),str(i[9]),normaltext)
        sheet.write_string('L'+str(k),str(i[10]),normaltext)
        sheet.write_string('M'+str(k),i[11],normaltext)
        sheet.write_string('N'+str(k),i[12],normaltext)
        sheet.write_string('O'+str(k),str(i[13]),normaltext)
        sheet.write_string('P'+str(k),i[14],normaltext)
        sheet.write_string('Q'+str(k),str(i[15]),normaltext)
        sheet.write_string('R'+str(k),i[16],normaltext)
        k+=1
    book.close()
    output.seek(0)
    response = HttpResponse(output.read(),content_type = 'application/vnd.ms-excel')
    st = 'attachment; filename = ' + request_batch+ request_branch + '.xlsx'
    response['Content-Disposition'] = st
    return response
