import datetime
import json

from itertools import chain
from xhtml2pdf import pisa
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.template.loader import get_template
from io import BytesIO


from applications.globals.models import Designation, ExtraInfo, HoldsDesignation

from .forms import AcademicTimetableForm, ExamTimetableForm, MinuteForm
from .models import (Course, Instructor, Exam_timetable, Grades, Meeting, Student,
                     Student_attendance, Timetable, Calendar)
from applications.academic_procedures.models import MinimumCredits, Register


def homepage(request):
    current_user = get_object_or_404(User, username=request.user.username)
    user_details = ExtraInfo.objects.all().filter(user=current_user).first()
    desig_id = Designation.objects.all().filter(name='Upper Division Clerk')
    temp = HoldsDesignation.objects.all().filter(designation = desig_id).first()
    print (temp)
    print (current_user)
    acadadmin = temp.working
    k = str(user_details).split()
    print(k)
    final_user = k[2]

    if (str(acadadmin) != str(final_user)):
        return HttpResponseRedirect('/academic-procedures/')
    minuteForm = MinuteForm()
    examTtForm = ExamTimetableForm()
    acadTtForm = AcademicTimetableForm()
    calendar = Calendar.objects.all()
    opt_courses = Course.objects.all().filter(optional=True)
    course_list = sem_for_generate_sheet()
    get_course_list = Course.objects.all().filter(sem = course_list[0])
    get_course_list_1 = Course.objects.all().filter(sem = course_list[1])
    get_course_list_2 = Course.objects.all().filter(sem = course_list[2])
    get_course_list_3 = Course.objects.all().filter(sem = course_list[3])

    get_courses = list(chain(get_course_list, get_course_list_1, get_course_list_2, get_course_list_3))
    if(course_list[0]==1):
        course_list = [2, 4, 6, 8]
    get_course_list = Course.objects.all().filter(sem = course_list[0])
    get_course_list_1 = Course.objects.all().filter(sem = course_list[1])
    get_course_list_2 = Course.objects.all().filter(sem = course_list[2])
    get_course_list_3 = Course.objects.all().filter(sem = course_list[3])

    this_sem_courses = list(chain(get_course_list, get_course_list_1, get_course_list_2, get_course_list_3))


    print("Courses>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.", get_courses)

    # print("Courses>>>>>>>>>>>.", courses)
    # print(calendar)
    try:
        senator_des = Designation.objects.get(name='senate')
        convenor_des = Designation.objects.get(name='Convenor')
        coconvenor_des = Designation.objects.get(name='Co Convenor')
        dean_des = Designation.objects.get(name='Dean')
        senates = ExtraInfo.objects.filter(designation=senator_des)
        Convenor = ExtraInfo.objects.filter(designation=convenor_des)
        CoConvenor = ExtraInfo.objects.filter(designation=coconvenor_des)
        Dean = ExtraInfo.objects.get(designation=dean_des)
        students = Student.objects.filter(id__in=senates)
        meetings = Meeting.objects.all()
        student = Student.objects.all()
        extra = ExtraInfo.objects.all()
        courses = Course.objects.all()
        timetable = Timetable.objects.all()
        exam_t = Exam_timetable.objects.all()
        grade = Grades.objects.all()
    except:
        senates = ""
        students = ""
        Convenor = ""
        CoConvenor = ""
        meetings = ""
        Dean = ""
        student = ""
        grade = ""
        courses = ""
        extra = ""
        exam_t = ""
        timetable = ""
    pass

    context = {
         'senates': senates,
         'students': students,
         'Convenor': Convenor,
         'CoConvenor': CoConvenor,
         'meetings': meetings,
         'minuteForm': minuteForm,
         'acadTtForm': acadTtForm,
         'examTtForm': examTtForm,
         'Dean': Dean,
         'student': student,
         'extra': extra,
         'grade': grade,
         'courses': courses,
         'exam': exam_t,
         'timetable': timetable,
         'academic_calendar': calendar,
         'opt_courses': opt_courses,
         'next_sem_course': get_courses,
         'this_sem_course': this_sem_courses,
    }
    return render(request, "ais/ais.html", context)


