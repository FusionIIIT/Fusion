from django.db.models.query_utils import Q
from django.http import request
from django.shortcuts import get_object_or_404, render, HttpResponse,redirect
from django.http import HttpResponse, HttpResponseRedirect
# import itertools
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Programme, Discipline, Curriculum, Semester, Course, Batch, CourseSlot,NewProposalFile,Proposal_Tracking
from .forms import ProgrammeForm, DisciplineForm, CurriculumForm, SemesterForm, CourseForm, BatchForm, CourseSlotForm, ReplicateCurriculumForm,NewCourseProposalFile,CourseProposalTrackingFile
from .filters import CourseFilter, BatchFilter, CurriculumFilter
from django.db import IntegrityError
from django.utils import timezone

from notification.views import prog_and_curr_notif
# from applications.academic_information.models import Student
from applications.globals.models import (DepartmentInfo, Designation,ExtraInfo, Faculty, HoldsDesignation)
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
    user=request.user
    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" or request.session['currentDesignationSelected']== "Dean Academic":
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif 'hod' in request.session['currentDesignationSelected'].lower() :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif request.session['currentDesignationSelected'] == "acadadmin" :
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
    url='programme_curriculum/'
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if  request.session['currentDesignationSelected']== "acadadmin":
        return render(request, 'programme_curriculum/admin_programmes/')
        
    elif request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" or request.session['currentDesignationSelected']== "Dean Academic" :
        url+='faculty/'
        
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        url+='faculty/'
    notifs = request.user.notifications.all()

    ug = Programme.objects.filter(category='UG')
    pg = Programme.objects.filter(category='PG')
    phd = Programme.objects.filter(category='PHD')
    url+='view_all_programmes.html'

    return render(request, url, {'ug': ug, 'pg': pg, 'phd': phd,'notifications': notifs,})


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
    url='programme_curriculum/'
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if  request.session['currentDesignationSelected']== "acadadmin":
        return render(request, 'programme_curriculum/admin_programmes/')
        
    elif request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" or request.session['currentDesignationSelected']== "Dean Academic" :
        url+='faculty/'
        
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        url+='faculty/'
    notifs = request.user.notifications.all()
    program = get_object_or_404(Programme, Q(id=programme_id))
    curriculums = program.curriculums

    curriculumfilter = CurriculumFilter(request.GET, queryset=curriculums)

    curriculums = curriculumfilter.qs

    working_curriculums = curriculums.filter(working_curriculum=1)
    past_curriculums = curriculums.filter(working_curriculum=0)
    url+='view_curriculums_of_a_programme.html'
    return render(request,url, {'program': program, 'past_curriculums': past_curriculums, 'working_curriculums': working_curriculums, 'curriculumfilter': curriculumfilter,'notifications': notifs,})


def view_all_working_curriculums(request):
    
    """ views all the working curriculums offered by the institute """
    url='programme_curriculum/'
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if  request.session['currentDesignationSelected']== "acadadmin":
        return render(request, 'programme_curriculum/admin_programmes/')

    elif request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" or request.session['currentDesignationSelected']== "Dean Academic" :

        url+='faculty/'
    
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        url+='faculty/'
    curriculums = Curriculum.objects.filter(working_curriculum=1)
    notifs = request.user.notifications.all()
    curriculumfilter = CurriculumFilter(request.GET, queryset=curriculums)

    curriculums = curriculumfilter.qs
    return render(request,url+'view_all_working_curriculums.html',{'curriculums':curriculums, 'curriculumfilter': curriculumfilter,'notifications': notifs,})

def view_semesters_of_a_curriculum(request, curriculum_id):
    """
    This function is used to Display all Semester of a Curriculum.

    @param:
        curriculum_id - Id of a specific curriculum
        
    @variables:
        transpose_semester_slots - semester_slots 2D list is transpose for viewing in HTML <table>.
        semester_credits - Total Credits for each semester.
    """
    url='programme_curriculum/'
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if  request.session['currentDesignationSelected']== "acadadmin":
        return render(request, 'programme_curriculum/admin_programmes/')
    
        
    elif request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" or request.session['currentDesignationSelected']== "Dean Academic" :
        url+='faculty/'
        
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        url+='faculty/'
    curriculum = get_object_or_404(Curriculum, Q(id=curriculum_id))
    notifs = request.user.notifications.all()
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
    
    transpose_semester_slots = list(zip(*semester_slots))

    return render(request, url+'view_semesters_of_a_curriculum.html', {'curriculum': curriculum, 'semesters': semesters, 'semester_slots': transpose_semester_slots, 'semester_credits': semester_credits,'notifications': notifs,})


def view_a_semester_of_a_curriculum(request, semester_id):
    """ views a specfic semester of a specfic curriculum """
    url='programme_curriculum/'
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if  request.session['currentDesignationSelected']== "acadadmin":
        return render(request, 'programme_curriculum/admin_programmes/')

    elif request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" or request.session['currentDesignationSelected']== "Dean Academic" :
        url+='faculty/'
        
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        url+='faculty/'
    semester = get_object_or_404(Semester, Q(id=semester_id))
    course_slots = semester.courseslots
    notifs = request.user.notifications.all()

    return render(request, url+'view_a_semester_of_a_curriculum.html', {'semester': semester, 'course_slots': course_slots,'notifications': notifs,})


