import json

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from applications.globals.models import Designation, ExtraInfo

from .forms import MinuteForm
from .models import (Course, Exam_timetable, Grades, Meeting, Student,
                     Student_attendance, Timetable)


def homepage(request):
    form = MinuteForm()

    try:
        s = Designation.objects.get(name='senate')
        v = Designation.objects.get(name='Convenor')
        t = Designation.objects.get(name='Co Convenor')
        d = Designation.objects.get(name='Dean')
        senates = ExtraInfo.objects.filter(designation=s)
        Convenor = ExtraInfo.objects.filter(designation=v)
        CoConvenor = ExtraInfo.objects.filter(designation=t)
        Dean = ExtraInfo.objects.get(designation=d)
        students = Student.objects.filter(id__in=senates)
        meetings = Meeting.objects.all()
        student = Student.objects.all()
        extra = ExtraInfo.objects.all()
        course = Course.objects.all()
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
        course = ""
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
         'form': form,
         'Dean': Dean,
         'student': student,
         'extra': extra,
         'grade': grade,
         'courses': course,
         'exam': exam_t,
         'timetable': timetable,
    }
    if request.method == 'POST' and request.FILES:
        form = MinuteForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponse('sucess')
        else:
            return HttpResponse('not uploaded')
    return render(request, "ais/ais.html", context)


def deleteSenator(request):
    s = Designation.objects.get(name="senate")
    student = ExtraInfo.objects.get(id=request.POST["delete"])
    student.designation.remove(s)
    return HttpResponse("Deleted")


# EDITED BY ANURAAG
@csrf_exempt
def senator(request):
    print(request.POST)
    if request.method == 'POST':
        rollno = request.POST['rollno']
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
# END EDIT


def add_convenor(request):
    s = Designation.objects.get(name='Convenor')
    p = Designation.objects.get(name='Co Convenor')
    if request.method == 'POST':
        extraInfo = ExtraInfo.objects.get(id=request.POST["Roll Number"])
        result = request.POST["Designation"]
        if result == "Convenor":
            extraInfo.designation.add(s)
            extraInfo.save()
        else:
            extraInfo.designation.add(p)
            extraInfo.save()
    return HttpResponse("Data Inputed")


def delete1(request):
    s = Designation.objects.get(name="Convenor")
    student = ExtraInfo.objects.get(id=request.POST["delete"])
    student.designation.remove(s)
    return HttpResponse("Deleted")


def delete2(request):
    s = Designation.objects.get(name="CoConvenor")
    student = ExtraInfo.objects.get(id=request.POST["delete"])
    student.designation.remove(s)
    return HttpResponse("Deleted")


def add_attendance(request):
    if request.method == 'POST':
        student_attend = Student_attendance()
        s_id = request.POST.get('student_id')
        c_id = request.POST.get('course_id')
        print(s_id)
        print(c_id)
        context = {}
        try:
            student_attend.student_id = Student.objects.get(id_id=s_id)
        except:
            error_mess = "Student Data Not Found"
            context['result'] = 'Failure'
            context['message'] = error_mess
            messages.error(request, error_mess)
            return HttpResponse(json.dumps(context), content_type='add_attendance/json')
        try:
            student_attend.course_id = Course.objects.get(course_id=c_id)
        except:
            error_mess = "Course Data Not Found"
            context['result'] = 'Failure'
            context['message'] = error_mess
            messages.error(request, error_mess)
            return HttpResponse(json.dumps(context), content_type='add_attendance/json')
        student_attend.present_attend = request.POST.get('present_attend')
        student_attend.total_attend = request.POST.get('total_attend')
        if student_attend.present_attend > student_attend.total_attend:
            error_mess = "Present attendance should not be greater than Total attendance"
            context['result'] = 'Failure'
            context['message'] = error_mess
            return HttpResponse(json.dumps(context), content_type='add_attendance/json')
        success_mess = "Your Data has been successfully added"
        messages.success(request, success_mess)
        student_attend.save()
        context['result'] = 'Success'
        context['message'] = success_mess
        messages.error(request, success_mess)
        return HttpResponse(json.dumps(context), content_type='add_attendance/json')