# ---------------------senator------------------
@csrf_exempt
def senator(request):
    current_user = get_object_or_404(User, username=request.user.username)
    user_details = ExtraInfo.objects.all().filter(user=current_user).first()
    desig_id = Designation.objects.all().filter(name='Upper Division Clerk')
    temp = HoldsDesignation.objects.all().filter(designation = desig_id).first()
    print (temp)
    print (current_user)
    acadadmin = temp.working
    k = str(user_details).split()
    print(k)
    final_user = k[2]

    if (str(acadadmin) != str(final_user)):
        return HttpResponseRedirect('/academic-procedures/')
    if request.method == 'POST':
        rollno = request.POST.get('rollno')
        extraInfo = ExtraInfo.objects.get(id=rollno)
        s = Designation.objects.get(name='senate')
        extraInfo.designation.add(s)
        extraInfo.save()
        student = Student.objects.get(id=extraInfo)
        data = {
            'name': extraInfo.user.username,
            'rollno': extraInfo.id,
            'programme': student.programme,
            'branch': extraInfo.department.name
        }
        return JsonResponse(data)
    else:
        data = {}
        return JsonResponse(data)


@csrf_exempt
def deleteSenator(request, pk):
    s = get_object_or_404(Designation, name="senate")
    student = get_object_or_404(ExtraInfo, id=pk)
    student.designation.remove(s)
    data = {}
    return JsonResponse(data)
# ####################################################


# ##########covenors and coconvenors##################
@csrf_exempt
def add_convenor(request):
    s = Designation.objects.get(name='Convenor')
    p = Designation.objects.get(name='Co Convenor')
    if request.method == 'POST':
        rollno = request.POST.get('rollno_convenor')
        extraInfo = ExtraInfo.objects.get(id=rollno)
        result = request.POST.get('designation')
        if result == "Convenor":
            extraInfo.designation.add(s)
            extraInfo.save()
            designation = 'Convenor'
        else:
            extraInfo.designation.add(p)
            extraInfo.save()
            designation = 'Co Convenor'
        data = {
            'name': extraInfo.user.username,
            'rollno_convenor': extraInfo.id,
            'designation': designation,
        }
        return JsonResponse(data)
    else:
        data = {}
        return JsonResponse(data)


@csrf_exempt
def deleteConvenor(request, pk):
    s = get_object_or_404(Designation, name="Convenor")
    c = get_object_or_404(Designation, name="Co Convenor")
    student = get_object_or_404(ExtraInfo, id=pk)
    for des in student.designation.all():
        if des.name == s.name:
            student.designation.remove(s)
            designation = des.name
        elif des.name == c.name:
            designation = des.name
            student.designation.remove(c)
    data = {
        'id': pk,
        'designation': designation,
    }
    return JsonResponse(data)
# ######################################################


# ##########Senate meeting Minute##################
@csrf_exempt
def addMinute(request):
    current_user = get_object_or_404(User, username=request.user.username)
    user_details = ExtraInfo.objects.all().filter(user=current_user).first()
    desig_id = Designation.objects.all().filter(name='Upper Division Clerk')
    temp = HoldsDesignation.objects.all().filter(designation = desig_id).first()
    print (temp)
    print (current_user)
    acadadmin = temp.working
    k = str(user_details).split()
    print(k)
    final_user = k[2]

    if (str(acadadmin) != str(final_user)):
        return HttpResponseRedirect('/academic-procedures/')
    if request.method == 'POST' and request.FILES:
        form = MinuteForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponse('sucess')
        else:
            return HttpResponse('not uploaded')
        return render(request, "ais/ais.html", {})


def deleteMinute(request):
    minute = Meeting.objects.get(id=request.POST["delete"])
    minute.delete()
    return HttpResponse("Deleted")
# ######################################################


# ##########Student basic profile##################
@csrf_exempt
def add_basic_profile(request):
    if request.method == "POST":
        name = request.POST.get('name')
        roll = ExtraInfo.objects.get(id=request.POST.get('rollno'))
        programme = request.POST.get('programme')
        batch = request.POST.get('batch')
        ph = request.POST.get('phoneno')
        if not Student.objects.filter(id=roll).exists():
            db = Student()
            st = ExtraInfo.objects.get(id=roll.id)
            db.name = name.upper()
            db.id = roll
            db.batch = batch
            db.programme = programme
            st.phone_no = ph
            db.save()
            st.save()
            data = {
                'name': name,
                'rollno': roll.id,
                'programme': programme,
                'phoneno': ph,
                'batch': batch
            }
            print(data)
            return JsonResponse(data)
        else:
            data = {}
            return JsonResponse(data)
    else:
        data = {}
        return JsonResponse(data)


