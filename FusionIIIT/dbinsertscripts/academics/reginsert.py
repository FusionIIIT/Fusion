import xlrd
import os
from applications.academic_information.models import Course, Student
from applications.academic_procedures.models import Register

excel = xlrd.open_workbook(os.path.join(os.getcwd(), 'dbinsertscripts/academics/registration.xlsx'))
z = excel.sheet_by_index(0)
#print(z.cell(5,0))
#print(z.cell(12,2).value)
#file = xlrd.open_workbook(excel,'r')
nahihua = []
for i in range(1, 8000):
    try:
        roll_no = int(z.cell(i, 0).value)
        course_code = str(z.cell(i,2).value)
        print(course_code)
        a1 = Course.objects.get(course_id = course_code)
        a2 = Student.objects.get(id = roll_no)
        print(a1,a2)
        semester = 2
        p = str(a2)
        print(p[0:4])
        if(p[0:4]=="2016"):
            semester = 4
        if(p[0:4]=="2015"):
            semester = 6
        if(p[0:4]=="2014"):
            semester = 8
        print(semester)
        u = Register.objects.create(
            r_id = int(i + 10),
            course_id = a1,
            year = 2018,
            student_id = a2,
            semester = semester
        )
        print('done')
        print(i)
    except Exception as e:
        print(e)
        print(i)
        nahihua.append(i)
print(nahihua)
#exec(open('dbinsertscripts/academics/reginsert.py').read())
