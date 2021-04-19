from django.http import request
from django.shortcuts import render, HttpResponse
from django.http import HttpResponse, HttpResponseRedirect
import itertools
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Programme, Discipline, Curriculum, Semester, Course, Batch, CourseSlot
from .forms import ProgrammeForm, DisciplineForm, CurriculumForm, SemesterForm, CourseForm, BatchForm, CourseSlotForm
# from applications.academic_information.models import Student
from applications.globals.models import (DepartmentInfo, Designation,
                                         ExtraInfo, Faculty, HoldsDesignation)

# ------------module-functions---------------#

@login_required(login_url='/accounts/login')
def programme_curriculum(request):
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        # obj = Student.objects.get(id = user_details.id)
        # print(obj.programme)
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        return HttpResponseRedirect('/programme_curriculum/admin_mainpage')



# ------------all-user-functions---------------#


def main_page(request):
    """ display the main page """
    return render(request, 'programme_curriculum/mainpage.html')

def view_all_programmes(request):
    """ views all programmes, both working and obselete curriculums of all programmes """

    ug = Programme.objects.filter(category='UG')
    pg = Programme.objects.filter(category='PG')
    phd = Programme.objects.filter(category='PHD')
    programmes = []
    for (ug, pg, phd) in itertools.zip_longest(ug, pg, phd, fillvalue=""):
        programmes.append([ug, pg, phd])

    return render(request, 'programme_curriculum/view_all_programmes.html', {'programmes': programmes})


def view_curriculums_of_a_programme(request, programme_id):
    """ views all the curriculums of a specfic programme """

    program = Programme.objects.get(id=programme_id)
    curriculums = Programme.get_curriculums_objects(program)
    batches = []
    for curriculum in curriculums:
        batches.append([Curriculum.get_batches(curriculum)])
    working_curriculums = curriculums.filter(working_curriculum=1)
    past_curriculums = curriculums.filter(working_curriculum=0)

    return render(request,'programme_curriculum/view_curriculums_of_a_programme.html', {'program': program, 'past_curriculums': past_curriculums, 'working_curriculums': working_curriculums})


def view_all_working_curriculums(request):
    """ views all the working curriculums offered by the institute """
    
    curriculums = Curriculum.objects.filter(working_curriculum=1)
    return render(request,'programme_curriculum/view_all_working_curriculums.html',{'curriculums':curriculums})


# def view_working_curriculums_of_a_program(request, programme_id):
#     """ views all the working curriculums of a specfic programme """
    
#     program = Programme.objects.get(id=programme_id)
#     working_curriculums = Programme.get_curriculums_objects(program).filter(working_curriculum=1)
#     return render(request,'programme_curriculum/view_working_curriculums_of_a_program.html',{'program': program, 'working_curriculums':working_curriculums})


def view_semesters_of_a_curriculum(request, curriculum_id):
    """ gets all the semesters of a specfic curriculum """

    curriculum = Curriculum.objects.get(id=curriculum_id)
    semesters = Curriculum.get_semesters_objects(curriculum)
    semester_slots = []
    # print('----')
    for sem in semesters:
        a = list(Semester.get_courseslots_objects(sem))
        semester_slots.append(a)
        # print (a)

    
    # print(curriculum)
    # print(semesters)
    # print('----')
    print(semester_slots)
    print('----')
    # print(transpose_semester_slots)
    # for course_slots in semester_slots:
    #     for slot in course_slots:
    #         print(slot)


    max_length = 0
    for course_slots in semester_slots:
        max_length = max(max_length, len(course_slots))

    for course_slots in semester_slots:
        course_slots += [""] * (max_length - len(course_slots))
    
    print(semester_slots)
    
    transpose_semester_slots = list(zip(*semester_slots))

    print('----')

    print(transpose_semester_slots)
    
    return render(request, 'programme_curriculum/view_semesters_of_a_curriculum.html', {'curriculum': curriculum, 'semesters': semesters, 'semester_slots': transpose_semester_slots})


def view_a_semester_of_a_curriculum(request, semester_id):
    """ views a specfic semester of a specfic curriculum """

    semester = Semester.objects.get(id=semester_id)
    course_slots = Semester.get_courseslots_objects(semester)
    # courses_list = []
    # for course_slot in course_slots:
    #     courses_list.append([CourseSlot.get_courses_objects(course_slot)])
    return render(request, 'programme_curriculum/view_a_semester_of_a_curriculum.html', {'semesters': semester, 'course_slots': course_slots})


# def view_curriculum_courses(request, curriculum_id):
#     """ views all the courses offered by a specfic program """
#     return HttpResponse()

