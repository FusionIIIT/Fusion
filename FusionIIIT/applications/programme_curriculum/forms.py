from django.db.models import fields
from django.forms import ModelForm
from .models import Programme, Discipline, Curriculum, Semester, Course, Batch, CourseSlot

class ProgrammeForm(ModelForm):
    class Meta:
        model = Programme
        fields = '__all__'

class DisciplineForm(ModelForm):
    class Meta:
        model = Discipline
        fields = '__all__'

class CurriculumForm(ModelForm):
    class Meta:
        model = Curriculum
        fields = '__all__'

class SemesterForm(ModelForm):
    class Meta:
        model = Semester
        fields = '__all__'

class CourseForm(ModelForm):
    class Meta:
        model = Course
        fields = '__all__'

class BatchForm(ModelForm):
    class Meta:
        model = Batch
        fields = '__all__'

class CourseSlotForm(ModelForm):
    class Meta:
        model = CourseSlot
        fields = '__all__'




# #
# from .models import ProgrammeList, CurriculumList, SemesterList, SemesterCourseList, CourseDetails

# class ProgrammeForm(ModelForm):  
#     class Meta:
#         model = ProgrammeList
#         fields = '__all__'

# class CurriculumForm(ModelForm):  
#     class Meta:
#         model = CurriculumList
#         fields = '__all__'

# class CoursesForm(ModelForm):   
#     class Meta:
#         model = CourseDetails
#         # fields = ("course_code",
#         # "title","contact_hours_Lecture",
#         # "contact_hours_Tutorial",
#         # "contact_hours_Lab",
#         # "contact_hours_Discussion",
#         # "contact_hours_Project",
#         # "syllabus",
#         # "evaluation_schema_quiz1",
#         # "evaluation_schema_midsem",
#         # "evaluation_schema_quiz2",
#         # "evaluation_schema_lab",
#         # "evaluation_schema_endsem",
#         # "ref_books")
#         fields = "__all__"
#         # exclude = ("credits",)

# class SemesterForm(ModelForm):
#     class Meta:
#         model = SemesterList
#         fields = ("semester_no","curriculum_id")

# class SemesterCourseForm(ModelForm):
    
#     class Meta:
#         model = SemesterCourseList
#         fields = ("course_id",)


# class CourseForm(ModelForm):   
#     class Meta:
#         model = CourseDetails
#         fields = ("credits",)