@csrf_exempt
def delete_basic_profile(request, pk):
    if(Student.objects.get(id=pk)):
        Student.objects.get(id=pk).delete()
    else:
        return HttpResponse("Id Does not exist")
    data = {}
    return JsonResponse(data)
# #########################################################


# view to add attendance data to database
def add_attendance(request):
    current_user = get_object_or_404(User, username=request.user.username)
    user_details = ExtraInfo.objects.all().filter(user=current_user).first()
    desig_id = Designation.objects.all().filter(name='Upper Division Clerk')
    temp = HoldsDesignation.objects.all().filter(designation = desig_id).first()
    print (temp)
    print (current_user)
    acadadmin = temp.working
    k = str(user_details).split()
    print(k)
    final_user = k[2]

    if (str(acadadmin) != str(final_user)):
        return HttpResponseRedirect('/academic-procedures/')
    if request.method == 'POST':
        s_id = request.POST.get('student_id')
        c_id = request.POST.get('course_id')

        context = {}
        # validating student data
        try:
            student_id = Student.objects.get(id_id=s_id)
        except:
            error_mess = "Student Data Not Found"
            context['result'] = 'Failure'
            context['message'] = error_mess
            return HttpResponse(json.dumps(context), content_type='add_attendance/json')
        # validating course data
        try:
            course_id = Course.objects.get(course_id=c_id)
        except:
            error_mess = "Course Data Not Found"
            context['result'] = 'Failure'
            context['message'] = error_mess
            return HttpResponse(json.dumps(context), content_type='add_attendance/json')

        present_attend = int(request.POST.get('present_attend'))
        total_attend = int(request.POST.get('total_attend'))
        # checking attendance data
        if present_attend > total_attend:
            error_mess = "Present attendance should not be greater than Total attendance"
            context['result'] = 'Failure'
            context['message'] = error_mess
            return HttpResponse(json.dumps(context), content_type='add_attendance/json')

        try:
            student_attend = Student_attendance.objects.get(student_id_id=student_id,
                                                            course_id_id=course_id)
            student_attend.present_attend = present_attend
            student_attend.total_attend = total_attend
            success_mess = "Your Data has been successfully edited"
            student_attend.save()
        except:
            student_attend = Student_attendance()
            student_attend.course_id = course_id
            student_attend.student_id = student_id
            student_attend.present_attend = present_attend
            student_attend.total_attend = total_attend
            success_mess = "Your Data has been successfully added"
            student_attend.save()
        context['result'] = 'Success'
        context['message'] = success_mess
        return HttpResponse(json.dumps(context), content_type='add_attendance/json')


# view to fetch attendance data
def get_attendance(request):
    current_user = get_object_or_404(User, username=request.user.username)
    user_details = ExtraInfo.objects.all().filter(user=current_user).first()
    desig_id = Designation.objects.all().filter(name='Upper Division Clerk')
    temp = HoldsDesignation.objects.all().filter(designation = desig_id).first()
    print (temp)
    print (current_user)
    acadadmin = temp.working
    k = str(user_details).split()
    print(k)
    final_user = k[2]

    if (str(acadadmin) != str(final_user)):
        return HttpResponseRedirect('/academic-procedures/')
    course_id = request.GET.get('course_id')

    c_id = Course.objects.get(course_id=course_id)
    data = Student_attendance.objects.filter(course_id_id=c_id).values_list('course_id_id',
                                                                            'student_id_id',
                                                                            'present_attend',
                                                                            'total_attend')
    stud_data = {}
    stud_data['name'] = []
    stud_data['programme'] = []
    stud_data['batch'] = []
    for obj in data:
        roll = obj[1]
        extra_info = ExtraInfo.objects.get(id=roll)
        s_id = Student.objects.get(id=extra_info)

        stud_data['name'].append(s_id.name)
        stud_data['programme'].append(s_id.programme)
        stud_data['batch'].append(s_id.batch)

    context = {}
    try:
        context['result'] = 'Success'
        context['tuples'] = list(data)
        context['stud_data'] = stud_data
    except:
        context['result'] = 'Failure'

    return HttpResponse(json.dumps(context), content_type='get_attendance/json')


