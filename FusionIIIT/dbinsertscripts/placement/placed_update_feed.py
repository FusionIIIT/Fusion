import os
import django

sys.path.append(r'/mnt/g/Documents/django-projects/Fusion/FusionIIIT/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'Fusion.settings'
django.setup()
from applications.academic_information.models import Student
from applications.placement_cell.models import StudentPlacement

class Data:
    def __init__(self, excel_file, row):
        self.file = xlrd.open_workbook(excel_file)
        self.row = row
        self.sheet = self.getSheet()

    def getSheet(self):
        return self.file.sheet_by_index(0)

    def changePlacedtype(self):
        for i in range (1,self.row+1):
            user = User.objects.get(username=str(int(self.sheet.cell(i,1).value)))
            uid = Student.objects.get(id = ExtraInfo.objects.get(id=user))
            add=StudentPlacement.objects.get(unique_id = uid)
            add.placed_type = 'PLACED'
            add.save()
            print('saved')

d = Data('B.Tech 2012.xlsx',131)
d.changePlacedtype()
# exec(open('dbinsertscripts/placement/placed_update_feed.py').read())
