import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Max
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

# from applications.academic_procedures.models import Register
from applications.academic_information.models import Course, Student
from applications.globals.models import DepartmentInfo, Designation, ExtraInfo

from .models import BranchChange, FinalRegistrations, Register

# from . forms import AddDropCourseForm

# Create your views here.


@login_required(login_url='/accounts/login')
def academic_procedures(request):
    current_user = get_object_or_404(User, username=request.user.username)
    user_details = ExtraInfo.objects.all().filter(user=current_user).first()
    user_type = Designation.objects.all().filter(name=user_details.designation).first()
    if user_type.name != 'student':
        return HttpResponseRedirect('/academic-procedures/acad_person')

    student = Student.objects.all().filter(id=user_details.id).first()
    # Fuction Call to get the current semster of the Student
    user_sem = get_user_semester(user_details.id)

    registered_or_not = Register.objects.all().filter(student_id=student).first()
    # Fucntio call to get the current user's branch
    user_branch = get_user_branch(user_details)
    user_sem = 2

    get_courses = Course.objects.all().filter(sem=(user_sem+1))
    # Fucntion Call to get the courses related to the branch
    branch_courses = get_branch_courses(get_courses, user_branch)
    details = {
            'current_user': current_user,
            'user_sem': user_sem,
            'check_pre_register': registered_or_not
            }
    final_register = Register.objects.all().filter(student_id=user_details.id)
    final_register_count = FinalRegistrations.objects.all().filter(student_id=user_details.id)

    # Branch Change Code starts here
    change_branch = apply_branch_change(request)
    return render(
        request, '../templates/academic_procedures/academic.html', {
                                                                'details': details,
                                                                'courses_list': branch_courses,
                                                                'final_register': final_register,
                                                                'final_count': final_register_count,
                                                                'change_branch': change_branch
                                                                }
        )


# function to get user semester
def get_user_semester(roll_no):
    roll = str(roll_no)
    roll = int(roll[:4])
    now = datetime.datetime.now()
    year, month = now.year, int(now.month)
    user_year = int(year) - roll
    sem = 'odd'
    if month >= 7 and month <= 12:
        sem = 'odd'
    else:
        sem = 'even'
    if sem == 'odd':
        return user_year * 2 + 1
    else:
        return user_year * 2


def get_branch_courses(courses, branch):
    course_list = []
    print(courses, branch)
    for course in courses:
        if branch[:2].lower() == course.course_id[:2].lower() and len(course.course_id) >= 5:
            course_list.append(course)
        if len(course.course_id) > 5:
            course_list.append(course)
    return course_list


def get_user_branch(user_details):
    return user_details.department.name


@login_required(login_url='/accounts/login')
def add_course(request):
    current_user = get_object_or_404(User, username=request.user.username)
    user_details = ExtraInfo.objects.all().filter(user=current_user).first()
    # Fuction Call to get the current semster of the Student
    user_sem = get_user_semester(user_details.id)
    user_sem = 3
    get_courses = Course.objects.all().filter(sem=user_sem)
    print(get_courses, user_sem)
    details = {'current_user': current_user, 'user_sem': user_sem}
    return render(
        request,
        '../templates/academic_procedures/addCourse.html',
        {'details': details, 'courses_list': get_courses})


def register(request):
    if request.method == 'POST':
        try:
            current_user = get_object_or_404(User, username=request.POST.get('user'))
            current_user = ExtraInfo.objects.all().filter(user=current_user).first()
            current_user = Student.objects.all().filter(id=current_user.id).first()
            # current_user = get_object_or_404(ExtraInfo, user=current_user.username)
            values_length = 0
            values_length = len(request.POST.getlist('choice'))
            # Get the semester for the registration
            sem = request.POST.get('semester')
            for x in range(values_length):
                for key, values in request.POST.lists():
                    if (key == 'choice'):
                        last_id = Register.objects.all().aggregate(Max('r_id'))
                        print(last_id)

                        try:
                            last_id = last_id['r_id__max']+1
                        except:
                            last_id = 1
                        course_id = get_object_or_404(Course, course_id=values[x])
                        p = Register(
                            r_id=last_id,
                            course_id=course_id,
                            student_id=current_user,
                            semester=sem
                            )
                        p.save()
                    else:
                        continue
            messages.info(request, 'Pre-Registration Successful')
            return HttpResponseRedirect('/academic-procedures/main')
        except:
            return HttpResponseRedirect('/academic-procedures/main')
    else:
        print('not okay')
        return HttpResponseRedirect('/academic-procedures/main')


