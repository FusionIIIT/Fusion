import xlrd
import os
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, Designation, DepartmentInfo
from applications.academic_information.models import Student

excel = xlrd.open_workbook(os.path.join(os.getcwd(), 'dbinsertscripts/academics/StudentInformation.xlsx'))
z = excel.sheet_by_index(0)
#print(z.cell(5,0))
#print(z.cell(12,2).value)
#file = xlrd.open_workbook(excel,'r')

nahihua = []
for i in range(1, 1121):
    try:
        print('ye naya hai')
        roll_no = int(z.cell(i, 0).value)
        username = roll_no
        print("holw)")
        print(username)

        print(username)
        name = (str(z.cell(i, 1).value)).split()
        first_name = str(name[0])
        programme = str(z.cell(i,3).value)
        print(programme)
        last_name = ""
        if(len(name)>1):
            last_name = str(name[1])
        sex = 'M'
        print(first_name, last_name)
        unique_id = int(roll_no)
        designation = 'student'
        dep = str(z.cell(i, 2).value)
        print(dep)
        department = DepartmentInfo.objects.get(name = dep)
        print(department)
        user_type = 'student'
        email = str(z.cell(i, 4).value)
        print(email)
        u = User.objects.create_user(
            username = username,
            password = 'hello123',
            first_name = first_name,
            last_name = last_name,
            email = email,
        )

        k = ExtraInfo.objects.create(
            sex = sex,
            user = u,
            id = unique_id,
            department = department,
            age = 18,
            about_me = 'Hello I am ' + first_name + last_name,
            user_type = 'student',
            phone_no = 9999999999
        )

        z2 = Student.objects.create(
            id = k,
            programme = programme,
            cpi = 7.0,
            category = 'GEN',
            father_name = 'Mr.',
            mother_name = 'Mrs.',
            hall_no = 4,
            specialization = 'None'
        )

        print (str(i) + "done")
    except Exception as e:
        print(e)
        print(i)
        nahihua.append(i)

print(nahihua)



    # if __name__ == '__main__':
    #     # django.settings.configure()
    #     data = Data('data.xlsx')
    #     data.create_designations(data.get_departments())
    #     data.create_departments(data.get_departments())
    #     data.create_users()


"""
from feed_data import Data; data = Data('data.xlsx');
data.create_departments(data.get_departments());
data.create_designations(data.get_designations());
data.create_users();
exec(open('dbinsertscripts/academics/scriptstudent.py').read())
"""
