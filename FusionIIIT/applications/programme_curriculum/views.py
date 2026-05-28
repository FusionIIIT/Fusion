from django.db.models.query_utils import Q
from django.http import request
from django.shortcuts import get_object_or_404, render, HttpResponse
from django.http import HttpResponse, HttpResponseRedirect
import itertools
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Programme, Discipline, Curriculum, Semester, Course, Batch, CourseSlot
from .forms import ProgrammeForm, DisciplineForm, CurriculumForm, SemesterForm, CourseForm, BatchForm, CourseSlotForm, ReplicateCurriculumForm
from .filters import CourseFilter, BatchFilter, CurriculumFilter

# from applications.academic_information.models import Student
from applications.globals.models import (DepartmentInfo, Designation,
                                         ExtraInfo, Faculty, HoldsDesignation)

# ------------module-functions---------------#

@login_required(login_url='/accounts/login')
def programme_curriculum(request):
    """
    This function is used to Differenciate acadadmin and all other user.

    @param:
        request - contains metadata about the requested page

    @variables:
        user_details - Gets the information about the logged in user.
        des - Gets the designation about the looged in user.
    """
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        return HttpResponseRedirect('/programme_curriculum/admin_programmes')
    
    return HttpResponseRedirect('/programme_curriculum/programmes/')



# ------------all-user-functions---------------#



def view_all_programmes(request):
    """
    This function is used to display all the programmes offered by the institute.
    @variables:
        ug - UG programmes
        pg - PG programmes
        phd - PHD programmes 
    """
    ug = Programme.objects.filter(category='UG')
    pg = Programme.objects.filter(category='PG')
    phd = Programme.objects.filter(category='PHD')


    return render(request, 'programme_curriculum/view_all_programmes.html', {'ug': ug, 'pg': pg, 'phd': phd})


def view_curriculums_of_a_programme(request, programme_id):
    """
    This function is used to Display Curriculum of a specific Programmes.

    @param:
        programme_id - Id of a specific programme
        
    @variables:
        curriculums - Curriculums of a specific programmes
        batches - List of batches for curriculums
        working_curriculum - Curriculums that are affective
        past_curriculum - Curriculums thet are obsolete
    """
    program = get_object_or_404(Programme, Q(id=programme_id))
    curriculums = program.curriculums

    curriculumfilter = CurriculumFilter(request.GET, queryset=curriculums)

    curriculums = curriculumfilter.qs

    working_curriculums = curriculums.filter(working_curriculum=1)
    past_curriculums = curriculums.filter(working_curriculum=0)

    return render(request,'programme_curriculum/view_curriculums_of_a_programme.html', {'program': program, 'past_curriculums': past_curriculums, 'working_curriculums': working_curriculums, 'curriculumfilter': curriculumfilter})


def view_all_working_curriculums(request):
    """ views all the working curriculums offered by the institute """
    
    curriculums = Curriculum.objects.filter(working_curriculum=1)

    curriculumfilter = CurriculumFilter(request.GET, queryset=curriculums)

    curriculums = curriculumfilter.qs
    return render(request,'programme_curriculum/view_all_working_curriculums.html',{'curriculums':curriculums, 'curriculumfilter': curriculumfilter})



def view_semesters_of_a_curriculum(request, curriculum_id):
    """
    This function is used to Display all Semester of a Curriculum.

    @param:
        curriculum_id - Id of a specific curriculum
        
    @variables:
        transpose_semester_slots - semester_slots 2D list is transpose for viewing in HTML <table>.
        semester_credits - Total Credits for each semester.
    """
    curriculum = get_object_or_404(Curriculum, Q(id=curriculum_id))
    semesters = curriculum.semesters
    semester_slots = []
    for sem in semesters:
        a = list(sem.courseslots)
        semester_slots.append(a)

    max_length = 0
    for course_slots in semester_slots:
        max_length = max(max_length, len(course_slots))

    for course_slots in semester_slots:
        course_slots += [""] * (max_length - len(course_slots))

    semester_credits = []

    for semester in semesters:
        credits_sum = 0
        for course_slot in semester.courseslots:
            max_credit = 0
            courses = course_slot.courses.all()
            for course in courses:
                max_credit = max(max_credit, course.credit)
            credits_sum = credits_sum + max_credit
        semester_credits.append(credits_sum)

    print (semester_credits)
    
    transpose_semester_slots = list(zip(*semester_slots))

    return render(request, 'programme_curriculum/view_semesters_of_a_curriculum.html', {'curriculum': curriculum, 'semesters': semesters, 'semester_slots': transpose_semester_slots, 'semester_credits': semester_credits})


