import xlrd
import os
import datetime
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, Designation, DepartmentInfo
from applications.academic_information.models import Student
from applications.scholarships.models import Previous_winner, Award_and_scholarship

excel = xlrd.open_workbook(os.path.join(os.getcwd(), 'dbinsertscripts/scholarship/previous winner.xlsx'))
z = excel.sheet_by_index(0)

for i in range(1, 16):
    try:
       
        roll_no = int(z.cell(i, 0).value)
        username = roll_no
        email = str(roll_no)+"@iiitdmj.ac.in"
        name = (str(z.cell(i, 1).value)).split()
        first_name = str(name[0])
        programme = str(z.cell(i,3).value)
        last_name = ""
        if(len(name)>1):
            last_name = str(name[1])
        dep = str(z.cell(i, 2).value)
        department = DepartmentInfo.objects.get(name = dep)
        award = str(z.cell(i,1).value)
        award_name = Award_and_scholarship.objects.get(award_name = award)
        now = datetime.datetime.now()
        year = now.year
        
        u = User.objects.create_user(
            username = username,
            password = 'hello123',
            first_name = first_name,
            last_name = last_name,
            email = email,
        )

        k = ExtraInfo.objects.create(
            user = u,
            id = unique_id,
            department = department,

        )

        z2 = Student.objects.create(
            id = k,
            programme = programme,
        )
        z3 = Previous_winner.objects.create(
             student = z2,
             year = year,
             award_id = award_name,

        )
             

        print (str(i) + "done")
    except Exception as e:
        print(e)
        print(i)
        break

#exec(open("dbinsertscripts/academics/scholarship/scriptprevious_winners.py").read())