# def view_semester_courses(request, semester_id):
#     """ views all the courses offered by a specfic semester """
#     return HttpResponse()

# def view_semester_course_slots(request, semester_id):
#     """ views all the course slots of a specfic semester """
#     return HttpResponse()

def view_a_courseslot(request, courseslot_id):
    """ view a course slot """
    course_slot = CourseSlot.objects.get(id=courseslot_id)
    return render(request, 'programme_curriculum/view_a_courseslot.html', {'course_slot': course_slot})

def view_all_courses(request):
    """ views all the course slots of a specfic semester """
    courses = Course.objects.all()
    return render(request, 'programme_curriculum/view_all_courses.html', {'courses': courses})

def view_a_course(request, course_id):
    """ views the details of a Course """
    course = Course.objects.get(id=course_id)
    return render(request, 'programme_curriculum/view_a_course.html', {'course': course})


# ------------Acad-Admin-functions---------------#

@login_required(login_url='/accounts/login')
def admin_main_page(request):
    """ display the main page """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass
    
    return render(request, 'programme_curriculum/acad_admin/admin_mainpage.html')

@login_required(login_url='/accounts/login')
def admin_view_all_programmes(request):
    """ views all programmes, both working and obselete curriculums of all programmes """
    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass
    
    ug = Programme.objects.filter(category='UG')
    pg = Programme.objects.filter(category='PG')
    phd = Programme.objects.filter(category='PHD')
    programmes = []
    for (ug, pg, phd) in itertools.zip_longest(ug, pg, phd, fillvalue=""):
        programmes.append([ug, pg, phd])

    return render(request, 'programme_curriculum/acad_admin/admin_view_all_programmes.html', {'programmes': programmes})

@login_required(login_url='/accounts/login')
def admin_view_curriculums_of_a_programme(request, programme_id):
    """ views all the curriculums of a specfic programme """
    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass
    
    program = Programme.objects.get(id=programme_id)
    curriculums = Programme.get_curriculums_objects(program)
    working_curriculums = curriculums.filter(working_curriculum=1)
    past_curriculums = curriculums.filter(working_curriculum=0)

    return render(request,'programme_curriculum/acad_admin/admin_view_curriculums_of_a_programme.html', {'program': program, 'past_curriculums': past_curriculums, 'working_curriculums': working_curriculums})

@login_required(login_url='/accounts/login')
def admin_view_all_working_curriculums(request):
    """ views all the working curriculums offered by the institute """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass
        
    curriculums = Curriculum.objects.filter(working_curriculum=1)
    return render(request,'programme_curriculum/acad_admin/admin_view_all_working_curriculums.html',{'curriculums':curriculums})


# def view_working_curriculums_of_a_program(request, programme_id):
#     """ views all the working curriculums of a specfic programme """
    
#     program = Programme.objects.get(id=programme_id)
#     working_curriculums = Programme.get_curriculums_objects(program).filter(working_curriculum=1)
#     return render(request,'programme_curriculum/acad_admin/admin_view_working_curriculums_of_a_program.html',{'program': program, 'working_curriculums':working_curriculums})

@login_required(login_url='/accounts/login')
def admin_view_semesters_of_a_curriculum(request, curriculum_id):
    """ gets all the semesters of a specfic curriculum """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass
    

    curriculum = Curriculum.objects.get(id=curriculum_id)
    semesters = Curriculum.get_semesters_objects(curriculum)
    semester_slots = []
    # print('----')
    for sem in semesters:
        a = list(Semester.get_courseslots_objects(sem))
        semester_slots.append(a)
        # print (a)

    
    # print(curriculum)
    # print(semesters)
    # print('----')
    print(semester_slots)
    print('----')
    # print(transpose_semester_slots)
    # for course_slots in semester_slots:
    #     for slot in course_slots:
    #         print(slot)


    max_length = 0
    for course_slots in semester_slots:
        max_length = max(max_length, len(course_slots))

    for course_slots in semester_slots:
        course_slots += [""] * (max_length - len(course_slots))
    
    print(semester_slots)
    
    transpose_semester_slots = list(zip(*semester_slots))

    print('----')

    print(transpose_semester_slots)
    return render(request, 'programme_curriculum/acad_admin/admin_view_semesters_of_a_curriculum.html', {'curriculum': curriculum, 'semesters': semesters, 'semester_slots': transpose_semester_slots})

@login_required(login_url='/accounts/login')
def admin_view_a_semester_of_a_curriculum(request, semester_id):
    """ views a specfic semester of a specfic curriculum """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass
    
    semester = Semester.objects.get(id=semester_id)
    course_slots = Semester.get_courseslots_objects(semester)
    # courses_list = []
    # for course_slot in course_slots:
    #     courses_list.append([CourseSlot.get_courses_objects(course_slot)])
    return render(request, 'programme_curriculum/acad_admin/admin_view_a_semester_of_a_curriculum.html', {'semesters': semester, 'course_slots': course_slots})


