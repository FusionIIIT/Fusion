from django.shortcuts import render, HttpResponse
import itertools
from .models import Programme, Discipline, Curriculum, Semester, Course, Batch, CourseSlot

# Create your views here.
def main_page(request):
    """ display the main page """
    return HttpResponse()

# def admin_page(request):
#     return HttpResponse()

def view_programes(request):
    """ views all programmes, both working and obselete curriculums of all programmes """

    ug = Programme.objects.filter(category='UG')
    pg = Programme.objects.filter(category='PG')
    phd = Programme.objects.filter(category='PHD')
    programmes = []
    for (ug, pg, phd) in itertools.zip_longest(ug, pg, phd, fillvalue=""):
        programmes.append([ug, pg, phd])

    return render(request,'programme_curriculum/',{'programmes':programmes})


def view_programme_curriculums(request, programme_id):
    """ views all the curriculums of a specfic programme """

    working_curriculums = Curriculum.objects.filter(programme = programme_id).filter(working_curriculum=1)
    past_curriculums = Curriculum.objects.filter(programme = programme_id).filter(working_curriculum=0)
    return render(request,'programme_curriculum/',{'past_curriculums': past_curriculums, 'working_curriculums': working_curriculums})


def view_working_curriculums(request, programme_id):
    """ views all the working curriculums of a specfic programme """
    
    curriculums = Curriculum.objects.filter(programme = programme_id).filter(working_curriculum=1)
    return render(request,'programme_curriculum/',{'curriculums':curriculums})


def view_curriculum_semesters(request, curriculum_id):
    """ gets all the semesters of a specfic curriculum """

    semesters = Semester.objects.filter(curriculum = curriculum_id).order_by("semester_no")
    course_slots = []
    for sem in semesters:
        course_slots.append(CourseSlot.objects.filter(semester=sem.id).order_by("id"))
    return semesters


def view_a_curriculum_semester(request, semester_id):
    """ views a specfic semester of a specfic curriculum """

    semester = Semester.objects.filter(id = semester_id)
    course_slots = Semester.objects.filter(id=semester_id).order_by("id")
    courses = []
    for cs in course_slots:
        courses.append(CourseSlot.get_courses_objects(cs))
    return HttpResponse()


def view_curriculum_courses(request, curriculum_id):
    """ views all the courses offered by a specfic program """
    return HttpResponse()

def view_semester_courses(request, semester_id):
    """ views all the courses offered by a specfic semester """
    return HttpResponse()

def view_semester_course_slots(request, semester_id):
    """ views all the course slots of a specfic semester """
    return HttpResponse()

def view_a_course(request, course_id):
    """ views all the curriculums of a specfic program """
    return HttpResponse()






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

# # def add_programme(request):
# #     if request.method == "POST":
# #         Category = request.POST.get('category')
# #         Title = request.POST.get('title')
# #         programme = ProgrammeList(category=Category, title=Title)
# #         programme.save()       
# #     return render(request,'add_programme.html')

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
