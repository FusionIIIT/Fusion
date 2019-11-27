import xlrd
import datetime
import sys
import os
import django
sys.path.append(r'/home/fusion/Fusion/FusionIIIT/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'Fusion.settings'
django.setup()


demo_date = datetime.datetime.now()

from django.contrib.auth.models import User
from applications.academic_information.models import Student,Course, Curriculum
from applications.academic_procedures.models import Register
from applications.globals.models import DepartmentInfo, Designation, ExtraInfo, HoldsDesignation

log = open("myprog.log", "a")
sys.stdout = log

filenames = os.listdir('/home/fusion/Fusion/FusionIIIT/dbinsertscripts/student_data/btech')
for filename in filenames:

    excel = xlrd.open_workbook(
            os.path.join(
                os.path.dirname(__file__),
                'btech', filename))
    z = excel.sheet_by_index(0)

    not_inserted_index = []

    course_name = str(z.cell(7, 2).value).strip()
    course_code = str(z.cell(6, 2).value).strip()
    instructor = str(z.cell(8, 2).value).strip()


    #Extracting branch from filename
    first = filename[0:2]
    if(first == "CS"):
        branch = "CSE"
    elif(first == "EC"):
        branch = "ECE"
    elif(first == "ME"):
        branch = "ME"
    else:
        branch = "Common"


    #Extracting branch and sem from filename
    second = int(filename[2:3])
    sem = 2*second-1
    batch = 2020-second


    programme = 'B.Tech'
    credits = 2

    try: 
        course_obj = Course.objects.filter(course_name = course_name).get(course_details = instructor)
    except :
        course_obj = Course(
            course_name = course_name,
            course_details = instructor)
        course_obj.save()
    try:
        curriculum_obj = Curriculum.objects.filter(course_code = course_code).get(programme = programme)
    except:
        curriculum_obj = Curriculum(
            course_code = course_code,
            course_id = course_obj,
            credits = credits,
            course_type = 'Professional Core',
            programme = programme,
            branch = branch,
            batch = batch,
            sem = sem,
            floated = True)
        curriculum_obj.save()

    number_rows = z.nrows
    number_cols = z.ncols
    for i in range(10, number_rows):
        print(i)
        roll_no = int(z.cell(i, 1).value)
        name = str(z.cell(i,2).value)
        name = name.split()
        first_name = name[0]
        if (len(name)==1):
            last_name = name[0]
        else:
            last_name  = name[1]
        username = str(roll_no).strip()
        year, month = demo_date.year, int(demo_date.month)
        user_year = year - int(username[:4])
        if month >= 7 and month<=12:
            sem_odd_even = 'odd'
        else:
            sem_odd_even = 'even'
        if sem_odd_even == 'odd':
            sem  = user_year* 2 + 1
        else:
            sem = user_year * 2
        email = username + '@iiitdmj.ac.in'
        print(username)
        password= "hello123"
        dep = str(z.cell(i, 3).value).strip()
        try:
            user = User.objects.get(username = username)
        except:
            user = User.objects.create_user(
                username = username,
                password = 'hello123',
                first_name = first_name,
                last_name = last_name,
                email = email
            )
            user.save()
        print(user)
        try:
            holds_desg = HoldsDesignation.objects.get(user = user)
        except:
            holds_desg = HoldsDesignation(
                user = user,
                working = user,
                designation = Designation.objects.get(name = "student")
            )
            holds_desg.save()
        try:
            ext = ExtraInfo.objects.get(user = user)
        except:
            department_list = ["CSE","ECE","ME"]
            if(dep not in department_list):
                dep = "Design"
            ext = ExtraInfo(
            id = roll_no,
            user = user,
            sex = 'M',
            user_type = 'student',
            department = DepartmentInfo.objects.get(name = dep)
            )
            ext.save()
        try:
            st = Student.objects.get(id = ext)
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
        print (curriculum_obj)
        print (st)
        try:
            register_obj = Register.objects.filter(curr_id = curriculum_obj).get(student_id = st)
        except:
            register_obj = Register(
                curr_id = curriculum_obj,
                year = batch,
                student_id = st,
                semester = sem)
            register_obj.save()
            print(str(i) + "done")
    print(not_inserted_index)