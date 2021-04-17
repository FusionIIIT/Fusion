from django.http import request
from django.shortcuts import render, HttpResponse
import itertools
from .models import Programme, Discipline, Curriculum, Semester, Course, Batch, CourseSlot

from .forms import ProgrammeForm, DisciplineForm, CurriculumForm, SemesterForm, CourseForm, BatchForm, CourseSlotForm


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

# logic need to added - imcomplete 
    curriculum = Curriculum.objects.get(id=curriculum_id)
    semesters = Curriculum.get_semesters_objects(curriculum)
    course_slots = []
    for sem in semesters:
        course_slots.append([Semester.get_courseslots_objects(sem)])
    return render(request, 'programme_curriculum/view_semesters_of_a_curriculum.html', {'curriculum': curriculum, 'semesters': semesters, 'course_slots': course_slots})


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

def view_all_courses(request):
    """ views all the course slots of a specfic semester """
    courses = Course.objects.all()
    return render(request, 'programme_curriculum/view_all_courses.html', {'courses': courses})

def view_a_course(request, course_id):
    """ views the details of a Course """
    course = Course.objects.get(id=course_id)
    return render(request, 'programme_curriculum/view_a_course.html', {'course': course})


# ------------Acad-Admin-functions---------------#

# def add_programme(request):
#     if request.method == "POST":
#         Category = request.POST.get('category')
#         Title = request.POST.get('title')
#         programme = Programme(category=Category, title=Title)
#         programme.save()       
#     return render(request,'add_programme.html')

def add_discipline_form(request):
    form = DisciplineForm()
    if request.method == 'POST':
        form = DisciplineForm(request.POST)  
        if form.is_valid():
            form.save()
    return render(request, 'programme_curriculum/acad_admin/add_discipline_form.html',{'form':form})

def add_programme_form(request):
    form = ProgrammeForm()
    if request.method == 'POST':
        form = ProgrammeForm(request.POST)  
        if form.is_valid():
            form.save()
    return render(request,'programme_curriculum/acad_admin/add_programme_form.html',{'form':form})

def add_curriculum_form(request):
    form = CurriculumForm()
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

    return render(request, 'programme_curriculum/acad_admin/add_curriculum_form.html',{'form':form})

def add_course_form(request):
    form = CourseForm()
    if request.method == 'POST':
        form = CourseForm(request.POST)  
        if form.is_valid():
            form.save()
    return render(request,'programme_curriculum/acad_admin/add_course_form.html',{'form':form})


def update_course_form(request,course_id):
    course = Course.objects.get(id=course_id)
    form = CourseForm(instance=course)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)  
        if form.is_valid():
            form.save()
    return render(request,'programme_curriculum/acad_admin/add_course_form.html',{'course':course, 'form':form})



























# """ def programme_curriculum(request):
#     return render(request, 'programme_curriculum/main.html')

# def programme_curriculum_admin(request):
#     return render(request, 'programme_curriculum/adminpage.html')

# def programme(request):
#     ug = ProgrammeList.objects.filter(category='UG')
#     pg = ProgrammeList.objects.filter(category='PG')
#     phd = ProgrammeList.objects.filter(category='PHD')
#     return render(request,'programme_curriculum/programme.html',{'UG':ug, 'PG':pg, 'PHD':phd})

# def curriculum(request, pro_id):
#     current_curriculum = CurriculumList.objects.filter(working_curriculum=1).filter(programme_id_id=pro_id)
#     past_curriculum = CurriculumList.objects.filter(working_curriculum=0).filter(programme_id_id=pro_id)
#     title = ProgrammeList.objects.filter(id=pro_id)[0]
#     return render(request,'programme_curriculum/curriculum.html',{'Current_curriculum': current_curriculum, 'Past_curriculum': past_curriculum, 'Title':title})

# def curriculum_semester(request, cur_id):
#     Curr = CurriculumList.objects.filter(id = cur_id).first()
#     Sem = SemesterList.objects.filter(curriculum_id_id = cur_id)
#     SCL = SemesterCourseList.objects.all()
#     return render(request,'programme_curriculum/curriculum_semester.html',{'sem':Sem, 'curr':Curr, 'scl':SCL})

# def working_curriculum(request):
#     current_curriculum = CurriculumList.objects.filter(working_curriculum=1)
#     return render(request,'programme_curriculum/working_curriculum.html',{'Current_curriculum': current_curriculum})