def view_a_semester_of_a_curriculum(request, semester_id):
    """ views a specfic semester of a specfic curriculum """

    semester = get_object_or_404(Semester, Q(id=semester_id))
    course_slots = semester.courseslots

    return render(request, 'programme_curriculum/view_a_semester_of_a_curriculum.html', {'semester': semester, 'course_slots': course_slots})


def view_a_courseslot(request, courseslot_id):
    """ view a course slot """
    course_slot = get_object_or_404(CourseSlot, Q(id=courseslot_id))
    return render(request, 'programme_curriculum/view_a_courseslot.html', {'course_slot': course_slot})


def view_all_courses(request):
    """ views all the course slots of a specfic semester """
    courses = Course.objects.all()

    coursefilter = CourseFilter(request.GET, queryset=courses)

    courses = coursefilter.qs
    return render(request, 'programme_curriculum/view_all_courses.html', {'courses': courses, 'coursefilter': coursefilter})


def view_a_course(request, course_id):
    """ views the details of a Course """
    course = get_object_or_404(Course, Q(id=course_id))
    return render(request, 'programme_curriculum/view_a_course.html', {'course': course})


def view_all_discplines(request):
    """ views the details of a Course """

    disciplines = Discipline.objects.all()
    return render(request, 'programme_curriculum/view_all_disciplines.html', {'disciplines': disciplines})


def view_all_batches(request):
    """ views the details of a Course """

    batches = Batch.objects.all().order_by('year')

    batchfilter = BatchFilter(request.GET, queryset=batches)

    batches = batchfilter.qs

    finished_batches = batches.filter(running_batch=False)

    batches = batches.filter(running_batch=True)

    return render(request, 'programme_curriculum/view_all_batches.html', {'batches': batches, 'finished_batches': finished_batches, 'batchfilter': batchfilter})




# ------------Acad-Admin-functions---------------#


@login_required(login_url='/accounts/login')
def admin_view_all_programmes(request):
    """
    This function is used to display all the programmes offered by the institute.
    @variables:
        ug - UG programmes
        pg - PG programmes
        phd - PHD programmes 
    """    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    
    ug = Programme.objects.filter(category='UG')
    pg = Programme.objects.filter(category='PG')
    phd = Programme.objects.filter(category='PHD')

    return render(request, 'programme_curriculum/acad_admin/admin_view_all_programmes.html', {'ug': ug, 'pg': pg, "phd": phd})


@login_required(login_url='/accounts/login')
def admin_view_curriculums_of_a_programme(request, programme_id):
    """
    This function is used to Display Curriculum of a specific Programmes.

    @param:
        programme_id - Id of a specific programme
        
    @variables:
        curriculums - Curriculums of a specific programmes
        batches - List of batches for curriculums
        working_curriculum - Curriculums that are affective
        past_curriculum - Curriculums thet are obsolete
    """    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    
    program = get_object_or_404(Programme, Q(id=programme_id))
    curriculums = program.curriculums

    curriculumfilter = CurriculumFilter(request.GET, queryset=curriculums)

    curriculums = curriculumfilter.qs

    working_curriculums = curriculums.filter(working_curriculum=1)
    past_curriculums = curriculums.filter(working_curriculum=0)

    return render(request,'programme_curriculum/acad_admin/admin_view_curriculums_of_a_programme.html', {'program': program, 'past_curriculums': past_curriculums, 'working_curriculums': working_curriculums, 'curriculumfilter': curriculumfilter})


