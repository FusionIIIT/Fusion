import django
import xlrd
from applications.placement_cell.models import StudentRecord,PlacementRecord
from applications.academic_information.models import Student


class Data:
    def __init__(self, excel_file, row):
        self.file = xlrd.open_workbook(excel_file)
        self.row = row
        self.sheet = self.getSheet()

    def getSheet(self):
        return self.file.sheet_by_index(0)


    def fillStudentrecord(self):
        for i in range (1,self.row+1):
            #print(self.sheet.cell(i,1).value)
            try:
                print(int(self.sheet.cell(i,1).value))
                sid=Student.objects.get(id=int(self.sheet.cell(i,1).value))
                rid=PlacementRecord.objects.get(name=self.sheet.cell(i,4).value.strip())
                add=StudentRecord()
                add.unique_id=sid
                add.record_id=rid
                add.save()
                print('saved')
            except:
                print('failed')

d = Data('dbinsertscripts/placement/B.Tech 2012.xlsx',131)
d.fillStudentrecord()
# exec(open('dbinsertscripts/placement/student_record_feed.py').read())
