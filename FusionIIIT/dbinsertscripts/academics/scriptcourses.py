import xlrd
import os
from applications.academic_information.models import Course

excel = xlrd.open_workbook(os.path.join(os.getcwd(), 'dbinsertscripts/academics/Courses Information.xlsx'))
z = excel.sheet_by_index(0)
#print(z.cell(5,0))
#print(z.cell(12,2).value)
#file = xlrd.open_workbook(excel,'r')
nahihua = []
for i in range(1, 86):
    try:
        code = str(z.cell(i, 0).value)
        course_name = str(z.cell(i, 1).value)
        credits = int(z.cell(i, 3).value)
        sem = int(z.cell(i, 2).value)
        print(code,course_name,credits,sem)

        u = Course.objects.create(
            course_id = code,
            course_name = course_name,
            sem = sem,
            credits = credits,
            optional = False
        )
        print('done')
        print(i)
    except Exception as e:
        print(e)
        print(i)
        nahihua.append(i)
print(nahihua)
#exec(open("dbinsertscripts/academics/scriptcourses.py").read())
