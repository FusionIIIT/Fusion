"""Registration and semester helpers used by the academic_procedures API.

Moved unchanged from views.py (the old server-rendered pages), which still
imports them from here until those pages are removed.
"""
import json
from itertools import chain

from django.core.serializers import serialize
from django.utils import timezone

from applications.academic_information.models import Calendar, Curriculum, Student
from applications.globals.models import Designation, HoldsDesignation
from applications.programme_curriculum.models import CourseSlot

from .models import FinalRegistration, Register, StudentRegistrationChecks, course_registration

# Evaluated once, when the module is first imported (as it was in views.py).
demo_date = timezone.now()


def get_final_registration_window():
    return Calendar.objects.all().filter(
        description="Physical Reporting at the Institute"
    ).first()


def get_final_registration_eligibility(current_date):
    try:
        frd = Calendar.objects.all().filter(description="Physical Reporting at the Institute").first()
        frd_start_date = frd.from_date
        frd_end_date = frd.to_date
        if current_date>=frd_start_date and current_date<=frd_end_date:
            return True
        else :
            return False
    except Exception as e:
        return False


def get_add_or_drop_course_date_eligibility(current_date):
    try:
        add_drop_course_date = Calendar.objects.all().filter(description="Last Date for Adding/Dropping of course").first()
        adc_start_date = add_drop_course_date.from_date
        adc_end_date = add_drop_course_date.to_date
        if current_date>=adc_start_date and current_date<=adc_end_date:
            return True
        else :
            return False
    except Exception as e:
        return False


def get_acad_year(user_sem, year):
        if user_sem%2 == 1:
            acad_year = str(year) + "-" + str(year+1)
        elif user_sem%2 == 0:
            acad_year = str(year-1) + "-" + str(year)
        return acad_year


def get_student_registrtion_check(obj, sem):
    return StudentRegistrationChecks.objects.all().filter(student_id = obj, semester_id = sem).first()


def get_cpi(id):
    obj =  Student.objects.select_related('id','id__user','id__department').get(id = id)
    return obj.cpi


def get_final_registration_choices(branch_courses,batch):
    course_option = []
    unavailable_courses = []
    for courseslot in branch_courses:
        max_limit = courseslot.max_registration_limit
        lis = []
        for course in courseslot.courses.all():
            if FinalRegistration.objects.filter(student_id__batch_id__year = batch, course_id = course).count() < max_limit:
                lis.append(course)
            else:
                unavailable_courses.append(course)
        course_option.append((courseslot, lis))
    return course_option, unavailable_courses


def get_add_course_options(branch_courses, current_register, batch):

    course_option = []
    courses = current_register
    slots = []
    for c in current_register:
        slots.append(c[0])
    for courseslot in branch_courses:
        if courseslot.type == "Swayam":
            continue
        max_limit = courseslot.max_registration_limit
        if courseslot not in slots:
            lis = []
            for course in courseslot.courses.all():
                # print(course)
                if course_registration.objects.filter(student_id__batch_id__year = batch, course_id = course).count() < max_limit:
                    lis.append(course)
            course_option.append((courseslot, lis))
    return course_option


def get_drop_course_options(current_register):
    courses = []
    for item in current_register:
        if item[0].type != "Professional Core":
            courses.append(item[1])
    return courses


def get_replace_course_options( current_register, batch):
    replace_options = []

    for registered_course in current_register:
        courseslot_id = registered_course[0]
        course_id = registered_course[1]

        courseslot = courseslot_id
        coursename = course_id.name
        lis = []

        if 'Elective' in courseslot.type:
            for course in courseslot.courses.all():
                if course != course_id:
                    lis.append(course)
            replace_options.append((courseslot, coursename, lis))

    return replace_options


