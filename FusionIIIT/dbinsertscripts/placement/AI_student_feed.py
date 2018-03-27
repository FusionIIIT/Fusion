import django
import xlrd
from applications.globals.models import ExtraInfo
from applications.academic_information.models import Student


class Data:
    def __init__(self, excel_file, row):
        self.file = xlrd.open_workbook(excel_file)
        self.row = row
        self.sheet = self.getSheet()

    def getSheet(self):
        return self.file.sheet_by_index(0)


    def fillAIstudent(self):
        for i in range (1,self.row+1):
            try:
                id = ExtraInfo.objects.get(id=str(int(self.sheet.cell(i,1).value)))
                add=Student()
                add.id = id
                add.programme = 'B.Tech'
                add.cpi = 8.0
                add.category = "GEN"
                add.father_name = "Father"
                add.mother_name = "Mother"
                add.specialization = 'None'
                add.save()
                print('saved')
            except:
                print(user.username,'unsucessful')

d = Data('dbinsertscripts/placement/B.Tech 2012.xlsx',131)
d.fillAIstudent()
# exec(open('dbinsertscripts/placement/Al_student_feed.py').read())