def final_register(request):
    if request.method == 'POST':
        current_user = get_object_or_404(User, username=request.user.username)
        extraInfo_user = ExtraInfo.objects.all().filter(user=current_user).first()
        current_user = Student.objects.all().filter(id=extraInfo_user.id).first()
        # Fuction Call to get the current semster of the Student
        user_sem = get_user_semester(extraInfo_user.id)
        p = FinalRegistrations(
            reg_id=extraInfo_user,
            semester=user_sem+1,
            student_id=current_user,
            registration=True
            )
        p.save()
        messages.info(request, 'Registration Successful')
    return HttpResponseRedirect('/academic-procedures/main')


@login_required(login_url='/accounts/login')
def drop_course(request):
    pass


@login_required(login_url='/accounts/login')
def apply_branch_change(request):
    # Get all the departments
    branch_list = DepartmentInfo.objects.all()
    branches = []

    # Get the current logged in user
    student = User.objects.all().filter(username=request.user).first()

    # Get the current logged in user's cpi
    extraInfo_user = ExtraInfo.objects.all().filter(user=student).first()
    cpi_data = Student.objects.all().filter(id=extraInfo_user.id).first()
    for i in range(len(branch_list)):
        branch_cut = branch_list[i].name
        branches.append(branch_cut)

    label_for_change = False

    semester = get_user_semester(extraInfo_user.id)

    if cpi_data.cpi >= 8 and semester >= 1 and semester <= 2:
        label_for_change = True

    context = {
            'branches': branches,
            'student': student,
            'cpi_data': cpi_data,
            'label_for_change': label_for_change,
        }
    return context


def branch_change_request(request):
    if request.method == 'POST':
        current_user = get_object_or_404(User, username=request.user.username)
        extraInfo_user = ExtraInfo.objects.all().filter(user=current_user).first()
        student = Student.objects.all().filter(id=extraInfo_user.id).first()
        department = DepartmentInfo.objects.all().filter(name=request.POST['change']).first()
        print(department)
        change_save = BranchChange(
            branches=department,
            user=student
            )
        change_save.save()
        messages.info(request, 'Apply for branch change successfull')
        return HttpResponseRedirect('/academic-procedures/main')
    else:
        messages.info(request, 'Unable to proceed')
        return HttpResponseRedirect('/academic-procedures/main')
    return HttpResponseRedirect('/academic-procedures/main')


@login_required(login_url='/accounts/login')
def acad_person(request):
    change_queries = BranchChange.objects.all()
    # Total seats taken as some random value
    total_cse_seats = 100
    total_ece_seats = 100
    total_me_seats = 100

    total_cse_filled_seats = 98
    total_ece_filled_seats = 98
    total_me_filled_seats = 98

    available_cse_seats = total_cse_seats - total_cse_filled_seats
    available_ece_seats = total_ece_seats - total_ece_filled_seats
    available_me_seats = total_me_seats - total_me_filled_seats

    initial_branch = []
    change_branch = []
    available_seats = []
    applied_by = []
    cpi = []

    for i in change_queries:
        applied_by.append(i.user.id)
        change_branch.append(i.branches.name)
        students = Student.objects.all().filter(id=i.user.id).first()
        user_branch = ExtraInfo.objects.all().filter(id=students.id.id).first()
        initial_branch.append(user_branch.department.name)
        cpi.append(students.cpi)
        if i.branches.name == 'cse':
            available_seats.append(available_cse_seats)
        elif i.branches.name == 'ece':
            available_seats.append(available_ece_seats)
        elif i.branches.name == 'me':
            available_seats.append(available_me_seats)
    lists = zip(applied_by, change_branch, initial_branch, available_seats, cpi)
    tag = False
    print(lists)
    if len(initial_branch) > 0:
        tag = True
    context = {
        'list': lists,
        'total': len(initial_branch),
        'tag': tag
    }
    print(context)
    return render(
        request,
        '../templates/academic_procedures/academicadmin.html',
        {'context': context, 'lists': lists})


@login_required(login_url='/acounts/login')
def approve_branch_change(request):
    if request.method == 'POST':
        values_length = 0
        for key, values in request.POST.lists():
            values_length = len(values)
            break
        choices = []
        branches = []
        for i in range(values_length):
            for key, values in request.POST.lists():
                if key == 'branch':
                    branches.append(values[i])
                if key == 'choice':
                    choices.append(values[i])
                else:
                    continue
                    print(key, values[i])
        for i in range(len(branches)):
            get_student = ExtraInfo.objects.all().filter(id=choices[i][:7])
            get_student = get_student[0]
            branch = DepartmentInfo.objects.all().filter(name=branches[i])
            get_student.department = branch[0]
            get_student.save()
            student = Student.objects.all().filter(id=choices[i][:7]).first()
            change = BranchChange.objects.all().filter(user=student)
            change = change[0]
            change.delete()
        messages.info(request, 'Apply for branch change successfull')
        return HttpResponseRedirect('/academic-procedures/main')

    else:
        messages.info(request, 'Unable to proceed')
        return HttpResponseRedirect('/academic-procedures/main')