@login_required(login_url='/accounts/login')
def admin_view_all_working_curriculums(request):
    """ views all the working curriculums offered by the institute """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
        
    curriculums = Curriculum.objects.filter(working_curriculum=1)

    curriculumfilter = CurriculumFilter(request.GET, queryset=curriculums)

    curriculums = curriculumfilter.qs

    return render(request,'programme_curriculum/acad_admin/admin_view_all_working_curriculums.html',{'curriculums':curriculums, 'curriculumfilter': curriculumfilter})


@login_required(login_url='/accounts/login')
def admin_view_semesters_of_a_curriculum(request, curriculum_id):
    """ gets all the semesters of a specfic curriculum """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    
    curriculum = get_object_or_404(Curriculum, Q(id=curriculum_id))
    semesters = curriculum.semesters
    semester_slots = []
    for sem in semesters:
        a = list(sem.courseslots)
        semester_slots.append(a)

    max_length = 0
    for course_slots in semester_slots:
        max_length = max(max_length, len(course_slots))

    for course_slots in semester_slots:
        course_slots += [""] * (max_length - len(course_slots))

    semester_credits = []

    for semester in semesters:
        credits_sum = 0
        for course_slot in semester.courseslots:
            max_credit = 0
            courses = course_slot.courses.all()
            for course in courses:
                max_credit = max(max_credit, course.credit)
            credits_sum = credits_sum + max_credit
        semester_credits.append(credits_sum)

    print (semester_credits)
    
    transpose_semester_slots = list(zip(*semester_slots))

    all_batches = Batch.objects.filter(running_batch=True).exclude(curriculum=curriculum_id).order_by('year')

    return render(request, 'programme_curriculum/acad_admin/admin_view_semesters_of_a_curriculum.html', {'curriculum': curriculum, 'semesters': semesters, 'semester_slots': transpose_semester_slots, 'semester_credits': semester_credits, 'all_batches':all_batches})


@login_required(login_url='/accounts/login')
def admin_view_a_semester_of_a_curriculum(request, semester_id):
    """
    This function is used to Display all Semester of a Curriculum.

    @param:
        curriculum_id - Id of a specific curriculum
        
    @variables:
        transpose_semester_slots - semester_slots 2D list is transpose for viewing in HTML <table>.
        semester_credits - Total Credits for each semester.
    """
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    
    semester = get_object_or_404(Semester, Q(id=semester_id))
    course_slots = semester.courseslots

    return render(request, 'programme_curriculum/acad_admin/admin_view_a_semester_of_a_curriculum.html', {'semester': semester, 'course_slots': course_slots})



@login_required(login_url='/accounts/login')
def admin_view_a_courseslot(request, courseslot_id):
    """ view a course slot """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    
    edit = request.POST.get('edit', -1)
    course_slot = get_object_or_404(CourseSlot, Q(id=courseslot_id))
    if edit == course_slot.id:
        return render(request, 'programme_curriculum/acad_admin/admin_edit_semesters_view_a_courseslot.html', {'course_slot': course_slot})
    
    return render(request, 'programme_curriculum/acad_admin/admin_view_a_courseslot.html', {'course_slot': course_slot})


@login_required(login_url='/accounts/login')
def admin_view_all_courses(request):
    """ views all the course slots of a specfic semester """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    

    courses = Course.objects.all()

    coursefilter = CourseFilter(request.GET, queryset=courses)

    courses = coursefilter.qs

    return render(request, 'programme_curriculum/acad_admin/admin_view_all_courses.html', {'courses': courses, 'coursefilter': coursefilter})


@login_required(login_url='/accounts/login')
def admin_view_a_course(request, course_id):
    """ views the details of a Course """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    
    course = get_object_or_404(Course, Q(id=course_id))
    return render(request, 'programme_curriculum/acad_admin/admin_view_a_course.html', {'course': course})


@login_required(login_url='/accounts/login')
def admin_view_all_discplines(request):
    """ views the details of a Course """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass

    disciplines = Discipline.objects.all()
    return render(request, 'programme_curriculum/acad_admin/admin_view_all_disciplines.html', {'disciplines': disciplines})