# def semester(request, cur_id):
#     Curr = CurriculumList.objects.filter(id = cur_id).first()
#     Sem = SemesterList.objects.filter(curriculum_id_id = cur_id)
#     SCL = SemesterCourseList.objects.all()
#     return render(request,'programme_curriculum/semester.html',{'sem':Sem, 'curr':Curr, 'scl':SCL})

# def courses(request,cour_id):
#     course_detail = CourseDetails.objects.filter(id = cour_id)
#     return render(request,'programme_curriculum/courses.html',{'Course_detail':course_detail})

# def add_programme(request):
#     form = ProgrammeForm()
#     if request.method == 'POST':
#         form = ProgrammeForm(request.POST)  
#         if form.is_valid():
#             form.save()
#     return render(request,'programme_curriculum/add_programme.html',{'form':form}) """

# # def show_courses(request):
# #     if request.method == "POST":
# #         Course_code = request.POST.get('')
# #         Course_name = request.POST.get('')
# #         Contact_hours_Lecture = request.POST.get('')
# #         Contact_hours_Tutorial = request.POST.get('')
# #         Contact_hours_Lab = request.POST.get('')
# #         Contact_hours_Discussion = request.POST.get('')
# #         Contact_hours_Project = request.POST.get('')
# #         Evaluation_schema_quiz1 = request.POST.get('')
# #         Evaluation_schema_midsem = request.POST.get('')
# #         Evaluation_schema_quiz2 = request.POST.get('')
# #         Evaluation_schema_lab = request.POST.get('')
# #         Evaluation_schema_endsem = request.POST.get('')
# #         Syllabus = request.POST.get('')
# #         Ref_books = request.POST.get('')
# #         courses = Courses()
# #         courses.save()   
# #     return render(request,'courses.html')

# """ def add_course(request):
#     form = CoursesForm()
#     if request.method == 'POST':
#         form = CoursesForm(request.POST)  
#         if form.is_valid():
#             form.save()
#     return render(request,'programme_curriculum/add_course.html',{'form':form}) """
#     # if request.method == "POST":
#     #     Course_code = request.POST.get('course_code')
#     #     Title = request.POST.get('course_name')
#     #     Credits = request.POST.get('')
#     #     Contact_hours_Lecture = request.POST.get('contact_hour_lecture')
#     #     Contact_hours_Tutorial = request.POST.get('contact_hour_tutorial')
#     #     Contact_hours_Lab = request.POST.get('contact_hour_lab')
#     #     Contact_hours_Discussion = request.POST.get('contact_hour_discussion')
#     #     Contact_hours_Project = request.POST.get('contact_hour_project')
#     #     Syllabus = request.POST.get('syllabus')
#     #     Evaluation_schema_quiz1 = request.POST.get('evaluation_schema_quiz1')
#     #     Evaluation_schema_midsem = request.POST.get('evaluation_schema_midsem')
#     #     Evaluation_schema_quiz2 = request.POST.get('evaluation_schema_quiz2')
#     #     Evaluation_schema_lab = request.POST.get('evaluation_schema_lab')
#     #     Evaluation_schema_endsem = request.POST.get('evaluation_schema_endsem')
#     #     Ref_books = request.POST.get('reference_books')
#     #     courses = Courses(course_code=Course_code, 
#     #     title=Title, 
#     #     contact_hours_Lecture=Contact_hours_Lecture, 
#     #     contact_hours_Tutorial=Contact_hours_Tutorial, 
#     #     contact_hours_Lab=Contact_hours_Lab, 
#     #     contact_hours_Discussion=Contact_hours_Discussion, 
#     #     contact_hours_Project=Contact_hours_Project, 
#     #     syllabus=Syllabus, 
#     #     evaluation_schema_quiz1=Evaluation_schema_quiz1, 
#     #     evaluation_schema_midsem=Evaluation_schema_midsem, 
#     #     evaluation_schema_quiz2=Evaluation_schema_quiz2, 
#     #     evaluation_schema_lab=Evaluation_schema_lab, 
#     #     evaluation_schema_endsem=Evaluation_schema_endsem, 
#     #     ref_books=Ref_books)
#     #     courses.save()   
#     # return render(request,'add_course.html')



