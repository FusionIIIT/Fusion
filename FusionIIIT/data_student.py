import os
from django.shortcuts import get_object_or_404
import xlrd
from django.contrib.auth.models import User

from applications.academic_information.models import Student,Course, Curriculum
from applications.academic_procedures.models import Register
from applications.globals.models import DepartmentInfo, Designation, ExtraInfo

excel = xlrd.open_workbook(
    os.path.join(
        os.getcwd(),
        'MS302.xlsx'))
z = excel.sheet_by_index(0)



nahihua = []

course_name = str(z.cell(7, 2).value)
course_code = str(z.cell(6, 2).value)
instructor = str(z.cell(8, 2).value)
sem = 8
branch = 'ME'
batch =  2015
programme = 'B.Tech'
credits = 4


course_obj = Course.objects.all().filter(course_name = course_name).first()
if not course_obj :
    course_obj_create = Course(
        course_name = course_name,
        course_details = instructor)
    course_obj_create.save()

course_obj = Course.objects.all().filter(course_name = course_name).first()

curriculum_obj_create = Curriculum(
    course_code = course_code,
    course_id = course_obj,
    credits = credits,
    course_type = 'Professional Core',
    programme = programme,
    branch = branch,
    batch = batch,
    sem = sem,
    floated = True)
curriculum_obj_create.save()

curriculum_obj = Curriculum.objects.all().filter(course_code = course_code).filter(batch = batch).filter(programme = programme).first()



for i in range(10, 31):
    print(i)
    try:
        roll_no = int(z.cell(i, 1).value)
        username = str(roll_no)
        print(username)

        dep = str(z.cell(i, 3).value)
        user = get_object_or_404(User, username = username)
        ext = ExtraInfo.objects.get(user = user)
        st = Student.objects.get(id = ext)



        batch = st.batch
        if batch == 2015 :
            try:
                last_id = Register.objects.all().aggregate(Max('r_id'))
                last_id = last_id['r_id__max']+1
            except:
                last_id = 1
                register_obj_create = Register(
                    r_id = last_id,
                    curr_id = curriculum_obj,
                    year = batch,
                    student_id = st,
                    semester = sem)
                register_obj_create.save()
        else :
            continue

        print(str(i) + "done")
    except Exception as e:
        print(e)
        print(i)
        nahihua.append(i)

print(nahihua)