@login_required(login_url='/accounts/login')
def admin_view_all_batches(request):
    """ views the details of a Course """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    
    batches = Batch.objects.all().order_by('year')

    batchfilter = BatchFilter(request.GET, queryset=batches)

    batches = batchfilter.qs

    finished_batches = batches.filter(running_batch=False)

    batches = batches.filter(running_batch=True)


    return render(request, 'programme_curriculum/acad_admin/admin_view_all_batches.html', {'batches': batches, 'finished_batches': finished_batches, 'batchfilter': batchfilter})


@login_required(login_url='/accounts/login')
def add_discipline_form(request):

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
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
                return HttpResponseRedirect('/programme_curriculum/admin_disciplines/')    
    return render(request, 'programme_curriculum/acad_admin/add_discipline_form.html',{'form':form})


@login_required(login_url='/accounts/login')
def edit_discipline_form(request, discipline_id):

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    
    discipline = get_object_or_404(Discipline, Q(id=discipline_id))
    form = DisciplineForm(instance=discipline)
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = DisciplineForm(request.POST, instance=discipline)  
            if form.is_valid():
                form.save()
                messages.success(request, "Updated "+ discipline.name +" successful")
                return HttpResponseRedirect("/programme_curriculum/admin_disciplines/")  
    return render(request, 'programme_curriculum/acad_admin/add_discipline_form.html',{'form':form})


@login_required(login_url='/accounts/login')
def add_programme_form(request):

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    
    form = ProgrammeForm()
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = ProgrammeForm(request.POST)  

            if form.is_valid():
                form.save()
                programme = Programme.objects.last()
                messages.success(request, "Added successful")
                return HttpResponseRedirect('/programme_curriculum/admin_curriculums/' + str(programme.id) + '/')  
    return render(request,'programme_curriculum/acad_admin/add_programme_form.html',{'form':form, 'submitbutton': submitbutton})


@login_required(login_url='/accounts/login')
def edit_programme_form(request, programme_id):

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    
    programme = get_object_or_404(Programme, Q(id=programme_id))
    form = ProgrammeForm(instance=programme)
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = ProgrammeForm(request.POST, instance=programme)  
            if form.is_valid():
                form.save()
                messages.success(request, "Updated "+ programme.name +" successful")
                return HttpResponseRedirect('/programme_curriculum/admin_curriculums/' + str(programme.id) + '/')  
    return render(request, 'programme_curriculum/acad_admin/add_programme_form.html',{'form':form, 'submitbutton': submitbutton})


@login_required(login_url='/accounts/login')
def add_curriculum_form(request):
    """
    This function is used to add Curriculum and Semester into Curriculum and Semester table.
        
    @variables:
        no_of_semester - Get number of Semesters from form.
        NewSemester - For initializing a new semester.
    """
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    

    programme_id = request.GET.get('programme_id', -1)
    form = CurriculumForm(initial={'programme': programme_id})
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = CurriculumForm(request.POST)  
            if form.is_valid():

                curriculum = form.save(commit=False)
                curriculum.save()
                no_of_semester = curriculum.no_of_semester

                for semester_no in range(1, no_of_semester+1):
                    NewSemester = Semester(curriculum=curriculum,semester_no=semester_no)
                    NewSemester.save()

                messages.success(request, "Added successful")
                return HttpResponseRedirect('/programme_curriculum/admin_curriculum_semesters/' + str(curriculum.id) + '/')
                
    return render(request, 'programme_curriculum/acad_admin/add_curriculum_form.html',{'form':form, 'submitbutton': submitbutton})



