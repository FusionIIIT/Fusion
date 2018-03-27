import django
import xlrd
from applications.globals.models import HoldsDesignation, Designation
from django.contrib.auth.models import User


class Data:
    def __init__(self, excel_file, row):
        self.file = xlrd.open_workbook(excel_file)
        self.row = row
        self.sheet = self.getSheet()

    def getSheet(self):
        return self.file.sheet_by_index(0)


    def fillHoldsDesignation(self):
        for i in range (1,self.row+1):
            try:
                user = User.objects.get(username=str(int(self.sheet.cell(i,1).value)))
                add=HoldsDesignation()
                add.user = user
                add.working = user
                add.designation = Designation.objects.get(name = 'student')
                add.save()
                print('saved')
            except:
                print(user.username,'unsucessful')

d = Data('dbinsertscripts/placement/B.Tech 2012.xlsx',131)
d.fillHoldsDesignation()
## exec(open('dbinsertscripts/placement/hold_designation_feed.py').read())