# def view_curriculum_courses(request, curriculum_id):
#     """ views all the courses offered by a specfic program """
#     return HttpResponse()

# def view_semester_courses(request, semester_id):
#     """ views all the courses offered by a specfic semester """
#     return HttpResponse()

# def view_semester_course_slots(request, semester_id):
#     """ views all the course slots of a specfic semester """
#     return HttpResponse()

@login_required(login_url='/accounts/login')
def admin_view_a_courseslot(request, courseslot_id):
    """ view a course slot """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass
    
    course_slot = CourseSlot.objects.get(id=courseslot_id)
    return render(request, 'programme_curriculum/acad_admin/admin_view_a_courseslot.html', {'course_slot': course_slot})

@login_required(login_url='/accounts/login')
def admin_view_all_courses(request):
    """ views all the course slots of a specfic semester """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass
    
    courses = Course.objects.all()
    return render(request, 'programme_curriculum/acad_admin/admin_view_all_courses.html', {'courses': courses})

@login_required(login_url='/accounts/login')
def admin_view_a_course(request, course_id):
    """ views the details of a Course """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass
    
    course = Course.objects.get(id=course_id)
    return render(request, 'programme_curriculum/acad_admin/admin_view_a_course.html', {'course': course})


@login_required(login_url='/accounts/login')
def admin_view_all_discplines(request):
    """ views the details of a Course """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass

    disciplines = Discipline.objects.all()
    return render(request, 'programme_curriculum/acad_admin/admin_view_all_disciplines.html', {'disciplines': disciplines})

    # return HttpResponse('Under Construction!')



@login_required(login_url='/accounts/login')
def admin_view_all_batches(request):
    """ views the details of a Course """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass

    batches = Batch.objects.all()
    return render(request, 'programme_curriculum/acad_admin/admin_view_all_batches.html', {'batches': batches})

    # return HttpResponse('Under Construction!')





@login_required(login_url='/accounts/login')
def add_discipline_form(request):

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass
    
    form = DisciplineForm()
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = DisciplineForm(request.POST)  
            if form.is_valid():
                form.save()
                messages.success(request, "Added Discipline successful")
                return HttpResponse("Upload successful.")    
    return render(request, 'programme_curriculum/acad_admin/add_discipline_form.html',{'form':form})



@login_required(login_url='/accounts/login')
def edit_discipline_form(request, discipline_id):

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass
    
    discipline = Discipline.objects.get(id=discipline_id)
    form = DisciplineForm(instance=discipline)
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = DisciplineForm(request.POST, instance=discipline)  
            if form.is_valid():
                form.save()
                messages.success(request, "Updated "+ discipline.name +" successful")
                return HttpResponseRedirect("/programme_curriculum/admin_disciplines/" + str(discipline.name) + "/")  
    return render(request, 'programme_curriculum/acad_admin/add_discipline_form.html',{'form':form})





@login_required(login_url='/accounts/login')
def add_programme_form(request):

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass
    
    form = ProgrammeForm()
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = ProgrammeForm(request.POST)  

            if form.is_valid():
                form.save()
                messages.success(request, "Added successful")
                return HttpResponseRedirect('/programme_curriculum/admin_mainpage')  
    return render(request,'programme_curriculum/acad_admin/add_programme_form.html',{'form':form, 'submitbutton': submitbutton})


@login_required(login_url='/accounts/login')
def edit_programme_form(request, programme_id):

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass
    
    programme = Programme.objects.get(id=programme_id)
    form = ProgrammeForm(instance=programme)
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = ProgrammeForm(request.POST, instance=programme)  
            if form.is_valid():
                form.save()
                messages.success(request, "Updated "+ programme.name +" successful")
                return HttpResponseRedirect("/programme_curriculum/admin_programmes/")  
    return render(request, 'programme_curriculum/acad_admin/add_programme_form.html',{'form':form, 'submitbutton': submitbutton})






@login_required(login_url='/accounts/login')
def add_curriculum_form(request):

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass
    
    form = CurriculumForm()
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = CurriculumForm(request.POST)  
            if form.is_valid():
                no_of_semester = form.cleaned_data['no_of_semester']
                print(form)
                print(no_of_semester)
                form.save()
                curriculum = Curriculum.objects.all().last()
                for semester_no in range(1, no_of_semester+1):
                    NewSemester = Semester(curriculum, semester_no)
                    NewSemester.save()
                messages.success(request, "Added successful")
                return HttpResponseRedirect('/programme_curriculum/admin_mainpage')

    return render(request, 'programme_curriculum/acad_admin/add_curriculum_form.html',{'form':form, 'submitbutton': submitbutton})