def get_user_semester(roll_no, ug_flag, masters_flag, phd_flag):
    roll = str(roll_no)
    now = demo_date
    year, month = now.year, int(now.month)
    y = str(year)
    if(ug_flag):
        if(roll[2].isdigit()):
            roll = int(roll[:4])
        else:
            roll = int("20"+roll[:2])        
        user_year = year - roll
    elif(masters_flag or phd_flag):
        roll =  int(roll[:2])
        user_year = int(y[-2:]) - roll
    sem = 'odd'
    if month >= 7 and month<=12:
        sem = 'odd'
    else:
        sem = 'even'
    if sem == 'odd':
        return user_year * 2 + 1
    else:
        return user_year * 2


def get_branch_courses(roll_no, user_sem, branch):
    roll = str(roll_no)
    try:
        year = int(roll[:4])
    except:
        year = int(roll[:2])
        year = 2000 + year
    courses = Curriculum.objects.all().select_related().filter(batch=(year))
    courses = courses.filter(sem = user_sem)
    courses = courses.filter(floated = True)
    course_list = []
    for course in courses:
        if branch.lower() == course.branch.lower() :
            course_list.append(course)
        elif course.branch.lower() == 'common':
            course_list.append(course)
    return course_list


def get_sem_courses(sem_id, batch):
    courses = []
    course_slots = CourseSlot.objects.all().filter(semester_id = sem_id)
    for slot in course_slots:
        courses.append(slot)
    return courses


def get_currently_registered_courses(id, user_sem):
    obj = Register.objects.all().select_related('curr_id','student_id','curr_id__course_id','student_id__id','student_id__id__user','student_id__id__department').filter(student_id=id, semester=user_sem)
    ans = []
    for i in obj:
        course = Curriculum.objects.select_related().get(curriculum_id=i.curr_id.curriculum_id)
        ans.append(course)
    return ans


def get_currently_registered_course(id, sem_id, courseregobj=False):
    if (type(sem_id) == int):
        obj = course_registration.objects.all().filter(student_id = id, semester_id__semester_no=sem_id)
    else:
        obj = course_registration.objects.all().filter(student_id = id).order_by('-semester_id__semester_no')
    courses = []
    for i in obj:
        if (courseregobj):
            courses.append(i)
        else:
            courses.append((i.course_slot_id,i.course_id))
    return courses


def get_current_credits(obj):
    credits = 0
    for i in obj:
        credits = credits + i[1].credit
    return credits


def get_faculty_list():
    f1 = HoldsDesignation.objects.select_related().filter(designation=Designation.objects.get(name = "Assistant Professor"))
    f2 = HoldsDesignation.objects.select_related().filter(designation=Designation.objects.get(name = "Professor"))
    f3 = HoldsDesignation.objects.select_related().filter(designation=Designation.objects.get(name = "Associate Professor"))

    faculty = list(chain(f1,f2,f3))
    faculty_list = []
    for i in faculty:
        faculty_list.append(i)
    return faculty_list


def get_registration_courses(courses):
    x = [[]]
    
    for temp in courses:
        flag = False
        i = str(temp.course_code)
        i = i[:5]
        for j in x:
            if j:
                name = j[0]
                name = str(name.course_code)
                name = name[:5]
                if i.upper() == name.upper():
                    j.append(temp)
                    flag = True
                else :
                    continue
        if not flag:
            x.append([temp])
    return x


def get_detailed_sem_courses(sem_id):
    course_slots = CourseSlot.objects.filter(semester_id=sem_id)
    # Serialize queryset of course slots into JSON
    course_slots_json = serialize('json', course_slots)
    # Convert JSON string into Python object
    course_slots_data = json.loads(course_slots_json)
    
    # Iterate over each course slot data and include associated course data
    for slot_data in course_slots_data:
        # Retrieve associated courses for the current course slot
        slot = CourseSlot.objects.get(id=slot_data['pk'])
        courses = list(slot.courses.all().values())
        # Add courses data to the course slot data
        slot_data['courses'] = courses
    
    return course_slots_data
