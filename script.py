import xlrd
import os

from django.contrib.auth.models import User
from application.globals.models import ExtraInfo, Designation, DepartmentInfo
import user_app

a = 0

class Data:

    def __init__(self, excel_file):
        self.file = xlrd.open_workbook(os.path.join(os.getcwd(), excel_file))
        self.sheet = self.file()

    def create_users(self):
        for i in range(2, 1121):
            try:
                roll_no = self.get_unicode(self.sheet.cell(i, 0))
                username = roll_no
                email = roll_no+"@iiitdmj.ac.in"
                print(username)
                name = self.get_unicode(self.sheet.cell(i, 1)).split()
                first_name = name[1]
                last_name = " ".join(name[2:])
                sex = 'Male'
                print(first_name)
                print(last_name)
                unique_id = int(roll_no)
                designation = 'student'
                department = self.get_unicode(self.staff_sheet.cell(i, 2))
                department = DepartmentInfo.objects.get(name=department)
                user_type = 'student'

                u = User.objects.create_user(
                    username = username,
                    password = 'hello123',
                    first_name = first_name,
                    last_name = last_name,
                    email = email,
                )

                u.extrainfo.sex = sex
                u.extrainfo.unique_id = unique_id
                u.extrainfo.department = department
                u.extrainfo.user_type = user_type
                u.extrainfo.designation = designation

                u.extrainfo.aboutme = 'Hello I am'+first_name

                u.extrainfo.save()

            except Exception as e:
                print(e)


    def get_unicode(self, string):
        return string.value.strip()


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
"""