@login_required(login_url='/accounts/login')
def edit_curriculum_form(request, curriculum_id):

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass
    
    # INCOMPLETE
    curriculum = Curriculum.objects.get(id=curriculum_id)
    form = CurriculumForm(instance=curriculum)
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = CurriculumForm(request.POST, instance=curriculum)
            if form.is_valid():
                form_no_of_semester = form.cleaned_data['no_of_semester']
                print(curriculum)
                form.save()
                if(curriculum.no_of_semester < form_no_of_semester):
                    for semester_no in range(max(1, curriculum.no_of_semester), form_no_of_semester+1):
                        NewSemester = Semester(curriculum, semester_no)
                        print(NewSemester)
                        # NewSemester.save()

    return render(request, 'programme_curriculum/acad_admin/add_curriculum_form.html',{'form':form,  'submitbutton': submitbutton})

@login_required(login_url='/accounts/login')
def add_course_form(request):

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass
    
    form = CourseForm()
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = CourseForm(request.POST)  
            if form.is_valid():
                form.save()
                messages.success(request, "Added successful")
                # return HttpResponseRedirect("/programme_curriculum/admin_course/")

    return render(request,'programme_curriculum/acad_admin/add_course_form.html',{'form':form})

@login_required(login_url='/accounts/login')
def update_course_form(request,course_id):

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass
    
    course = Course.objects.get(id=course_id)
    form = CourseForm(instance=course)
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = CourseForm(request.POST, instance=course)  
            if form.is_valid():
                form.save()
                messages.success(request, "Updated "+ course.name +" successful")
                return HttpResponseRedirect("/programme_curriculum/admin_course/" + str(course_id) + "/")  

    return render(request,'programme_curriculum/acad_admin/add_course_form.html',{'course':course, 'form':form, 'submitbutton': submitbutton})



@login_required(login_url='/accounts/login')
def add_courseslot_form(request):
    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass
    
    form = CourseForm()
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = CourseForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Added Course Slot successful")
                return HttpResponseRedirect('/programme_curriculum/admin_mainpage/')
    return render(request, 'programme_curriculum/acad_admin/add_courseslot_form.html',{'form':form, 'submitbutton': submitbutton})
    # return HttpResponse('Under Construction!')

@login_required(login_url='/accounts/login')
def edit_courselot_form(request, courseslot_id):
    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass
    
    courseslot = CourseSlot.objects.get(id=courseslot_id)
    form = CourseForm(instance=courseslot)
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = CourseForm(request.POST, instance=courseslot)  
            if form.is_valid():
                form.save()
                messages.success(request, "Updated"+ courseslot.name +"successful")
                return HttpResponseRedirect("/programme_curriculum/admin_courseslot/" + str(courseslot.id) + "/")  

    return render(request,'programme_curriculum/acad_admin/add_courseslot_form.html',{'courseslot':courseslot, 'form':form, 'submitbutton':submitbutton})

    # return HttpResponse('Under Construction!')

@login_required(login_url='/accounts/login')
def add_batch_form(request):
    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass
    
    form = BatchForm()
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = BatchForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Added Batch successful")
                return HttpResponseRedirect('/programme_curriculum/admin_batches/')
    return render(request, 'programme_curriculum/acad_admin/add_batch_form.html',{'form':form, 'submitbutton': submitbutton})
    
    # return HttpResponse('Under Construction!')

@login_required(login_url='/accounts/login')
def edit_batch_form(request, batch_id):
    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass
    
    batch = Batch.objects.get(id=batch_id)
    form = BatchForm(instance=batch)
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = BatchForm(request.POST, instance=batch)  
            if form.is_valid():
                form.save()
                messages.success(request, "Updated "+ batch.name +" successful")
                return HttpResponseRedirect("/programme_curriculum/admin_batches/")  

    return render(request,'programme_curriculum/acad_admin/add_batch_form.html',{'batch':batch, 'form':form, 'submitbutton':submitbutton})
    
    # return HttpResponse('Under Construction!')

@login_required(login_url='/accounts/login')
def add_semester_form(request):
    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass
    
    
    return HttpResponse('Site Under Construction!')

@login_required(login_url='/accounts/login')
def edit_semesters_form(request):
    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/mainpage/')
    elif str(request.user) == "acadadmin" :
        pass
    
    
    return HttpResponse('Site Under Construction!')