def view_a_courseslot(request, courseslot_id):
    """ view a course slot """
    url='programme_curriculum/'
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if  request.session['currentDesignationSelected']== "acadadmin":
        return render(request, 'programme_curriculum/admin_programmes/') 
    elif request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" or request.session['currentDesignationSelected']== "Dean Academic" :
        url+='faculty/'
    
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        url+='faculty/'
    course_slot = get_object_or_404(CourseSlot, Q(id=courseslot_id))
    return render(request, url+'view_a_courseslot.html', {'course_slot': course_slot,'notifications': notifs,})


def view_all_courses(request):
    """ views all the course slots of a specfic semester """
    url='programme_curriculum/'
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if  request.session['currentDesignationSelected']== "acadadmin":
        return render(request, 'programme_curriculum/admin_programmes/')
    elif request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" or request.session['currentDesignationSelected']== "Dean Academic" :

        url+='faculty/'
    
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        url+='faculty/'
    courses = Course.objects.all()
    notifs = request.user.notifications.all()

    coursefilter = CourseFilter(request.GET, queryset=courses)

    courses = coursefilter.qs
    return render(request, url+'view_all_courses.html', {'courses': courses, 'coursefilter': coursefilter,'notifications': notifs,})


def view_a_course(request, course_id):
    """ views the details of a Course """
    url='programme_curriculum/'
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if  request.session['currentDesignationSelected']== "acadadmin":
        return render(request, 'programme_curriculum/admin_programmes/')
    elif request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" or request.session['currentDesignationSelected']== "Dean Academic" :

        url+='faculty/'
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        url+='faculty/'
    course = get_object_or_404(Course, Q(id=course_id))
    notifs = request.user.notifications.all()
    return render(request, url+'view_a_course.html', {'course': course,'notifications': notifs,})


def view_all_discplines(request):
    """ views the details of a Course """
    url='programme_curriculum/'
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if  request.session['currentDesignationSelected']== "acadadmin":
        return render(request, 'programme_curriculum/admin_programmes/')
    elif request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" or request.session['currentDesignationSelected']== "Dean Academic" :
        url+='faculty/'
    
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        url+='faculty/'

    disciplines = Discipline.objects.all()
    notifs = request.user.notifications.all()
    return render(request, url+'view_all_disciplines.html', {'disciplines': disciplines,'notifications': notifs,})


def view_all_batches(request):
    """ views the details of a Course """
    url='programme_curriculum/'
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if  request.session['currentDesignationSelected']== "acadadmin":
        return render(request, 'programme_curriculum/admin_programmes/')
    elif request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" or request.session['currentDesignationSelected']== "Dean Academic" :

        url+='faculty/'
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        url+='faculty/'

    batches = Batch.objects.all().order_by('year')

    batchfilter = BatchFilter(request.GET, queryset=batches)

    batches = batchfilter.qs

    finished_batches = batches.filter(running_batch=False)

    batches = batches.filter(running_batch=True)
    notifs = request.user.notifications.all()

    return render(request, url+'view_all_batches.html', {'batches': batches, 'finished_batches': finished_batches, 'batchfilter': batchfilter,'notifications': notifs,})




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
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
    ug = Programme.objects.filter(category='UG')
    pg = Programme.objects.filter(category='PG')
    phd = Programme.objects.filter(category='PHD')

    return render(request, 'programme_curriculum/acad_admin/admin_view_all_programmes.html', {'ug': ug, 'pg': pg, "phd": phd})


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
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
    program = get_object_or_404(Programme, Q(id=programme_id))
    curriculums = program.curriculums

    curriculumfilter = CurriculumFilter(request.GET, queryset=curriculums)

    curriculums = curriculumfilter.qs

    working_curriculums = curriculums.filter(working_curriculum=1)
    past_curriculums = curriculums.filter(working_curriculum=0)

    return render(request,'programme_curriculum/acad_admin/admin_view_curriculums_of_a_programme.html', {'program': program, 'past_curriculums': past_curriculums, 'working_curriculums': working_curriculums, 'curriculumfilter': curriculumfilter})


def admin_view_all_working_curriculums(request):
    """ views all the working curriculums offered by the institute """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
        
    curriculums = Curriculum.objects.filter(working_curriculum=1)

    curriculumfilter = CurriculumFilter(request.GET, queryset=curriculums)

    curriculums = curriculumfilter.qs

    return render(request,'programme_curriculum/acad_admin/admin_view_all_working_curriculums.html',{'curriculums':curriculums, 'curriculumfilter': curriculumfilter})


def admin_view_semesters_of_a_curriculum(request, curriculum_id):
    """ gets all the semesters of a specfic curriculum """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
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
    
    transpose_semester_slots = list(zip(*semester_slots))

    all_batches = Batch.objects.filter(running_batch=True).exclude(curriculum=curriculum_id).order_by('year')

    return render(request, 'programme_curriculum/acad_admin/admin_view_semesters_of_a_curriculum.html', {'curriculum': curriculum, 'semesters': semesters, 'semester_slots': transpose_semester_slots, 'semester_credits': semester_credits, 'all_batches':all_batches})


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
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
    semester = get_object_or_404(Semester, Q(id=semester_id))
    course_slots = semester.courseslots

    return render(request, 'programme_curriculum/acad_admin/admin_view_a_semester_of_a_curriculum.html', {'semester': semester, 'course_slots': course_slots})


