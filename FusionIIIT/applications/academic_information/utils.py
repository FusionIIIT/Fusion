from applications.academic_information.models import (Calendar, Student,Curriculum_Instructor, Curriculum,
                                                      Student_attendance)
from ..academic_procedures.models import (BranchChange, CoursesMtech, InitialRegistration, StudentRegistrationChecks,
                     Register, Thesis, FinalRegistration, ThesisTopicProcess,
                     Constants, FeePayments, TeachingCreditRegistration, SemesterMarks, 
                     MarkSubmissionCheck, Dues,AssistantshipClaim, MTechGraduateSeminarReport,
                     PhDProgressExamination,CourseRequested, course_registration, MessDue, Assistantship_status , backlog_course)

from applications.programme_curriculum.models import(Course,CourseSlot)
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Q
import datetime
import random
from django.db import transaction
time = timezone.now()
def check_for_registration_complete (request):
    batch = int(request.POST.get('batch'))
    sem = int(request.POST.get('sem'))
    programme = request.POST.get('programme')
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
        
        if course_registration.objects.filter(Q(semester_id__semester_no = sem) & Q(student_id__batch = batch) & Q(student_id__programme = programme)).exists() : 
            return JsonResponse({'status':2,"message":"courses already allocated"})
        
        return JsonResponse({"status":1 , "message" : "courses not yet allocated"})
    except :
        return JsonResponse({"status":-3, "message" : "No such registration found"})

@transaction.atomic
def random_algo(request) :
    print("hi")
    batch = request.POST.get('batch')
    sem = request.POST.get('sem')
    programme = request.POST.get('programme')
    year = request.POST.get('year')


    unique_course = InitialRegistration.objects.filter(Q(semester_id__semester_no = sem) & Q(student_id__batch = batch) & Q(student_id__programme = programme)).values_list('course_id',flat=True).distinct()
    print("unique course")
    print(len(unique_course))
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

    priority_1 = InitialRegistration.objects.filter(Q(semester_id__semester_no = sem) & Q(student_id__batch = batch) & Q(student_id__programme = programme) & Q(priority=1))
    print(priority_1)
    rem=0
    for p in priority_1 :
        present_priority[p.course_id.id].append([p.student_id.id.id,p.course_slot_id.id])
        rem+=1    
    
    if rem > total_seats :
        return JsonResponse({'status': -1 , 'message' : "seats not enough"})
    with transaction.atomic :
        present_priority = 1
        while rem > 0 :
            for course in present_priority :
                print(course)
                while(len(present_priority[course])) :
                    random_student_selected = random.choice(present_priority[course])

                    present_priority[course].remove(random_student_selected)

                    if seats_alloted[course] < max_seats[course] :
                        stud = Student.objects.get(student_id__id = random_student_selected[0])
                        course_object = Course.objects.get(id=course)
                        course_slot_object = CourseSlot.objects.get(id = random_student_selected[1])
                        course_registration.objects.create(
                            student_id = stud,
                            working_year = year,
                            semester_id = sem,
                            course_id = course_object,
                            course_slot_id = course_slot_object
                        )
                        seats_alloted[course] += 1
                        rem-=1
                    else :
                        next = InitialRegistration.objects.get(Q(student_id__id = random_student_selected[0]) & Q(course_id__id = course) & Q(student_id__programme = programme) & Q(priority = present_priority+1))
                        next_priority[course].append([next.student_id.id.id,next.course_slot_id.id])
            present_priority = next_priority
            next_priority = {course : [] for course in unique_course}
            present_priority+=1

    print(rem)
    return JsonResponse({'status':1})
