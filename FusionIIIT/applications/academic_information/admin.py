from django.contrib import admin

from .models import (Calendar, Course, Exam_timetable, Grades, Holiday,
                     Curriculum_Instructor, Meeting, Student, Student_attendance, Curriculum,
                     Timetable)

class CurriculumAdmin(admin.ModelAdmin):
    model = Curriculum
    search_fields = ('course_id__course_name',)

class CourseAdmin(admin.ModelAdmin):
    model = Course
    search_fields = ('course_name',)

class StudentAdmin(admin.ModelAdmin):
    model = Student
    raw_id_fields = ("student",)
    search_fields = ('id__user__username',)

admin.site.register(Student)
admin.site.register(Course,CourseAdmin)
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
