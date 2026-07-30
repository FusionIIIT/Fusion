from applications.academic_information.models import (Calendar, Student,Curriculum_Instructor, Curriculum,
                                                      Student_attendance)
from ..academic_procedures.models import (BranchChange, CoursesMtech, FinalRegistrations, InitialRegistration, StudentRegistrationChecks,
                     Register, Thesis, FinalRegistration, ThesisTopicProcess,
                     Constants, FeePayments, TeachingCreditRegistration, SemesterMarks, 
                     MarkSubmissionCheck, Dues,AssistantshipClaim, MTechGraduateSeminarReport,
                     PhDProgressExamination,CourseRequested, course_registration, MessDue, Assistantship_status , backlog_course,)

from applications.programme_curriculum.models import(Course,CourseSlot,Batch,Semester)
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.core import serializers
from django.db.models import Q, Count
import datetime
import random
from django.db import transaction
time = timezone.now()


def validate_course_slots(batch, sem, programme_type, skip_course_ids=None):
    """
    Finds courses registered under a CourseSlot that does not list them.

    random_algo pools students by slot *name* across curricula, so a course in
    one curriculum's slot but absent from another's gets allotted into a slot
    that does not contain it. Empty list means allocation is safe to proceed.
    """
    skip_course_ids = {int(c) for c in (skip_course_ids or [])}

    pairs = (InitialRegistration.objects
             .filter(Q(semester_id__semester_no=sem)
                     & Q(student_id__batch=batch)
                     & Q(student_id__batch_id__curriculum__programme__category=programme_type))
             .exclude(course_id__isnull=True)
             .exclude(course_slot_id__isnull=True)
             .values('course_id', 'course_slot_id')
             .annotate(students=Count('id')))
    pairs = [p for p in pairs if p['course_id'] not in skip_course_ids]
    if not pairs:
        return []

    slot_ids = {p['course_slot_id'] for p in pairs}
    valid = set(CourseSlot.courses.through.objects
                .filter(courseslot_id__in=slot_ids)
                .values_list('courseslot_id', 'course_id'))

    offending = [p for p in pairs if (p['course_slot_id'], p['course_id']) not in valid]
    if not offending:
        return []

    courses = {c.id: c for c in Course.objects.filter(
        id__in={p['course_id'] for p in offending})}
    slots = {s.id: s for s in CourseSlot.objects
             .filter(id__in={p['course_slot_id'] for p in offending})
             .select_related('semester', 'semester__curriculum')}

    problems = {}
    for p in offending:
        course, slot = courses[p['course_id']], slots[p['course_slot_id']]
        entry = problems.setdefault((course.id, slot.name), {
            'course_id': course.id,
            'course_code': course.code,
            'course_name': course.name,
            'slot_name': slot.name,
            'slot_type': slot.type,
            'missing_from': [],
            'students': 0,
        })
        entry['missing_from'].append({
            'slot_id': slot.id,
            'semester_no': slot.semester.semester_no,
            'curriculum_id': slot.semester.curriculum_id,
            'curriculum_name': str(slot.semester.curriculum.name),
            'students': p['students'],
        })
        entry['students'] += p['students']

    return sorted(problems.values(), key=lambda e: -e['students'])
def check_for_registration_complete(batch, sem, year, programme_type):
    date = datetime.date.today()
    try:
        pre_registration_date = Calendar.objects.filter(description=f"Pre Registration {sem} {year}").first()
        if not pre_registration_date:
            return {"status": -3, "message": "No such registration found"}
        
        prd_start_date = pre_registration_date.from_date
        prd_end_date = pre_registration_date.to_date

        if date < prd_start_date:
            return {"status": -2, "message": "Registration didn't start"}

        if prd_start_date <= date <= prd_end_date:
            return {"status": -1, "message": "Registration is under process"}

        if FinalRegistration.objects.filter(Q(semester_id__semester_no = sem) & Q(student_id__batch = batch) & Q(student_id__batch_id__curriculum__programme__category=programme_type)).exists() :
            return {"status": 2, "message": "Courses already allocated"}

        return {"status": 1, "message": "Courses not yet allocated"}
    
    except Exception as e:
        return {"status": -3, "message": f"Internal Server Error: {str(e)}"}

