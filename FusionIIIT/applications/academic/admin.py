from django.contrib import admin

from .models import (Course, Instructor, Meeting, Exam_timetable, Timetable, Student_attendance, Grades, Calendar, Holiday)

# Register your models here.

admin.site.register(Course)
admin.site.register(Instructor)
admin.site.register(Meeting)
admin.site.register(Exam_timetable)
admin.site.register(Timetable)
admin.site.register(Student_attendance)
admin.site.register(Grades)
admin.site.register(Calendar)
admin.site.register(Holiday)