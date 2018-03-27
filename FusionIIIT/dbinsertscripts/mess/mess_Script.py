import xlrd
import os
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, Designation, HoldsDesignation
from applications.academic_information.models import Student
from applications.central_mess.models import Messinfo

vegexcel = xlrd.open_workbook(os.path.join(os.getcwd(), 'dbinsertscripts/veg_mess_list.xlsx'))
nvegexcel = xlrd.open_workbook(os.path.join(os.getcwd(), 'dbinsertscripts/nveg_mess_list.xlsx'))
z = vegexcel.sheet_by_index(0)
z1 = nvegexcel.sheet_by_index(0)

for i in range(2, 712):
	try:

		roll_no = int(z.cell(i, 1).value)
		unique_id = int(roll_no)
		user = User.objects.get(username=roll_no)
		extrainfo = ExtraInfo.objects.get(user=user)
		student = Student.objects.get(id=extrainfo)
		d = Designation.objects.get(name="student")
		k = HoldsDesignation.objects.create(
            user = user,
            working = user,
            designation = d
        )
		mess = Messinfo.objects.create(
			student_id = student,
			mess_option = 'mess2',

        )

		print (str(i) + "done")
	except Exception as e:
		print(e)
		print(i)


for i in range(2,667):
	try:
		roll_no = int(z1.cell(i, 1).value)
		unique_id = int(roll_no)
		user = User.objects.get(username=roll_no)
		extrainfo = ExtraInfo.objects.get(user=user)
		student = Student.objects.get(id=extrainfo)
		d = Designation.objects.get(name="student")
		k = HoldsDesignation.objects.create(
            user = user,
            working = user,
            designation = d
        )
		mess = Messinfo.objects.create(
			student_id = student,
			mess_option = 'mess1',
        )

		print (str(i) + "done")
	except Exception as e:
		print(e)
		print(i)

print(i)
# exec(open('dbinsertscripts/mess_Script.py').read())
