from applications.academic_information.models import (Calendar, Student,Curriculum_Instructor, Curriculum,
                                                      Student_attendance)
from ..academic_procedures.models import (BranchChange, CoursesMtech, InitialRegistration, StudentRegistrationChecks,
                     Register, Thesis, FinalRegistration, ThesisTopicProcess,
                     Constants, FeePayments, TeachingCreditRegistration, SemesterMarks, 
                     MarkSubmissionCheck, Dues,AssistantshipClaim, MTechGraduateSeminarReport,
                     PhDProgressExamination,CourseRequested, course_registration, MessDue, Assistantship_status , backlog_course,)

from applications.programme_curriculum.models import(Course,CourseSlot,Batch,Semester)
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.core import serializers
from django.db.models import Q
import datetime
import random
from django.db import transaction
time = timezone.now()
def check_for_registration_complete (request):
    batch = int(request.POST.get('batch'))
    sem = int(request.POST.get('sem'))
    year = request.POST.get('year')


    date = time.date()

    try:

        pre_registration_date = Calendar.objects.all().filter(description=f"Pre Registration {sem} {year}").first()
        prd_start_date = pre_registration_date.from_date
        prd_end_date = pre_registration_date.to_date

        if date<prd_start_date : 
            return JsonResponse({'status':-2 , 'message': "registration didn't start"})
        if date>=prd_start_date and date<=prd_end_date:
            return JsonResponse({'status':-1 , "message":"registration is under process"})
        
        if FinalRegistration.objects.filter(Q(semester_id__semester_no = sem) & Q(student_id__batch = batch)).exists() : 
            return JsonResponse({'status':2,"message":"courses already allocated"})
        
        return JsonResponse({"status":1 , "message" : "courses not yet allocated"})
    except :
        return JsonResponse({"status":-3, "message" : "No such registration found"})

@transaction.atomic
def random_algo(batch,sem,year,course_slot) :
    unique_course = InitialRegistration.objects.filter(Q(semester_id__semester_no = sem) & Q( course_slot_id__name = course_slot ) & Q(student_id__batch = batch)).values_list('course_id',flat=True).distinct()
    max_seats={}
    seats_alloted = {}
    present_priority = {}
    next_priority = {}
    total_seats = 0
    for course in unique_course :
        max_seats[course] = Course.objects.get(id=course).max_seats
        total_seats+=max_seats[course]
        seats_alloted[course] = 0
        present_priority[course] = []
        next_priority[course] = []

    priority_1 = InitialRegistration.objects.filter(Q(semester_id__semester_no = sem) & Q( course_slot_id__name = course_slot ) & Q(student_id__batch = batch) & Q(priority=1))
    rem=len(priority_1)
    if rem > total_seats :
        return -1
    
    for p in priority_1 :
        present_priority[p.course_id.id].append([p.student_id.id.id,p.course_slot_id.id])   
    with transaction.atomic() :
        p_priority = 1
        while rem > 0 :
            for course in present_priority :
                while(len(present_priority[course])) :
                    random_student_selected = random.choice(present_priority[course])

                    present_priority[course].remove(random_student_selected)

                    if seats_alloted[course] < max_seats[course] :
                        stud = Student.objects.get(id__id = random_student_selected[0])
                        curriculum_object = Student.objects.get(id__id = random_student_selected[0]).batch_id.curriculum
                        course_object = Course.objects.get(id=course)
                        course_slot_object = CourseSlot.objects.get(id = random_student_selected[1])
                        semester_object = Semester.objects.get(Q(semester_no = sem) & Q(curriculum = curriculum_object))
                        FinalRegistration.objects.create(
                            student_id = stud,
                            verified=False,
                            semester_id = semester_object,
                            course_id = course_object,
                            course_slot_id = course_slot_object
                        )
                        seats_alloted[course] += 1
                        rem-=1
                    else :
                        next = InitialRegistration.objects.get(Q(student_id__id__id = random_student_selected[0]) & Q( course_slot_id__name = course_slot ) & Q(semester_id__semester_no = sem) & Q(student_id__batch = batch) & Q(priority=p_priority+1))
                        next_priority[next.course_id.id].append([next.student_id.id.id,next.course_slot_id.id])
            p_priority+=1
            present_priority = next_priority
            next_priority = {course : [] for course in unique_course}

    return 1

@transaction.atomic
def allocate(request):
    batch = request.POST.get('batch')
    sem = request.POST.get('sem')
    year = request.POST.get('year')
    unique_course_slot = InitialRegistration.objects.filter(Q(semester_id_semester_no=sem) & Q(
        student_id_batch=batch)).values('course_slot_id').distinct()
    unique_course_name = []

    try:
        with transaction.atomic():
            for entry in unique_course_slot:
                course_slot_object = CourseSlot.objects.get(
                    id=entry['course_slot_id'])
                if course_slot_object.type != "Open Elective":
                    # Fetch students registered in this course slot
                    students = InitialRegistration.objects.filter(
                        Q(semester_id__semester_no=sem) &
                        Q(course_slot_id=course_slot_object) &
                        Q(student_id__batch=batch)
                    ).values_list('student_id', flat=True)

                    # Allocate each student directly to FinalRegistration
                    for student_id in students:
                        student = Student.objects.get(id=student_id)
                        semester = Semester.objects.get(
                            semester_no=sem, curriculum=student.batch_id.curriculum)
                        regis = InitialRegistration.objects.filter(
                            course_slot_id_id=course_slot_object,
                            student_id_id=student_id
                        ).values_list('registration_type', flat=True).first()
                        # course = Course.objects.get(id=course_slot_object.courses.id)
                        # course_id = course_slot_object.courses.values_list('id', flat=True).first()
                        course_id = InitialRegistration.objects.filter(
                            course_slot_id_id=course_slot_object,
                            student_id_id=student_id
                        ).values_list('course_id', flat=True).first()

                        # Retrieve the Course instance
                        course = Course.objects.get(id=course_id)

                        # Insert directly into FinalRegistration
                        # if course_slot_object.name in unique_course_name:
                        #     print("skip")
                        #     continue

                        FinalRegistration.objects.create(
                            student_id=student,
                            verified=False,
                            semester_id=semester,
                            course_id=course,
                            course_slot_id=course_slot_object,
                            registration_type=regis
                        )

                    unique_course_name.append(course_slot_object.name)
                elif course_slot_object.type == "Open Elective":  # Runs only for open elective course slots
                    if course_slot_object.name not in unique_course_name:
                        stat = random_algo(batch, sem, year, course_slot_object.name)
                        unique_course_name.append(course_slot_object.name)
                        if (stat == -1):
                            print("Seats not enough for course_slot", str(course_slot_object.name), "terminating process...")
                            raise Exception("seats not enough for course_slot "+str(course_slot_object.name))

        return JsonResponse({'status': 1, 'message': "course allocation successful"})
    except:
        return JsonResponse({'status': -1, 'message': "seats not enough for some course_slot"})
    
def view_alloted_course(request) : 
    batch = request.POST.get('batch')
    sem = request.POST.get('sem')
    verified = request.POST.get('year')
    course = request.POST.get('course')

    registrations = FinalRegistration.objects.filter(Q(student_id__batch = batch) &  Q(semester_id__semester_no = sem) & Q(course_id__code = course))
    return_list = []
    for registration in registrations:
        obj = {
            'student':registration.student_id.id.id
        }
        return_list.append(obj)
    return JsonResponse({'status':1 , 'student_list':return_list })