# # def show_update_course(request):
# #     if request.method == "POST":
# #         cour_code =request.POST.get('course_code')
# #         obj = Courses.objects.filter(course_code=cour_code)
# #     return render(request,'update_course.html',{'courses':obj}) 
       
    


# # def update_course(request):
# #     if request.method == "POST":
# #         Course_code = request.POST.get('')
# #         Title = request.POST.get('')
# #         Credits = request.POST.get('')
# #         Contact_hours_Lecture = request.POST.get('')
# #         Contact_hours_Tutorial = request.POST.get('')
# #         Contact_hours_Lab = request.POST.get('')
# #         Contact_hours_Discussion = request.POST.get('')
# #         Contact_hours_Project = request.POST.get('')
# #         Syllabus = request.POST.get('')
# #         Evaluation_schema_quiz1 = request.POST.get('')
# #         Evaluation_schema_midsem = request.POST.get('')
# #         Evaluation_schema_quiz2 = request.POST.get('')
# #         Evaluation_schema_lab = request.POST.get('')
# #         Evaluation_schema_endsem = request.POST.get('')
# #         Ref_books = request.POST.get('')
# #         courses = Courses()
# #         courses.save()
# #     return render(request,'update_course.html')

# """ def update_course(request,cour_id=0):
#     cour = CourseDetails.objects.all()
#     cour1 = CourseDetails.objects.get(id=cour_id)
#     form = CoursesForm(instance=cour1)
#     if request.method == 'POST':
#         form = CoursesForm(request.POST, instance=cour1)  
#         if form.is_valid():
#             form.save()
#     return render(request,'programme_curriculum/update_course.html',{'cour':cour, 'form':form}) """



# # def add_curriculum_semester(request,co_id):
# #     if request.method == 'POST':
# #         sem_no = request.POST.get('semestor_no')
# #         course_code = request.POST.get('course_code')
# #         credit = request.POST.get('credit')
# #         obj1 = SemesterList(semester_no=sem_no, curriculum_id=co_id)
# #         obj1.save()

# #         cour = Courses.objects.filter(course_code=course_code).filter(curriculum_id=co_id)
# #         cour.credits=credit
# #         cour.save()
# #         add_course_curriculum(course_code,sem_no,co_id)
      

        
# #     return render(request,'add_curriculum_semster.html',{'Prog':prog})

# # def add_course_curriculum(request,course_code,sem_no,co_id):
# #     cour = Courses.objects.filter(course_code=course_code)
# #     cour_id=cour.id
# #     sem  = SemesterList.objects.filter(semester_no=sem_no).filter(curriculum_id=co_id)
# #     sem_id= sem.id
# #     obj = SemesterCourseList(semester_id=sem_id, course_id=cour_id)
# #     obj.save() 
# #    # obj  = SemesterCourseList(semester_id=)
# #     return render(request,'add_course_curriculum.html',{'Cour':cour})

# """ def add_curriculum_semester(request):
#     form = CurriculumForm()
#     if request.method == 'POST':
#         form = CurriculumForm(request.POST)  
#         if form.is_valid():
#             form.save()
#     return render(request,'programme_curriculum/add_curriculum_semster.html',{'form':form})

# def add_course_curriculum(request):
#     cur = CurriculumList.objects.all()
#     cour = CourseDetails.objects.all()
#     if request.method == "POST":
#         curr_id = request.POST.get('currid')
#         sem_no = request.POST.get('semno')
#         cour_id = request.POST.get('courid')
#         semester = SemesterList(semester_no=sem_no, curriculum_id_id=curr_id)
#         semester.save()
#         sem = SemesterList.objects.all().last()
#         semester_course = SemesterCourseList(semester_id=sem.id, course_id=cour_id)
#         semester_course.save()
#     return render(request,'programme_curriculum/add_course_curriculum.html',{'cur':cur, 'cour':cour}) """

# # def show_course(request):
# #     courses=Courses.objects.all()
# #     return render(request,'courses.html',{'courses':courses})

# # def add_curriculum_semester(request):
# #     if request.method == 'POST':
# #         programme =  programme()
# #         programme.save()
# #         name = request.POST.get('')
# #         batch_year = request.POST.get('')
# #         no_of_semester = request.POST.get('')
# #     return render(request,'add_curriculum_semster.html',{'Prog':prog})