@transaction.atomic
def random_algo(batch,sem,year,course_slot, programme_type, skip_course_ids=None) :
    # zero seats makes the "slot full" branch below push these students to
    # their next priority, so skipping reuses the existing fall-through
    skip_course_ids = {int(c) for c in (skip_course_ids or [])}
    unique_course = InitialRegistration.objects.filter(Q(semester_id__semester_no = sem) & Q( course_slot_id__name = course_slot ) & Q(student_id__batch = batch) & Q(student_id__batch_id__curriculum__programme__category=programme_type)).values_list('course_id',flat=True).distinct()
    slot_filter = (Q(semester_id__semester_no = sem) & Q( course_slot_id__name = course_slot ) & Q(student_id__batch = batch) & Q(student_id__batch_id__curriculum__programme__category=programme_type))
    max_seats={}
    seats_alloted = {}
    present_priority = {}
    next_priority = {}
    total_seats = 0

    # every per-course lookup below used to be one query per course inside the loop
    course_caps = dict(Course.objects.filter(id__in=unique_course).values_list('id', 'max_seats'))
    already_alloted = dict(FinalRegistration.objects.filter(
        course_id_id__in=unique_course,
        semester_id__semester_no=sem,
        student_id__batch=batch,
        student_id__batch_id__curriculum__programme__category=programme_type,
    ).values('course_id_id').annotate(n=Count('id')).values_list('course_id_id', 'n'))

    for course in unique_course :
        if course in skip_course_ids :
            max_seats[course] = 0
        else :
            max_seats[course] = course_caps.get(course, 0)
            total_seats+=max_seats[course]
        seats_alloted[course] = already_alloted.get(course, 0)
        present_priority[course] = []
        next_priority[course] = []

    priority_1 = InitialRegistration.objects.filter(slot_filter & Q(priority=1))
    rem=len(priority_1)
    if rem > total_seats :
        return -1

    for p in priority_1 :
        present_priority[p.course_id_id].append([p.student_id_id,p.course_slot_id_id])

    # the fall-through lookup was one query per bumped student
    choice_by_priority = {}
    for stud_id, prio, c_id, cs_id in InitialRegistration.objects.filter(slot_filter).values_list(
            'student_id_id', 'priority', 'course_id_id', 'course_slot_id_id') :
        choice_by_priority.setdefault((stud_id, prio), (c_id, cs_id))

    student_curriculum = dict(Student.objects.filter(
        id__in={s for lst in present_priority.values() for s, _ in lst}
    ).values_list('id_id', 'batch_id__curriculum_id'))
    semester_by_curriculum = dict(Semester.objects.filter(
        semester_no=sem, curriculum_id__in=set(student_curriculum.values())
    ).values_list('curriculum_id', 'id'))

    to_create = []
    with transaction.atomic() :
        p_priority = 1
        while rem > 0 :
            for course in present_priority :
                while(len(present_priority[course])) :
                    random_student_selected = random.choice(present_priority[course])

                    present_priority[course].remove(random_student_selected)

                    if seats_alloted[course] < max_seats[course] :
                        to_create.append(FinalRegistration(
                            student_id_id = random_student_selected[0],
                            verified=False,
                            semester_id_id = semester_by_curriculum[
                                student_curriculum[random_student_selected[0]]],
                            course_id_id = course,
                            course_slot_id_id = random_student_selected[1]
                        ))
                        seats_alloted[course] += 1
                        rem-=1
                    else :
                        next = choice_by_priority.get((random_student_selected[0], p_priority+1))
                        if next is not None and next[0] in next_priority :
                            next_priority[next[0]].append([random_student_selected[0],next[1]])
                        else :
                            rem-=1
            p_priority+=1
            present_priority = next_priority
            next_priority = {course : [] for course in unique_course}

        FinalRegistration.objects.bulk_create(to_create)

    return 1

@transaction.atomic
def allocate(request):
    batch = request.POST.get('batch')
    sem = request.POST.get('sem')
    year = request.POST.get('year')
    programme_type = request.POST.get('programme_type')
    skip_course_ids = {int(c) for c in (request.POST.get('skip_course_ids') or [])}

    # write nothing until every mis-slotted course is added or skipped
    problems = validate_course_slots(batch, sem, programme_type, skip_course_ids)
    if problems:
        return JsonResponse({
            'status': 0,
            'message': "Some registered courses are missing from their course slot.",
            'needs_action': problems,
        }, status=409)

    unique_course_slot = InitialRegistration.objects.filter(
        Q(semester_id__semester_no=sem) & Q(student_id__batch=batch) & Q(student_id__batch_id__curriculum__programme__category=programme_type)
    ).values('course_slot_id').distinct()

    unique_course_name = []
    skipped_students = 0

    try:
        with transaction.atomic():
            for entry in unique_course_slot:
                course_slot_object = CourseSlot.objects.get(id=entry['course_slot_id'])

                if course_slot_object.type != "Open Elective":
                    # one row per student for this slot, instead of five queries each
                    registrations = list(InitialRegistration.objects.filter(
                        Q(semester_id__semester_no=sem) &
                        Q(course_slot_id=course_slot_object) &
                        Q(student_id__batch=batch) & Q(student_id__batch_id__curriculum__programme__category=programme_type)
                    ).values_list('student_id_id', 'course_id_id', 'registration_type',
                                  'old_course_registration_id'))

                    curriculum_by_student = dict(Student.objects.filter(
                        id__in={r[0] for r in registrations}
                    ).values_list('id_id', 'batch_id__curriculum_id'))
                    semester_by_curriculum = dict(Semester.objects.filter(
                        semester_no=sem, curriculum_id__in=set(curriculum_by_student.values())
                    ).values_list('curriculum_id', 'id'))

                    slot_rows = []
                    for student_id, course_id, regis, prev_registration_id in registrations:
                        # no alternative in a single-choice slot
                        if course_id in skip_course_ids:
                            skipped_students += 1
                            continue

                        slot_rows.append(FinalRegistration(
                            student_id_id=student_id,
                            verified=False,
                            semester_id_id=semester_by_curriculum[curriculum_by_student[student_id]],
                            course_id_id=course_id,
                            course_slot_id=course_slot_object,
                            registration_type=regis,
                            old_course_registration_id=prev_registration_id
                        ))
                    FinalRegistration.objects.bulk_create(slot_rows)

                    unique_course_name.append(course_slot_object.name)

                elif course_slot_object.type == "Open Elective":
                    if course_slot_object.name not in unique_course_name:
                        stat = random_algo(batch, sem, year, course_slot_object.name,
                                           programme_type, skip_course_ids)
                        unique_course_name.append(course_slot_object.name)
                        if stat == -1:
                            raise Exception(f"Seats not enough for course_slot {course_slot_object.name}")

        message = "Course allocation successful"
        if skip_course_ids:
            message += (f" ({len(skip_course_ids)} course(s) skipped"
                        f"; {skipped_students} student(s) left without a course in a single-choice slot)")
        return JsonResponse({'status': 1, 'message': message,
                             'skipped_course_ids': sorted(skip_course_ids)})

    except Exception as e:
        return JsonResponse({'status': -1, 'message': str(e) or "Allocation failed"})

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