def admin_view_a_courseslot(request, courseslot_id):
    """ view a course slot """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
    edit = request.POST.get('edit', -1)
    course_slot = get_object_or_404(CourseSlot, Q(id=courseslot_id))
    if edit == course_slot.id:
        return render(request, 'programme_curriculum/acad_admin/admin_edit_semesters_view_a_courseslot.html', {'course_slot': course_slot})
    
    return render(request, 'programme_curriculum/acad_admin/admin_view_a_courseslot.html', {'course_slot': course_slot})


def admin_view_all_courses(request):
    """ views all the course slots of a specfic semester """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    

    courses = Course.objects.all()

    coursefilter = CourseFilter(request.GET, queryset=courses)

    courses = coursefilter.qs

    return render(request, 'programme_curriculum/acad_admin/admin_view_all_courses.html', {'courses': courses, 'coursefilter': coursefilter})


def admin_view_a_course(request, course_id):
    """ views the details of a Course """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
    course = get_object_or_404(Course, Q(id=course_id))
    return render(request, 'programme_curriculum/acad_admin/admin_view_a_course.html', {'course': course})


def admin_view_all_discplines(request):
    """ views the details of a Course """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')

    disciplines = Discipline.objects.all()
    return render(request, 'programme_curriculum/acad_admin/admin_view_all_disciplines.html', {'disciplines': disciplines})


def admin_view_all_batches(request):
    """ views the details of a Course """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
    batches = Batch.objects.all().order_by('year')

    batchfilter = BatchFilter(request.GET, queryset=batches)

    batches = batchfilter.qs

    finished_batches = batches.filter(running_batch=False)

    batches = batches.filter(running_batch=True)


    return render(request, 'programme_curriculum/acad_admin/admin_view_all_batches.html', {'batches': batches, 'finished_batches': finished_batches, 'batchfilter': batchfilter})



def add_discipline_form(request):

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
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


def edit_discipline_form(request, discipline_id):

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
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



def add_programme_form(request):

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
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



def edit_programme_form(request, programme_id):

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
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


def add_curriculum_form(request):
    """
    This function is used to add Curriculum and Semester into Curriculum and Semester table.
        
    @variables:
        no_of_semester - Get number of Semesters from form.
        NewSemester - For initializing a new semester.
    """
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    

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
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
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


def add_course_form(request):

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
    form = CourseForm()
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = CourseForm(request.POST)  
            if form.is_valid():
                new_course = form.save(commit=False)
                new_course.version=1.0
                new_course.save()
                course = Course.objects.last()
                messages.success(request, "Added successful")
                return HttpResponseRedirect("/programme_curriculum/admin_course/" + str(course.id) + "/")

    return render(request,'programme_curriculum/acad_admin/course_form.html',{'form':form,'submitbutton': submitbutton})

def update_course_form(request, course_id):
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected']== "student":
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
    course = get_object_or_404(Course, Q(id=course_id))
    previous = Course.objects.all().filter(code=course.code).order_by('version').last()
    course.version=previous.version
    version_error=''
    form = CourseForm(instance=course)
    submitbutton= request.POST.get('Submit')
    if submitbutton:
        if request.method == 'POST':
            form = CourseForm(request.POST)  
            if form.is_valid() :
                previous.latest_version=False
                previous.save()
                form.latest_version=True
                new_course = form.save(commit=False)
                add=True
                ver=0
                if(new_course.version>previous.version):
                    # Check if a course with the same values (except version, latest_version, disciplines, and pre_requisit_courses) already exists
                    old_course=Course.objects.filter(code=new_course.code, name=new_course.name, credit=new_course.credit, lecture_hours=new_course.lecture_hours, tutorial_hours=new_course.tutorial_hours, pratical_hours=new_course.pratical_hours, discussion_hours=new_course.discussion_hours, project_hours=new_course.project_hours, pre_requisits=new_course.pre_requisits, syllabus=new_course.syllabus, percent_quiz_1=new_course.percent_quiz_1, percent_midsem=new_course.percent_midsem, percent_quiz_2=new_course.percent_quiz_2, percent_endsem=new_course.percent_endsem, percent_project=new_course.percent_project, percent_lab_evaluation=new_course.percent_lab_evaluation, percent_course_attendance=new_course.percent_course_attendance, ref_books=new_course.ref_books)
                    if old_course:
                        # Check if disciplines or pre_requisit_courses have been changed
                        for i in old_course:
                            if set(form.cleaned_data['disciplines']) != set(i.disciplines.all()) or set(form.cleaned_data['pre_requisit_courses']) != set(i.pre_requisit_courses.all()):
                                add=True
                            else:
                                add=False
                                ver=i.version
                                break
                        if add:
                            new_course.save()  # Save the new course first before adding many-to-many fields
                            new_course.disciplines.set(form.cleaned_data['disciplines'])
                            new_course.pre_requisit_courses.set(form.cleaned_data['pre_requisit_courses'])
                            course = Course.objects.last()
                            messages.success(request, "Added successful")
                            return HttpResponseRedirect("/programme_curriculum/admin_course/" + str(course.id) + "/")
                        else:
                            form.add_error(None,  'A Course with the same values already exists at "Version Number '+' ' +str(ver)+'"')
                    else:
                        new_course.save()  # Save the new course first before adding many-to-many fields
                        new_course.disciplines.set(form.cleaned_data['disciplines'])
                        new_course.pre_requisit_courses.set(form.cleaned_data['pre_requisit_courses'])
                        course = Course.objects.last()
                        messages.success(request, "Added successful")
                        return HttpResponseRedirect("/programme_curriculum/admin_course/" + str(course.id) + "/")
                else:
                    version_error+=f'The version should be greater than {previous.version}'
                    
    return render(request,'programme_curriculum/acad_admin/course_form.html',{'course':course, 'form':form, 'submitbutton': submitbutton,'version_error':version_error})

