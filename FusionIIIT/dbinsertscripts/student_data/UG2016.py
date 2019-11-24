import xlrd
import sys
import os
import django
sys.path.append(r'/home/fusion/Fusion/FusionIIIT/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'Fusion.settings'
django.setup()


from django.contrib.auth.models import User
from applications.academic_information.models import Student,Course, Curriculum
from applications.globals.models import ExtraInfo,DepartmentInfo
from applications.academic_procedures.models import InitialRegistrations,StudentRegistrationCheck

excel = xlrd.open_workbook(
        os.path.join(
            os.path.dirname(__file__),
            'pre_registration','UG2016.xlsx'))


programme = 'B.Tech'
batch = 2016
sem = 8
credits = 2
z = excel.sheet_by_index(0)
number_rows = z.nrows
number_cols = z.ncols


for i in range(1,number_rows):
    username = int(z.cell(i, 1).value)
    username = str(username).strip()
    email = username + '@iiitdmj.ac.in'
    name = str(z.cell(i,2).value)
    name = name.split()
    first_name = name[0]
    dep = str(z.cell(i, 3).value).strip()
    if (len(name)==1):
        last_name = name[0]
    else:
        last_name  = name[1]
    try:
        user = User.objects.get(username=username)
    except:
        user = User.objects.create_user(
            username = username,
            password = 'hello123',
            first_name = first_name,
            last_name = last_name,
            email = email
        )
        user.save()
    try:
        ext = ExtraInfo.objects.get(user=user)
    except:
        ext = ExtraInfo(
        id = username,
        user = user,
        sex = 'M',
        user_type = 'student',
        department = DepartmentInfo.objects.get(name = dep)
        )
        ext.save()
    try:
        st = Student.objects.get(id=ext)
    except:
        st = Student(
            id = ext,
            programme = programme,
            batch = username[0:4],
            cpi = 9.5,
            category = "GEN",
            specialization = None,
            room_no = "A-302",
            hall_no = "4",
        )
        st.save()
    courses = []
    for j in range(4,number_cols):
        course_name = str(z.cell(i, j).value).strip()
        if(j!=8 and course_name!=''):
            courses.append(course_name)
        if(j==8 and course_name!=''):
            one_credit = course_name.split(',')
            for c in one_credit:
                courses.append(c.strip())
    print(courses)
    for course_name in courses:
        course_code = course_name[0:6]
        course_code = course_code.strip()
        branch = "Common"
        try:
            course_obj = Course.objects.get(course_name = course_name)
            print(course_obj)
        except:
            course_obj = Course(course_name = course_name)
            course_obj.save()
            print(course_obj)
        try:
            curriculum_obj = Curriculum.objects.filter(course_code = course_code).filter(batch=batch).get(programme=programme)
            print(curriculum_obj)
        except:
            print("assfjsd")
            curriculum_obj = Curriculum(
                course_id = course_obj,
                credits = credits,
                course_code = course_code,
                branch = branch,
                course_type = 'Professional Core',
                programme = programme,
                batch = batch,
                sem = sem,
                floated = True)
            curriculum_obj.save()
        try:
            p = InitialRegistrations.objects.filter(student_id__id = ext).get(curr_id = curriculum_obj)
        except:
            p = InitialRegistrations(
                curr_id = curriculum_obj,
                semester = sem,
                student_id = st,
                batch = batch
                )
            p.save()
    check = StudentRegistrationCheck(
                student = st,
                pre_registration_flag = True,
                final_registration_flag = False,
                semester = sem
            )
    check.save()