# view to delete attendance data
def delete_attendance(request):
    current_user = get_object_or_404(User, username=request.user.username)
    user_details = ExtraInfo.objects.all().filter(user=current_user).first()
    desig_id = Designation.objects.all().filter(name='Upper Division Clerk')
    temp = HoldsDesignation.objects.all().filter(designation = desig_id).first()
    print (temp)
    print (current_user)
    acadadmin = temp.working
    k = str(user_details).split()
    print(k)
    final_user = k[2]

    if (str(acadadmin) != str(final_user)):
        return HttpResponseRedirect('/academic-procedures/')
    course_id = request.GET.get('course_id')
    student_id = request.GET.get('student_id')
    c_id = Course.objects.get(course_id=course_id)
    student_attend = Student_attendance.objects.get(student_id_id=student_id, course_id_id=c_id)
    student_attend.delete()
    context = {}
    context['result'] = 'Success'
    return HttpResponse(json.dumps(context), content_type='delete_attendance/json')


def delete_advanced_profile(request):
    current_user = get_object_or_404(User, username=request.user.username)
    user_details = ExtraInfo.objects.all().filter(user=current_user).first()
    desig_id = Designation.objects.all().filter(name='Upper Division Clerk')
    temp = HoldsDesignation.objects.all().filter(designation = desig_id).first()
    print (temp)
    print (current_user)
    acadadmin = temp.working
    k = str(user_details).split()
    print(k)
    final_user = k[2]

    if (str(acadadmin) != str(final_user)):
        return HttpResponseRedirect('/academic-procedures/')
    if request.method == "POST":
        st = request.POST['delete']
        arr = st.split("-")
        stu = arr[0]
        if Student.objects.get(id=stu):
            s = Student.objects.get(id=stu)
            s.father_name = ""
            s.mother_name = ""
            s.hall_no = 1
            s.room_no = ""
            s.save()
        else:
            return HttpResponse("Data Does Not Exist")

    return HttpResponse("Data Deleted Successfully")


def add_advanced_profile(request):
    current_user = get_object_or_404(User, username=request.user.username)
    user_details = ExtraInfo.objects.all().filter(user=current_user).first()
    desig_id = Designation.objects.all().filter(name='Upper Division Clerk')
    temp = HoldsDesignation.objects.all().filter(designation = desig_id).first()
    print (temp)
    print (current_user)
    acadadmin = temp.working
    k = str(user_details).split()
    print(k)
    final_user = k[2]

    if (str(acadadmin) != str(final_user)):
        return HttpResponseRedirect('/academic-procedures/')
    if request.method == "POST":
        try:
            roll = ExtraInfo.objects.get(id=request.POST['roll'])
            father = request.POST['father']
            mother = request.POST['mother']
            hall = request.POST['hall']
            room = request.POST['room']
        except:
            return HttpResponse("Student Does Not Exist")
        try:
            db = Student.objects.get(id=roll)
        except:
            return HttpResponse("Student Does Not Exist")
        db.father_name = father.upper()
        db.mother_name = mother.upper()
        db.hall_no = hall
        db.room_no = room.upper()
        db.save()
    return HttpResponse("Data successfully inputed")


def add_grade(request):
    current_user = get_object_or_404(User, username=request.user.username)
    user_details = ExtraInfo.objects.all().filter(user=current_user).first()
    desig_id = Designation.objects.all().filter(name='Upper Division Clerk')
    temp = HoldsDesignation.objects.all().filter(designation = desig_id).first()
    print (temp)
    print (current_user)
    acadadmin = temp.working
    k = str(user_details).split()
    print(k)
    final_user = k[2]

    if (str(acadadmin) != str(final_user)):
        return HttpResponseRedirect('/academic-procedures/')
    if request.method == "POST":
        try:
            roll = Student.objects.get(id=request.POST['roll'])
        except:
            return HttpResponse("Student Does Not Exist")
        subject = request.POST['course']
        sem = request.POST['sem']
        grade = request.POST['grade']
        course = Course.objects.get(course_id=subject)
        arr = []
        for c in roll.courses.all():
            arr.append(c)
        flag = 1
        print(arr)
        for i in arr:
            if(subject == str(i)):
                if(sem == str(c.sem)):
                    if not Grades.objects.filter(student_id=roll, course_id=course).exists():
                        db = Grades()
                        db.student_id = roll
                        db.course_id = course
                        db.sem = sem
                        db.grade = grade
                        db.save()
                        flag = 0
                        break
                    else:
                        return HttpResponse("Data Already Exists")
                else:
                    return HttpResponse("Student did not take " + subject + " in semester " + sem)
        if(flag == 1):
            return HttpResponse("Student did not opt for course")
        grades = Grades.objects.all()
        context = {
            'grades': grades,
        }
    return render(request, "ais/ais.html", context)