@login_required(login_url='/accounts/login')
def edit_curriculum_form(request, curriculum_id):
    """
    This function is used to edit Curriculum and Semester into Curriculum and Semester table.
        
    @variables:
        no_of_semester - Get number of Semesters from form.
        OldSemester - For Removing dropped Semester.
        NewSemester - For initializing a new semester.
    """
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    
    curriculum = get_object_or_404(Curriculum, Q(id=curriculum_id))

    form = CurriculumForm(instance=curriculum)
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = CurriculumForm(request.POST, instance=curriculum)
            if form.is_valid():
                form.save()
                no_of_semester = int(form.cleaned_data['no_of_semester'])
                old_no_of_semester = Semester.objects.filter(curriculum=curriculum).count()
                if(old_no_of_semester != no_of_semester):
                    
                    if(old_no_of_semester > no_of_semester):
                        for semester_no in range(no_of_semester+1, old_no_of_semester+1):
                            try:
                                OldSemester = Semester.objects.filter(curriculum=curriculum).filter(semester_no=semester_no)
                                OldSemester.delete()
                            except:
                                print("Failed to remove old semester")
                                
                                
                    elif(old_no_of_semester < no_of_semester):
                        for semester_no in range(max(1, old_no_of_semester), no_of_semester+1):
                            try:
                                NewSemester = Semester(curriculum=curriculum,semester_no=semester_no)
                                NewSemester.save()
                            except:
                                print("Failed to add new semester")            

                messages.success(request, "Updated "+ curriculum.name +" successful")
                return HttpResponseRedirect('/programme_curriculum/admin_curriculum_semesters/' + str(curriculum.id) + '/')

    return render(request, 'programme_curriculum/acad_admin/add_curriculum_form.html',{'form':form,  'submitbutton': submitbutton})


@login_required(login_url='/accounts/login')
def add_course_form(request):

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    
    form = CourseForm()
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = CourseForm(request.POST)  
            if form.is_valid():
                form.save()
                course = Course.objects.last()
                messages.success(request, "Added successful")
                return HttpResponseRedirect("/programme_curriculum/admin_course/" + str(course.id) + "/")

    return render(request,'programme_curriculum/acad_admin/add_course_form.html',{'form':form})


@login_required(login_url='/accounts/login')
def update_course_form(request, course_id):

    #user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student":  # or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" 
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    
    course = get_object_or_404(Course, Q(id=course_id))
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
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    
    curriculum_id = request.GET.get('curriculum_id', -1)
    submitbutton= request.POST.get('Submit')
    semester_id = request.GET.get('semester_id', -1)
    form = CourseSlotForm(initial={'semester': semester_id})

    if submitbutton:
        if request.method == 'POST':
            form = CourseSlotForm(request.POST)
            if form.is_valid():
                form.save()
                courseslot = CourseSlot.objects.last()
                messages.success(request, "Added Course Slot successful")
                return HttpResponseRedirect('/programme_curriculum/admin_curriculum_semesters/' + str(courseslot.semester.curriculum.id) + '/')
    return render(request, 'programme_curriculum/acad_admin/add_courseslot_form.html',{'form':form, 'submitbutton': submitbutton, 'curriculum_id': curriculum_id})


@login_required(login_url='/accounts/login')
def edit_courseslot_form(request, courseslot_id):
    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    
    courseslot = get_object_or_404(CourseSlot, Q(id=courseslot_id))
    curriculum_id = courseslot.semester.curriculum.id
    form = CourseSlotForm(instance=courseslot)
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = CourseSlotForm(request.POST, instance=courseslot)  
            if form.is_valid():
                form.save()
                messages.success(request, "Updated "+ str(courseslot.name) +" successful")
                return HttpResponseRedirect('/programme_curriculum/admin_curriculum_semesters/' + str(courseslot.semester.curriculum.id) + '/')  

    return render(request,'programme_curriculum/acad_admin/add_courseslot_form.html',{'courseslot':courseslot, 'form':form, 'submitbutton':submitbutton, 'curriculum_id': curriculum_id})

def delete_courseslot(request, courseslot_id):
    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    
    courseslot = get_object_or_404(CourseSlot, Q(id=courseslot_id))
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            courseslotname = courseslot.name
            curriculum_id = courseslot.semester.curriculum.id
            courseslot.delete() 
            messages.success(request, "Deleted "+ courseslotname +" successful")
            return HttpResponseRedirect('/programme_curriculum/admin_curriculum_semesters/' + str(curriculum_id) + '/')  

    return render(request, 'programme_curriculum/view_a_courseslot.html', {'course_slot': courseslot})


