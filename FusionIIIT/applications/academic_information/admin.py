from django.contrib import admin

from .models import (Calendar, Course, Exam_timetable, Grades, Holiday,
                     Curriculum_Instructor, Meeting, Student, Student_attendance, Curriculum,
                     Timetable)

class CurriculumAdmin(admin.ModelAdmin):
    model = Curriculum
    search_fields = ('course_id__course_name',)


admin.site.register(Student)
admin.site.register(Course)
admin.site.register(Curriculum_Instructor)
admin.site.register(Meeting)
admin.site.register(Exam_timetable)
admin.site.register(Timetable)
admin.site.register(Student_attendance)
admin.site.register(Grades)
admin.site.register(Calendar)
admin.site.register(Holiday)
admin.site.register(Curriculum,CurriculumAdmin)

#Hello!