def add_courseslot_form(request):
    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
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


def edit_courseslot_form(request, courseslot_id):
    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
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
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
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


def add_batch_form(request):
    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
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
    

def edit_batch_form(request, batch_id):
    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
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
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
    
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


def replicate_curriculum(request, curriculum_id):
    """
    This function is used to replicate the previous curriculum into a new curriculum.
        
    @variables:
        no_of_semester - For initializing the next version into a new curriculum.

    """    
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected']== "student" or request.session['currentDesignationSelected']== "Associate Professor" or request.session['currentDesignationSelected']== "Professor" or request.session['currentDesignationSelected']== "Assistant Professor" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif str(request.user) == "acadadmin" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        return HttpResponseRedirect('/programme_curriculum/programmes/')

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

#new

@login_required(login_url='/accounts/login')
def view_course_proposal_forms(request):
    data=""
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).last()
    
    if request.session['currentDesignationSelected']  == "Associate Professor" or request.session['currentDesignationSelected']  == "Professor" or request.session['currentDesignationSelected']  == "Assistant Professor" :
            pass
    elif request.session['currentDesignationSelected']  == "student" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif request.session['currentDesignationSelected']== "acadadmin":
        return render(request, 'programme_curriculum/admin_programmes/')
    else:
        data='Files Cannot be sent with current Designation Switch to "Professor or Assistant Professor or Associate Professor"'
    notifs = request.user.notifications.all()
    courseProposal = NewProposalFile.objects.filter(uploader=des.user,designation=request.session['currentDesignationSelected'],is_update=False)
    updatecourseProposal = NewProposalFile.objects.filter(uploader=des.user,designation=request.session['currentDesignationSelected'],is_update=True)
    
    return render(request, 'programme_curriculum/faculty/view_course_proposal_forms.html',{'courseProposals': courseProposal,'updateProposals':updatecourseProposal,'data':data,'notifications': notifs,})

@login_required(login_url='/accounts/login')
def faculty_view_all_courses(request):
    """ views all the course slots of a specfic semester """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected'] == "student" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif request.session['currentDesignationSelected'] == "acadadmin" :
        return HttpResponseRedirect('/programme_curriculum/admin_programmes')
    elif request.session['currentDesignationSelected'] == "Associate Professor" or request.session['currentDesignationSelected'] == "Professor" or request.session['currentDesignationSelected'] == "Assistant Professor":
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        pass

    courses = Course.objects.all()
    notifs = request.user.notifications.all()
    coursefilter = CourseFilter(request.GET, queryset=courses)

    courses = coursefilter.qs

    return render(request, 'programme_curriculum/faculty/faculty_view_all_courses.html', {'courses': courses, 'coursefilter': coursefilter,'notifications': notifs,})


def faculty_view_a_course(request, course_id):
    """ views the details of a Course """

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected'] == "student" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif request.session['currentDesignationSelected'] == "acadadmin" :
        return HttpResponseRedirect('/programme_curriculum/admin_programmes')
    elif request.session['currentDesignationSelected'] == "Associate Professor" or request.session['currentDesignationSelected'] == "Professor" or request.session['currentDesignationSelected'] == "Assistant Professor" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        pass
    course = get_object_or_404(Course, Q(id=course_id))
    notifs = request.user.notifications.all()
    return render(request, 'programme_curriculum/faculty/faculty_view_a_course.html', {'course': course,'notifications': notifs,})


def view_a_course_proposal_form(request,CourseProposal_id):
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()

    if request.session['currentDesignationSelected'] == "Associate Professor" or request.session['currentDesignationSelected'] == "Professor" or request.session['currentDesignationSelected'] == "Assistant Professor":
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        pass
    elif request.session['currentDesignationSelected'] == "acadadmin" :
        return HttpResponseRedirect('/programme_curriculum/admin_programmes')
    else:
        return HttpResponseRedirect('/programme_curriculum/programmes')

    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    proposalform = get_object_or_404(NewProposalFile, Q(id=CourseProposal_id))
    notifs = request.user.notifications.all()
    return render(request, 'programme_curriculum/faculty/view_a_course_proposal.html', {'proposal': proposalform,'notifications': notifs,})