def delete_grade(request):
    current_user = get_object_or_404(User, username=request.user.username)
    user_details = ExtraInfo.objects.all().filter(user=current_user).first()
    desig_id = Designation.objects.all().filter(name='Upper Division Clerk')
    temp = HoldsDesignation.objects.all().filter(designation = desig_id).first()
    print (temp)
    print (current_user)
    acadadmin = temp.working
    k = str(user_details).split()
    print(k)
    final_user = k[2]

    if (str(acadadmin) != str(final_user)):
        return HttpResponseRedirect('/academic-procedures/')
    print(request.POST['delete'])
    data = request.POST['delete']
    d = data.split("-")
    id = d[0]
    course = d[2]
    sem = int(d[3])
    if request.method == "POST":
        if(Grades.objects.filter(student_id=id, sem=sem)):
            s = Grades.objects.filter(student_id=id, sem=sem)
            for p in s:
                if (str(p.course_id) == course):
                    print(p.course_id)
                    p.delete()
        else:
            return HttpResponse("Unable to delete data")
    return HttpResponse("Data Deleted SuccessFully")


def add_course(request):
    current_user = get_object_or_404(User, username=request.user.username)
    user_details = ExtraInfo.objects.all().filter(user=current_user).first()
    desig_id = Designation.objects.all().filter(name='Upper Division Clerk')
    temp = HoldsDesignation.objects.all().filter(designation = desig_id).first()
    print (temp)
    print (current_user)
    acadadmin = temp.working
    k = str(user_details).split()
    print(k)
    final_user = k[2]

    if (str(acadadmin) != str(final_user)):
        return HttpResponseRedirect('/academic-procedures/')
    if request.method == "POST":
        try:
            c = Student.objects.get(id=request.POST['roll'])
        except:
            return HttpResponse("Student Does Not Exist")
        if(request.POST['c1']):
            c_id = Course.objects.get(course_id=request.POST['c1'])
            c.courses.add(c_id)
        if(request.POST['c2']):
            c_id2 = Course.objects.get(course_id=request.POST['c2'])
            c.courses.add(c_id2)
        if(request.POST['c3']):
            c_id3 = Course.objects.get(course_id=request.POST['c3'])
            c.courses.add(c_id3)
        if(request.POST['c4']):
            c_id4 = Course.objects.get(course_id=request.POST['c4'])
            c.courses.add(c_id4)
        if(request.POST['c5']):
            c_id5 = Course.objects.get(course_id=request.POST['c5'])
            c.courses.add(c_id5)
        if(request.POST['c6']):
            c_id6 = Course.objects.get(course_id=request.POST['c6'])
            c.courses.add(c_id6)

        c.save()
        print(c.courses.all())
    return HttpResponse("Data Entered Successfully")


def add_timetable(request):
    acadTtForm = AcademicTimetableForm()
    if request.method == 'POST' and request.FILES:
        acadTtForm = AcademicTimetableForm(request.POST, request.FILES)
        if acadTtForm.is_valid():
            acadTtForm.save()
            return HttpResponse('sucess')
    else:
        return HttpResponse('not uploaded')


def add_exam_timetable(request):
    examTtForm = ExamTimetableForm()
    if request.method == 'POST' and request.FILES:
        examTtForm = ExamTimetableForm(request.POST, request.FILES)
        if examTtForm.is_valid():
            examTtForm.save()
            return HttpResponse('sucess')
    else:
        return HttpResponse('not uploaded')


def delete_timetable(request):
    if request.method == "POST":
        data = request.POST['delete']
        t = Timetable.objects.get(time_table=data)
        t.delete()
        return HttpResponse("TimeTable Deleted")


def delete_exam_timetable(request):
    if request.method == "POST":
        data = request.POST['delete']
        t = Exam_timetable.objects.get(exam_time_table=data)
        t.delete()
        return HttpResponse("TimeTable Deleted")

def add_calendar(request):
    if request.method == "POST":
        print("Requested Method: ", request.POST)
        from_date = request.POST.getlist('from_date')
        to_date = request.POST.getlist('to_date')
        desc = request.POST.getlist('description')[0]
        print(from_date, to_date, desc)
        from_date = from_date[0].split('-')
        from_date = [int(i) for i in from_date]
        from_date = datetime.datetime(*from_date).date()
        to_date = to_date[0].split('-')
        to_date = [int(i) for i in to_date]
        to_date = datetime.datetime(*to_date).date()
        print(from_date, to_date, desc)
        c = Calendar(
            from_date=from_date,
            to_date=to_date,
            description=desc)
        print(c)
        c.save()
        return HttpResponse("Calendar Added")

