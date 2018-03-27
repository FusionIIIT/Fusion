import django
from applications.academic_information.models import Student
from applications.placement_cell.models import StudentPlacement

class Data:
    def __init__(self):
        self.uids = Student.objects.all()

    def fillStudentplacement(self):
        for uid in self.uids:
            try:
                add = StudentPlacement()
                add.unique_id = uid
                add.debar = 'NOT DEBAR'
                add.future_aspect = 'PLACEMENT'
                add.placed_type = 'NOT PLACED'
                add.save()
                print('saved')
            except:
                print("already exists")

d = Data()
d.fillStudentplacement()
# exec(open('dbinsertscripts/placement/placement_student_feed.py').read())