def new_course_proposal_file(request):
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected'] == "Associate Professor" or request.session['currentDesignationSelected'] == "Professor" or request.session['currentDesignationSelected'] == "Assistant Professor":
        pass
    elif request.session['currentDesignationSelected'] == "acadadmin" :
        return HttpResponseRedirect('/programme_curriculum/admin_programmes')
    else:
        return HttpResponseRedirect('/programme_curriculum/programmes')
    
    uploader = request.user.extrainfo
    design=request.session['currentDesignationSelected']
    form=NewCourseProposalFile(initial={'uploader':des.user,'designation':design})
    submitbutton= request.POST.get('Submit')
    
    if submitbutton:
        if request.method == 'POST':
            form = NewCourseProposalFile(request.POST)  
            if form.is_valid():
                new_course=form.save(commit=False)
                new_course.is_read=False
                new_course.save()
                messages.success(request, "Added successful")

                return HttpResponseRedirect('/programme_curriculum/view_course_proposal_forms/')

    return render(request,'programme_curriculum/faculty/course_proposal_form.html',{'form':form,'submitbutton': submitbutton})



def filetracking(request,proposal_id):


    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected'] == "Associate Professor" or request.session['currentDesignationSelected'] == "Professor" or request.session['currentDesignationSelected'] == "Assistant Professor" or request.session['currentDesignationSelected'] == "Dean Academic":
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        pass
    elif request.session['currentDesignationSelected'] == "acadadmin":
        return HttpResponseRedirect('/programme_curriculum/admin_programmes')
    uploader = request.user.extrainfo
    design=request.session['currentDesignationSelected']
    file = get_object_or_404(NewProposalFile, Q(id=proposal_id))
    file_data=file.name+' '+file.code
    form=CourseProposalTrackingFile(initial={'current_id':file.uploader,'current_design':file.designation,'file_id':int(proposal_id)})
    
    submitbutton= request.POST.get('Submit')
    
    if submitbutton:
        if request.method == 'POST':
            form = CourseProposalTrackingFile(request.POST)
            if form.is_valid():
                try:
                    form.is_read=False
                    form.save()
                    receiver=request.POST.get('receive_id')
                    receiver_id = User.objects.get(id=receiver)
                    receiver_design=request.POST.get('receive_design')
                    receiver_des= Designation.objects.get(id=receiver_design)
                    uploader=request.POST.get('current_id')
                    uploader_design=request.POST.get('current_design')
                    
                    data='Received as '+ str(receiver_id) +'-'+str(receiver_des) +' Course Proposal Form "'+file_data +'"  By   '+str(uploader)+' - '+str(uploader_design)
                    # data=file.subject
                    messages.success(request, "Submitted successful")
                    prog_and_curr_notif(request.user,receiver_id,data)
                    return HttpResponseRedirect('/programme_curriculum/outward_files/')
                except IntegrityError as e:
                # Handle the IntegrityError here, for example:
                    form.add_error(None, 'Proposal_ tracking with this File id, Current id, Current design and Disciplines already exists.')
                


    return render(request,'programme_curriculum/faculty/filetracking.html',{'form':form,'submitbutton': submitbutton,'file_info':file_data,})



def inward_files(request):
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).last()
    data=''
    
    if request.session['currentDesignationSelected']  == "Associate Professor" or request.session['currentDesignationSelected']  == "Professor" or request.session['currentDesignationSelected']  == "Assistant Professor" :
        data=f'As a "{request.session["currentDesignationSelected"]}" you cannot receive any proposal requests'
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        pass
    elif request.session['currentDesignationSelected'] == "Dean Academic":
        pass
    elif request.session['currentDesignationSelected']  == "acadadmin" :
        return HttpResponseRedirect('/programme_curriculum/admin_programmes/')
    else:
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
    id=request.user
    user_designation=HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)
    notifs = request.user.notifications.all()
    designation = Designation.objects.get(name=request.session['currentDesignationSelected'])
    des_id = designation.id
    
    courseProposal = Proposal_Tracking.objects.filter(receive_design = des_id,receive_id= id)

    
    return render(request, 'programme_curriculum/faculty/inward_course_forms.html',{'courseProposals': courseProposal,'design':request.session['currentDesignationSelected'],'data':data,'notifications': notifs,})



def outward_files(request):
    user_details = ExtraInfo.objects.get(user = request.user)
    des = HoldsDesignation.objects.all().filter(user = request.user).last()
    data=''
    if request.session['currentDesignationSelected'] == "Dean Academic" :
        data=f'As a "{request.session["currentDesignationSelected"]}" you cannot have any out going files'
        pass
    elif request.session['currentDesignationSelected']  == "Associate Professor" or request.session['currentDesignationSelected']  == "Professor" or request.session['currentDesignationSelected']  == "Assistant Professor" :
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        pass
    elif request.session['currentDesignationSelected']  == "student" :
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    elif request.session['currentDesignationSelected']== "acadadmin":
        return render(request, 'programme_curriculum/admin_programmes/')
    
    id=request.user
    notifs = request.user.notifications.all()
    user_designation=HoldsDesignation.objects.select_related('user','working','designation').filter(user=request.user)
    design=request.session['currentDesignationSelected']
    
    
    designation = Designation.objects.get(name=request.session['currentDesignationSelected'])
    des_id = designation.id
    
    courseProposal = Proposal_Tracking.objects.filter(current_design = design,current_id= des.user)

    
    return render(request, 'programme_curriculum/faculty/outward_course_forms.html',{'courseProposals': courseProposal,'design':request.session['currentDesignationSelected'],'data':data,'notifications': notifs,})

