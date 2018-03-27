import xlrd
import os
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation, DepartmentInfo


excel = xlrd.open_workbook(os.path.join(os.getcwd(), 'dbinsertscripts/healthcenter/Compounder-List.xlsx'))
z = excel.sheet_by_index(0)

for i in range(1, 4):
    try:
        empid = int(z.cell(i, 0).value)
        name = str(z.cell(i,1).value)
        dep = str(z.cell(i,2).value)
        email = str(z.cell(i,3).value)
        des = str(z.cell(i,4).value)
        print(dep,des)
        at = 0
        for i in range(0,len(email)):
            if(email[i]=='@'):
                at = i
                break
        username = str(email[0:at])
        print(username)
        dd = ""
        dess = ""
        try:
            dd = DepartmentInfo.objects.get(name = dep)
        except:
            dd = DepartmentInfo.objects.create(name = dep)
        try:
            dess = Designation.objects.get(name = des)
        except:
            dess = Designation.objects.create(name = des)
        name = name.split()
        last_name = name[len(name)-1]
        first_name = ""
        for i in range(0,len(name)-1):
            first_name += name[i]
        print(first_name,last_name)
        u = User.objects.create_user(
                    username = username,
                    password = 'hello123',
                    first_name = first_name,
                    last_name = last_name,
                    email = email,
        )
        sex = "M"
        print(str(i)+" user creation done")
        f = ExtraInfo.objects.create(
            sex = sex,
            user = u,
            id = empid,
            department = dd,
            age = 38,
            about_me = 'Hello I am ' + first_name + last_name,
            user_type = 'compounder',
            phone_no = 9999999999
        )
        print("extraInfoCreation done -> "+str(i))

        qz = HoldsDesignation.objects.create(
            user = u,
            working = u,
            designation = dess,
        )
        print("All done yippe -> " + str(i))
    except Exception as e:
        print(e)
        print(i)

#exec(open("dbinsertscripts/healthcenter/compounderscript.py").read())
