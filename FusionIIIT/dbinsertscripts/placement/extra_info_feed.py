import django
import xlrd
from applications.globals.models import ExtraInfo, DepartmentInfo
from django.contrib.auth.models import User


class Data:
    def __init__(self, excel_file, row):
        self.file = xlrd.open_workbook(excel_file)
        self.row = row
        self.sheet = self.getSheet()

    def getSheet(self):
        return self.file.sheet_by_index(0)


    def fillExtrainfo(self):
        for i in range (1,self.row+1):
            try:
                user = User.objects.get(username=str(int(self.sheet.cell(i,1).value)))
                add=ExtraInfo()
                add.id = user.username
                add.user = user
                add.age = 21
                add.address = "ghar"
                add.phone_no = 9999999999
                add.user_type = 'student'
                dept = self.sheet.cell(i,3).value.strip()
                add.department = DepartmentInfo.objects.get(name=dept)
                add.about_me = "i am fine"
                add.save()
                print('saved')
            except:
                print(user.username,'unsucessful')

d = Data('dbinsertscripts/placement/B.Tech 2012.xlsx',131)
d.fillExtrainfo()
# exec(open('dbinsertscripts/placement/extra_info_feed.py').read())
