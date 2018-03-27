import django
from applications.academic_information.models import Student
from applications.placement_cell.models import StudentPlacement

class Data:
    def __init__(self):
        self.uids = Student.objects.all()
    i = 0
    def fillStudentplacement(self):
        for uid in self.uids:
            add = StudentPlacement()
            add.unique_id = uid
            add.debar = 'NOT DEBAR'
            add.future_aspect = 'PLACEMENT'
            add.placed_type = 'NOT PLACED'
            add.save()
            i+=1
            print(str(i) + 'ho gaya save')

d = Data()
d.fillStudentplacement()
