from django.contrib import admin

from .models import (Calendar, Course, Exam_timetable, Grades, Holiday,
                     Curriculum_Instructor, Meeting, Student, Student_attendance, Curriculum,
                     Timetable)

class CurriculumAdmin(admin.ModelAdmin):
    model = Curriculum
    search_fields = ('course_code',)

class CourseAdmin(admin.ModelAdmin):
    model = Course
    search_fields = ('course_name',)

class StudentAdmin(admin.ModelAdmin):
    model = Student
    search_fields = ('id__user__username',)

class Curriculum_InstructorAdmin(admin.ModelAdmin):
    model = Curriculum_Instructor
    search_fields = ('curriculum_id__course_code',)

admin.site.register(Student,StudentAdmin)
admin.site.register(Course,CourseAdmin)
admin.site.register(Curriculum_Instructor,Curriculum_InstructorAdmin)
admin.site.register(Meeting)
admin.site.register(Exam_timetable)
admin.site.register(Timetable)
admin.site.register(Student_attendance)
admin.site.register(Grades)
admin.site.register(Calendar)
admin.site.register(Holiday)
admin.site.register(Curriculum,CurriculumAdmin)

#Hello!
