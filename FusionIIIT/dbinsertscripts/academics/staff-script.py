import xlrd
import os
import django

sys.path.append(r'/mnt/g/Documents/django-projects/Fusion/FusionIIIT/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'Fusion.settings'
django.setup()
from applications.academic_information.models import Course, Student
from applications.academic_procedures.models import Register
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo,Staff, Faculty, HoldsDesignation, Designation, DepartmentInfo
from datetime import date
from applications.leave.models import LeaveAdministrators

excel = xlrd.open_workbook(os.path.join(os.getcwd(), 'Faculty-List.xlsx'))
z = excel.sheet_by_index(0)
nahihua = []
for i in range(1, 52):
    try:
        pfid = int(z.cell(i, 1).value)
        name = str(z.cell(i,2).value)
        dep = str(z.cell(i,4).value)
        sanc_aut = str(z.cell(i,5).value)
        sanc_officer = str(z.cell(i,6).value)
        email = str(z.cell(i,7).value)
        des = str(z.cell(i,3).value)
        print(des)
        at = 0
        for iz in range(0,len(email)):
            if(email[iz]=='@'):
                at = iz
                break
        username = str(email[0:at])
        print(username)
        dd = 0
        try:
            dd = DepartmentInfo.objects.get(name = dep)
        except:
            dd = DepartmentInfo.objects.create(name = dep)
        dess = 0
        try:
            dess = Designation.objects.get(name = des)
        except:
            dess = Designation.objects.create(name = des)
        print(dess)
        name = name.split()
        last_name = name[len(name)-1]
        first_name = ""
        for iz in range(0,len(name)-1):
            first_name += name[iz] + " ";
        print(first_name, last_name)
        u = User.objects.create_user(
                    username = username,
                    password = 'hello123',
                    first_name = first_name,
                    last_name = last_name,
                    email = email,
        )
        sex = "M"
        print(str(i) + " user creation done")
        datee = date(1985,2,22)
        f = ExtraInfo.objects.create(
            sex = sex,
            user = u,
            id = pfid,
            department = dd,
            date_of_birth = datee,
            about_me = 'Hello I am ' + first_name + last_name,
            user_type = 'staff',
            phone_no = 9999999999
        )
        print("extraInfoCreation done -> "+str(i))
        q = Staff.objects.create(
            id = f
        )
        print("Faculty bhi ho gaya"+  str(i))
        qz = HoldsDesignation.objects.create(
            user = u,
            working = u,
            designation = dess,
        )
        print("Globals done -> " + str(i))
        print(sanc_aut)
        print(sanc_officer)
        sa = ""
        so = ""
        try:
            sa = Designation.objects.get(name = str(sanc_aut))
        except:
            sa = Designation.objects.create(name = str(sanc_aut))
        try:
            so = Designation.objects.get(name = str(sanc_officer))
        except:
            so = Designation.objects.create(name = str(sanc_officer))
        k = LeaveAdministrators.objects.create(user=u,
                                                authority=sa,
                                                officer=so)
        print("Leave bhi ho gaya!" + str(i))

    except Exception as e:
        print(e)
        print(i)
        z = []
        z.append(e)
        z.append(i)
        nahihua.append(z)

print(nahihua)
#exec(open("dbinsertscripts/academics/staff-script.py").read())