def update_course_proposal_file(request, course_id):
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    if request.session['currentDesignationSelected'] == "Associate Professor" or request.session['currentDesignationSelected'] == "Professor" or request.session['currentDesignationSelected'] == "Assistant Professor":
        pass
    elif request.session['currentDesignationSelected'] == "acadadmin" :
        return HttpResponseRedirect('/programme_curriculum/admin_programmes')
    else:
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
    uploader = request.user.extrainfo
    design=request.session['currentDesignationSelected']
    course = get_object_or_404(Course, Q(id=course_id))
    file_data=course.code+' - '+course.name
    form = NewCourseProposalFile(initial={'uploader':des.user,'designation':design},instance=course)
    submitbutton= request.POST.get('Submit')
    
    if submitbutton:
        if request.method == 'POST':
            form = NewCourseProposalFile(request.POST)  
            if form.is_valid():
                previous = Course.objects.all().filter(code=course.code).order_by('version').last()
                course.version=previous.version
                new_course=form.save(commit=False)
                new_course.is_read=False
                new_course.is_update=True
                add=True
                ver=0
                # Check if a course with the same values (except version, latest_version, disciplines, and pre_requisit_courses) already exists
                old_course=Course.objects.filter(code=new_course.code, name=new_course.name, credit=new_course.credit, lecture_hours=new_course.lecture_hours, tutorial_hours=new_course.tutorial_hours, pratical_hours=new_course.pratical_hours, discussion_hours=new_course.discussion_hours, project_hours=new_course.project_hours, pre_requisits=new_course.pre_requisits, syllabus=new_course.syllabus, percent_quiz_1=new_course.percent_quiz_1, percent_midsem=new_course.percent_midsem, percent_quiz_2=new_course.percent_quiz_2, percent_endsem=new_course.percent_endsem, percent_project=new_course.percent_project, percent_lab_evaluation=new_course.percent_lab_evaluation, percent_course_attendance=new_course.percent_course_attendance, ref_books=new_course.ref_books)
                if old_course:
                    # Check if disciplines or pre_requisit_courses have been changed
                    for i in old_course:
                        if set(form.cleaned_data['pre_requisit_courses']) != set(i.pre_requisit_courses.all()):
                            add=True
                        else:
                            add=False
                            ver=i.version
                            break
                    if add:
                        new_course.save()  # Save the new course first before adding many-to-many fields
                        new_course.pre_requisit_courses.set(form.cleaned_data['pre_requisit_courses'])
                        course = Course.objects.last()
                        messages.success(request, "Added successful")
                        return HttpResponseRedirect("/programme_curriculum/admin_course/" + str(course.id) + "/")
                    else:
                        form.add_error(None,  'A Course with the same values already exists at "Version Number '+' ' +str(ver)+'"')
                else:
                    new_course.save()  # Save the new course first before adding many-to-many fields
                    new_course.pre_requisit_courses.set(form.cleaned_data['pre_requisit_courses'])
                    course = Course.objects.last()
                    messages.success(request, "Added successful")
                    return HttpResponseRedirect("/programme_curriculum/admin_course/" + str(course.id) + "/")
                    
    return render(request,'programme_curriculum/faculty/course_proposal_form.html',{'form':form,'submitbutton': submitbutton,'file_info':file_data,})




