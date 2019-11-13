import xlrd
import sys
import os
import django
sys.path.append(r'/home/fusion/Fusion/FusionIIIT/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'Fusion.settings'
django.setup()


from django.contrib.auth.models import User
from applications.academic_information.models import Student,Course, Curriculum
from applications.globals.models import ExtraInfo
from applications.academic_procedures.models import InitialRegistrations,StudentRegistrationCheck

filenames = os.listdir('/home/fusion/Fusion/FusionIIIT/dbinsertscripts/student_data/pre_registration')

for filename in filenames:
    excel = xlrd.open_workbook(
        os.path.join(
            os.path.dirname(__file__),
            'pre_registration',filename))
    programme = 'B.Tech'
    batch = int(filename[2:6])
    sem = (10-int(filename[5:6]))*2
    credits = 2
    z = excel.sheet_by_index(0)
    number_rows = z.nrows
    number_cols = z.ncols
    for i in range(1,number_rows):
        username = int(z.cell(i, 1).value)
        username = str(username).strip()
        print(username)
        try:
            user = User.objects.get(username=username)
            ext = ExtraInfo.objects.get(user=user)
            st = Student.objects.get(id=ext)
        except:
            print("CHALTE JAO")
        for j in range(4,number_cols):
            course_name = str(z.cell(i, j).value).strip()
            print(course_name)
            if(course_name!=''):
                course_code = course_name[0:6]
                course_code = course_code.strip()
                branch = course_code[0:2]
                if(branch=="CS"):
                    branch = "CSE"
                elif(branch=="ME"):
                    branch = "ME"
                elif(branch=="EC"):
                    branch = "ECE"
                elif(branch=="DS"):
                    branch = "DESIGN"
                else:
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
                    p = InitialRegistrations.objects.get(student_id__id = ext)
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