@login_required(login_url='/accounts/login')
def add_batch_form(request):
    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    
    curriculum_id = request.GET.get('curriculum_id', -1)
    form = BatchForm(initial={'curriculum': curriculum_id})
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = BatchForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Added Batch successful")
                return HttpResponseRedirect('/programme_curriculum/admin_batches/')
    return render(request, 'programme_curriculum/acad_admin/add_batch_form.html',{'form':form, 'submitbutton': submitbutton})
    

@login_required(login_url='/accounts/login')
def edit_batch_form(request, batch_id):
    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    
    curriculum_id = request.GET.get('curriculum_id', -1)
    batch = get_object_or_404(Batch, Q(id=batch_id))
    if curriculum_id != -1:
        batch.curriculum = Curriculum.objects.get(id=curriculum_id)
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


@login_required(login_url='/accounts/login')
def instigate_semester(request, semester_id):
    """
    This function is used to add the semester information.
        
    @variables:
        no_of_semester - Get number of Semesters from form.
        OldSemester - For Removing dropped Semester.
        NewSemester - For initializing a new semester.
    """    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    
    
    semester = get_object_or_404(Semester, Q(id=semester_id))
    sdate = semester.start_semester
    edate = semester.end_semester
    isem = semester.instigate_semester
    info = semester.semester_info
    form = SemesterForm(initial={'start_semester': sdate ,'end_semester': edate ,'instigate_semester': isem , 'semester_info': info, })
    curriculum_id = semester.curriculum.id
    submitbutton = request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = SemesterForm(request.POST or None)
            if form.is_valid():
                semester.start_semester = form.cleaned_data['start_semester']
                semester.end_semester = form.cleaned_data['end_semester']
                semester.instigate_semester = form.cleaned_data['instigate_semester']
                semester.semester_info = form.cleaned_data['semester_info']
                semester.save()
                messages.success(request, "Instigated "+ str(semester) +" successful")
                return HttpResponseRedirect('/programme_curriculum/admin_curriculum_semesters/' + str(semester.curriculum.id) + '/')

    return render(request,'programme_curriculum/acad_admin/instigate_semester_form.html',{'semester':semester, 'form':form, 'submitbutton':submitbutton, 'curriculum_id':curriculum_id})


@login_required(login_url='/accounts/login')
def replicate_curriculum(request, curriculum_id):
    """
    This function is used to replicate the previous curriculum into a new curriculum.
        
    @variables:
        no_of_semester - For initializing the next version into a new curriculum.

    """    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if str(des.designation) == "student" or str(des.designation) == "Associate Professor" or str(des.designation) == "Professor" or str(des.designation) == "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass

    old_curriculum = get_object_or_404(Curriculum, Q(id=curriculum_id))
    programme = old_curriculum.programme
    name = old_curriculum.name
    version = int(old_curriculum.version) + 1
    working_curriculum = old_curriculum.working_curriculum
    no_of_semester = old_curriculum.no_of_semester



    form = CurriculumForm(initial={'programme': programme.id,
                                    'name': name,
                                    'version': version,
                                    'working_curriculum': working_curriculum,
                                    'no_of_semester': no_of_semester,
                                })
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = CurriculumForm(request.POST)  
            if form.is_valid():
                form.save()
                no_of_semester = int(form.cleaned_data['no_of_semester'])
                old_semesters = old_curriculum.semesters
                curriculum = Curriculum.objects.all().last()
                for semester_no in range(1, no_of_semester+1):
                    
                    NewSemester = Semester(curriculum=curriculum,semester_no=semester_no)
                    NewSemester.save()
                    for old_sem in old_semesters:
                        if old_sem.semester_no == semester_no:
                            for slot in old_sem.courseslots:
                                courses = slot.courses.all()
                                slot.pk = None
                                slot.semester = NewSemester
                                slot.save(force_insert=True)
                                slot.courses.set(courses)
                
                messages.success(request, "Added successful")
                return HttpResponseRedirect('/programme_curriculum/admin_curriculum_semesters/' + str(curriculum.id) + '/')

    return render(request, 'programme_curriculum/acad_admin/add_curriculum_form.html',{'form':form, 'submitbutton': submitbutton})