def get_attendance(request):
    course_id = request.GET.get('course_id')
    print(course_id)
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
        roll = data[0][1]
        extra_info = ExtraInfo.objects.get(id=roll)
        s_id = Student.objects.get(id=extra_info)
        s_name = s_id.name
        s_programme = s_id.programme
        s_batch = s_id.batch
        print(s_name)
        print(s_programme)
        stud_data['name'].append(s_name)
        stud_data['programme'].append(s_programme)
        stud_data['batch'].append(s_batch)
    print(stud_data)
    context = {}
    try:
        context['result'] = 'Success'
        context['tuples'] = list(data)
        context['stud_data'] = stud_data
    except:
        context['result'] = 'Failure'
    print(data[0][1])
    print(stud_data['name'][0])
    print(context)
    return HttpResponse(json.dumps(context), content_type='get_attendance/json')


def deleteMinute(request):
    minute = Meeting.objects.get(id=request.POST["delete"])
    minute.delete()
    return HttpResponse("Deleted")


def add_basic_profile(request):
    if request.method == "POST":
        name = request.POST['name']
        roll = ExtraInfo.objects.get(id=request.POST['roll'])
        programme = request.POST['programme']
        batch = request.POST['batch']
        ph = request.POST['ph']
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
        else:
            return HttpResponse("Data Already Exists")
    students = Student.objects.all()
    extra = ExtraInfo.objects.all()
    context = {
        'students': students,
        'extra': extra,
    }
    return render(request, "ais/ais.html", context)


def delete_basic_profile(request):
    if request.method == "POST":
        if(Student.objects.get(id=request.POST['delete'])):
            Student.objects.get(id=request.POST['delete']).delete()
        else:
            return HttpResponse("Id Does not exist")
    return HttpResponse("Data Deleted Successfully")


def delete_advanced_profile(request):
    if request.method == "POST":
        print(request.POST['delete'])
        if Student.objects.get(id=request.POST['delete']):
            s = Student.objects.get(id=request.POST['delete'])
            s.father_name = ""
            s.mother_name = ""
            s.hall_no = 1
            s.room_no = ""
            s.save()
        else:
            return HttpResponse("Data Does Not Exist")
    return HttpResponse("Data Deleted Successfully")


def add_advanced_profile(request):
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
        # db2 = ExtraInfo()
        # db2.profile_picture = dp
        # db2.save()
    return HttpResponse("Data successfully inputed")


def add_grade(request):
    if request.method == "POST":
        try:
            roll = Student.objects.get(id=request.POST['roll'])
        except:
            return HttpResponse("Student Does Not Exist")
        sem = request.POST['sem']
        course = Course.objects.get(course_id=request.POST['course'])
        grade = request.POST['grade']

        # print(Grades.objects.filter(student_id=roll, course_id=course).count())
        if not Grades.objects.filter(student_id=roll, course_id=course).exists():
            db = Grades()
            db.student_id = roll
            db.course_id = course
            db.sem = sem
            db.grade = grade
            db.save()
        else:
            return HttpResponse("Data Already Exists")
        grades = Grades.objects.all()
        context = {
            'grades': grades,
        }
    return render(request, "ais/ais.html", context)


def delete_grade(request):
    print(request.POST['delete'])
    data = request.POST['delete']
    d = data.split("-")
    id = d[0]
    course = d[1]
    sem = int(d[2])
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
    return HttpResponse("Data Entered Successfully")


def add_timetable(request):
    if(request.method == "POST"):
        file = request.POST['file']
        db = Timetable()
        db.time_table = file
        db.save()
    # timetable = Timetable.objects.all()
    # context = {
    #     'timetable': timetable,
    # }
    return HttpResponse("Added")


def add_exam_timetable(request):
    if(request.method == "POST"):
        file = request.POST['file']
        db = Exam_timetable()
        db.exam_time_table = file
        db.save()
    return HttpResponse("Data Deleted SuccessFully")


def delete_timetable(request):
    if request.method == "POST":
        data = request.POST['delete']
        t = Timetable.objects.get(time_table=data)
        t.delete()
    return HttpResponse("TimeTable Deleted")