def update_calendar(request):
    if request.method == "POST":
        print("Requested Method: ", request.POST)
        from_date = request.POST.getlist('from_date')
        to_date = request.POST.getlist('to_date')
        desc = request.POST.getlist('description')[0]
        prev_desc = request.POST.getlist('prev_desc')[0]
        print(from_date, to_date, desc, prev_desc)
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
        return HttpResponseRedirect('/academic-procedures/')

def add_optional(request):
    if request.method == "POST":
        print(request.POST)
        choices = request.POST.getlist('choice')
        for i in choices:
            course = Course.objects.all().filter(course_id=i).first()
            course.acad_selection = True
            course.save()
        courses = Course.objects.all()
        for i in courses:
            if i.course_id not in choices:
                i.acad_selection = False
                i.save()
        return HttpResponseRedirect('/academic-procedures/')

def add_course(request):
    if request.method == "POST":
        print(request.POST)
        c_id = request.POST.getlist('course_id')[0]
        c_name = request.POST.getlist('course_name')[0]
        c_opt = request.POST.getlist('course_optional')[0]
        c_sem = request.POST.getlist('course_semester')[0]
        c_cred = request.POST.getlist('course_credit')[0]
        print("Credit>>>>>>>>>>", c_cred)
        c_check = True if c_opt == "on" else False
        c_save = Course(course_id=c_id,
            course_name=c_name,
            sem=c_sem,
            credits=c_cred,
            optional=c_check)
        c_save.save()
        return HttpResponse("Worked")

def min_cred(request):
    if request.method=="POST":
        sem_cred = []
        sem_cred.append(0)
        for i in range(1, 10):
            sem = "sem_"+"1"
            sem_cred.append(request.POST.getlist(sem)[0])

        for i in range(1, 9):
            sem = MinimumCredits.objects.all().filter(semester=i).first()
            sem.credits = sem_cred[i+1]
            sem.save()
        return HttpResponse("Worked")

#Generate Attendance Sheet
def sem_for_generate_sheet():
    now = datetime.datetime.now()
    year, month = now.year, int(now.month)
    sem = 'odd'

    if month >= 7 and month <= 12:
        return [2, 4, 6, 8]
    else:
        return [1, 3, 5, 7]


def generatexlsheet(request):
    idd = str(request.POST['year'])
    f_key = Course.objects.get(course_name = str(idd))
    course_id = str(f_key.course_id)
    obj = Register.objects.all().filter(course_id = f_key)
    ans = []
    for i in obj:
        k = []
        k.append(i.student_id.id.id)
        k.append(i.student_id.id.user.first_name)
        k.append(i.student_id.id.user.last_name)
        k.append(i.student_id.id.department)
        ans.append(k)
    ans.sort()
    import io
    output = io.BytesIO()
    from xlsxwriter.workbook import Workbook

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

    title_text = ((str(course_id)+" : "+str(str(idd))))
    #width = len(title_text)
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
    st = 'attachment; filename = ' + course_id + '.xlsx'
    response['Content-Disposition'] = st
    return response


'''
def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse('We had some errors<pre>%s</pre>' % escape(html))
'''


def generate_preregistration_report(request):
    sem = sem_for_generate_sheet();
    # EDIT HERE ON DEPLOYMENT
    sem = [2, 4, 6, 8]
    print(sem)
    # END EDIT HERE
    obj1 = Register.objects.filter(semester=sem[0])
    obj2 = Register.objects.filter(semester=sem[1])
    obj3 = Register.objects.filter(semester=sem[2])
    obj4 = Register.objects.filter(semester=sem[3])
    obj = list(chain(obj1, obj2, obj3, obj4))

    data = []
    m = 1
    for i in obj:
        z = []
        z.append(m)
        m += 1
        z.append(i.student_id.id.user.username)
        z.append(str(i.student_id.id.user.first_name)+" "+str(i.student_id.id.user.last_name))
        z.append(i.student_id.id.department.name)
        z.append(i.course_id.credits)
        z.append(i.course_id.course_id)
        z.append(i.course_id.course_name)
        try:
            p = Instructor.objects.get(course_id = i.course_id)
            z.append(p.instructor_id)
        except:
            z.append("Dr. Atul Gupta")
        data.append(z)
    data.sort()
    print(data)
    context = {'dict':data }
    return render(request,'ais/generate_preregistration_report.html', context)