def forward_course_forms(request,ProposalId):
    de= ProposalId
    des = HoldsDesignation.objects.all().filter(user = request.user).first()

    courseform = Proposal_Tracking.objects.all().filter(id=ProposalId)
    
    uploader = request.user.extrainfo
    design=request.session['currentDesignationSelected']
    file = get_object_or_404(Proposal_Tracking, Q(id=ProposalId))
    file_id = int(file.file_id)
    file2 = get_object_or_404(NewProposalFile, Q(id=file_id))
    file_data=file2.code + ' ' + file2.name
    Proposal_D = file.id
            
    if request.session['currentDesignationSelected'] == "Dean Academic" :
        file = get_object_or_404(Proposal_Tracking, Q(id=ProposalId))
        file_id = int(file.file_id)
        file2 = get_object_or_404(NewProposalFile, Q(id=file_id))
        course =Course.objects.all().filter(code=file2.code).last()
        version_error=''
        if(course):
            previous = Course.objects.all().filter(code=course.code).order_by('version').last()
            course.version=previous.version
            form = CourseForm(instance=file2,initial={'disciplines':file.disciplines})
            submitbutton= request.POST.get('Submit')
            if submitbutton:
                if request.method == 'POST':
                    form = CourseForm(request.POST)  
                    if form.is_valid() :
                        
                        new_course = form.save(commit=False)
                        if(new_course.version>previous.version):
                            previous.latest_version=False
                            previous.save()
                            file.is_added=True
                            file.is_submitted=True
                            file.save()
                            form.latest_version=True
                            form.save()
                            course = Course.objects.last()
                        
                            receiver=file2.uploader
                            receiver_id = User.objects.get(username=receiver)
                            data=f'The Course " {file2.code} -{file2.name}" Updated Successfully'
                            # data=file.subject
                            prog_and_curr_notif(request.user,receiver_id,data)
                            messages.success(request, "Updated "+ file2.code+'-'+file2.name +" successful")
                            return HttpResponseRedirect("/programme_curriculum/course/" + str(course.id) + "/")
                        else:
                            version_error+=f'The version should be greater than {previous.version}'
                    
            return render(request,'programme_curriculum/faculty/dean_view_a_course_proposal.html',{'course':course, 'form':form, 'submitbutton': submitbutton,'version_error':version_error,'id':Proposal_D})
        else:
            form = CourseForm(instance=file2,initial={'disciplines':file.disciplines})
            # course1 =Course.objects.filter(code=file2.code,name=file2.name,credit=file2.credit,lecture_hours=file2.lecture_hours,tutorial_hours=file2.tutorial_hours,pratical_hours=file2.pratical_hours,discussion_hours=file2.discussion_hours,project_hours=file2.project_hours,pre_requisits=file2.pre_requisits,syllabus=file2.syllabus,percent_quiz_1=file2.percent_quiz_1,percent_midsem=file2.percent_midsem,percent_quiz_2=file2.percent_quiz_2,percent_project=file2.percent_project,percent_endsem=file2.percent_endsem,percent_lab_evaluation=file2.percent_lab_evaluation,percent_course_attendance=file2.percent_course_attendance,ref_books=file2.ref_books)
            submitbutton= request.POST.get('Submit')
            
            if submitbutton:
                if request.method == 'POST':
                    form = CourseForm(request.POST)
                    
                    if form.is_valid():
                        file.is_added=True
                        file.is_submitted=True
                        file.save()
                        form.save()
                        receiver=file2.uploader
                        receiver_id = User.objects.get(username=receiver)
                        data='The Course "'+ file2.code+ ' - '+ file2.name + '" Added Successfully'
                        # data=file.subject
                        prog_and_curr_notif(request.user,receiver_id,data)
                        course =Course.objects.all().filter(code=file2.code).last()
                        messages.success(request, "Added "+ file2.name +" successful")
                        return HttpResponseRedirect("/programme_curriculum/course/" + str(course.id) + "/")
                            
                           
                        
            return render(request, 'programme_curriculum/faculty/dean_view_a_course_proposal.html', {'course': file2 ,'form':form,'submitbutton': submitbutton,'id':Proposal_D})
    
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        
        form=CourseProposalTrackingFile(initial={'current_id':des.user,'current_design':request.session['currentDesignationSelected'],'file_id':file.file_id,'disciplines':file.disciplines})
        
        # The above code is trying to retrieve the value of the 'Submit' key from the POST request
        # data. It is using the `get` method on the `request.POST` dictionary to access the value
        # associated with the 'Submit' key.
        submitbutton= request.POST.get('Submit')
        
        if submitbutton:
            if request.method == 'POST':
                form = CourseProposalTrackingFile(request.POST)
                if form.is_valid():
                    try:
                        file.is_submitted=True
                        file.save()
                        form.is_read=False
                        form.save()
                        
                        receiver=request.POST.get('receive_id')
                        
                        uploader=request.POST.get('current_id')
                        uploader_design=request.POST.get('current_design')
                        
                        
                        receiver_design=request.POST.get('receive_design')
                        receiver_des= Designation.objects.get(id=receiver_design)
                        receiver_id = User.objects.get(id=receiver)
                        messages.success(request, "Added successful")
                        data='Received as '+ str(receiver_id) +'-'+str(receiver_des) +' Course Proposal of Course '+file_data +' By   '+str(uploader)+' - '+str(uploader_design)

                        prog_and_curr_notif(request.user,receiver_id,data)
                        return HttpResponseRedirect('/programme_curriculum/outward_files/')
                    except IntegrityError as e:
                        form.add_error(None, 'Proposal_ tracking with this File id, Current id, Current design and Disciplines already exists.')
    elif request.session['currentDesignationSelected'] == "acadadmin" :
        return HttpResponseRedirect('/programme_curriculum/admin_programmes')
    else:
        return HttpResponseRedirect('/programme_curriculum/programmes')
        
        
        
    return render(request,'programme_curriculum/faculty/forward.html',{'form':form,'receive_date':file.receive_date,'proposal':file2,'submitbutton': submitbutton,'id':Proposal_D})


def view_inward_files(request,ProposalId):
    
    if request.session['currentDesignationSelected'] == "Associate Professor" or request.session['currentDesignationSelected'] == "Professor" or request.session['currentDesignationSelected'] == "Assistant Professor" or request.session['currentDesignationSelected'] == "Dean Academic":
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        pass
    elif request.session['currentDesignationSelected'] == "acadadmin":
        return HttpResponseRedirect('/programme_curriculum/admin_programmes/')
    else:
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
    des = HoldsDesignation.objects.all().filter(user = request.user).first()
    uploader = request.user.extrainfo
    design=request.session['currentDesignationSelected']
    file = get_object_or_404(Proposal_Tracking, Q(id=ProposalId))
    file_id = int(file.file_id)
    file2 = get_object_or_404(NewProposalFile, Q(id=file_id))
    file_data=''
    file_data2=''
    
    
    if(file.is_rejected):
        file_data='"'+str(file2.name) + '"'+' Course Rejected by ' + str(file.receive_id) + ' - ' +str(file.receive_design)
    if(file.is_added and not file.is_rejected):
        file_data2='"'+str(file2.code)+' - '+str(file2.name) +'"  Course Added Succesfully'
    
    courseProposal = Proposal_Tracking.objects.filter(file_id=file.file_id,disciplines=file.disciplines)
    form=CourseProposalTrackingFile(initial={'current_id':des.user,'current_design':request.session['currentDesignationSelected'],'file_id':file.file_id,'disciplines':file.disciplines})

    return render(request,'programme_curriculum/faculty/view_file.html',{'form':form,'receive_date':file.receive_date,'proposal':file2,'trackings':courseProposal,'file_info':file_data,'file_sucess':file_data2})

def reject_form(request,ProposalId):
    
    if request.session['currentDesignationSelected'] == "Associate Professor" or request.session['currentDesignationSelected'] == "Professor" or request.session['currentDesignationSelected'] == "Assistant Professor" or request.session['currentDesignationSelected'] == "Dean Academic":
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        pass
    elif request.session['currentDesignationSelected'] == "acadadmin":
        return HttpResponseRedirect('/programme_curriculum/admin_programmes/')
    else:
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
    track=get_object_or_404(Proposal_Tracking, Q(id=ProposalId))
    file2 = get_object_or_404(NewProposalFile,Q(id = track.file_id))
    if(not track.is_added and not track.is_submitted):
        track.is_rejected=True
        track.is_submitted=True
        track.save()
        messages.success(request, "Course Proposal Form Rejected")
        receiver=file2.uploader
        receiver_id = User.objects.get(username=receiver)
        data='The Course "'+ file2.code+ ' - '+ file2.name + '" was Rejected by ' + str(request.user) + ' - ' +str(request.session['currentDesignationSelected'])
        prog_and_curr_notif(request.user,receiver_id,data)

        
    else:
        messages.error(request, "course already forwarded or added can't be rejected")
    return HttpResponseRedirect('/programme_curriculum/inward_files/')


def tracking_unarchive(request,ProposalId):
    if request.session['currentDesignationSelected'] == "Associate Professor" or request.session['currentDesignationSelected'] == "Professor" or request.session['currentDesignationSelected'] == "Assistant Professor" or request.session['currentDesignationSelected'] == "Dean Academic":
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        pass
    elif request.session['currentDesignationSelected'] == "acadadmin":
        return HttpResponseRedirect('/programme_curriculum/admin_programmes/')
    else:
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
    track=get_object_or_404(Proposal_Tracking, Q(id=ProposalId))
    file = get_object_or_404(NewProposalFile,Q(id = track.file_id))
    print(request.user)
    if str(track.current_design)==str(request.session['currentDesignationSelected']) and str(track.current_id)==str(request.user):
        track.sender_archive=False
        track.save()
        messages.success(request, "File UnArchived")
        return HttpResponseRedirect('/programme_curriculum/outward_files/')
    else : 
        track.receiver_archive=False
        track.save()
        messages.success(request, "File UnArchived")
        return HttpResponseRedirect('/programme_curriculum/inward_files/')
    
    
    
def tracking_archive(request,ProposalId):
    
    if request.session['currentDesignationSelected'] == "Associate Professor" or request.session['currentDesignationSelected'] == "Professor" or request.session['currentDesignationSelected'] == "Assistant Professor" or request.session['currentDesignationSelected'] == "Dean Academic":
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        pass
    elif request.session['currentDesignationSelected'] == "acadadmin":
        return HttpResponseRedirect('/programme_curriculum/admin_programmes/')
    else:
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
    track=get_object_or_404(Proposal_Tracking, Q(id=ProposalId))
    if str(track.current_design)==str(request.session['currentDesignationSelected']) and str(track.current_id)==str(request.user):
        track.sender_archive=True
        track.save()
        messages.success(request, "File Archived")
        return HttpResponseRedirect('/programme_curriculum/outward_files/')

    else:
        track.receiver_archive=True
        track.save()
        messages.success(request, "File Archived")
        return HttpResponseRedirect('/programme_curriculum/inward_files/')
    
def file_archive(request,FileId):
    if request.session['currentDesignationSelected'] == "Associate Professor" or request.session['currentDesignationSelected'] == "Professor" or request.session['currentDesignationSelected'] == "Assistant Professor" or request.session['currentDesignationSelected'] == "Dean Academic":
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        pass
    elif request.session['currentDesignationSelected'] == "acadadmin":
        return HttpResponseRedirect('/programme_curriculum/admin_programmes/')
    else:
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
    file = get_object_or_404(NewProposalFile,Q(id = FileId))
    file.is_archive=True
    file.save()
    return HttpResponseRedirect('/programme_curriculum/view_course_proposal_forms/')

def file_unarchive(request,FileId):
    if request.session['currentDesignationSelected'] == "Associate Professor" or request.session['currentDesignationSelected'] == "Professor" or request.session['currentDesignationSelected'] == "Assistant Professor" or request.session['currentDesignationSelected'] == "Dean Academic":
        pass
    elif 'hod' in request.session['currentDesignationSelected'].lower():
        pass
    elif request.session['currentDesignationSelected'] == "acadadmin":
        return HttpResponseRedirect('/programme_curriculum/admin_programmes/')
    else:
        return HttpResponseRedirect('/programme_curriculum/programmes/')
    
    file = get_object_or_404(NewProposalFile,Q(id = FileId))
    file.is_archive=False
    file.save()
    return HttpResponseRedirect('/programme_curriculum/view_course_proposal_forms/')