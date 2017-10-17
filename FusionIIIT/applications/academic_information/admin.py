from django.contrib import admin

from .models import (Calendar, Course, Exam_timetable, Grades, Holiday,
                     Instructor, Meeting, Student, Student_attendance,
                     Timetable)

admin.site.register(Student)
admin.site.register(Course)
admin.site.register(Instructor)
admin.site.register(Meeting)
admin.site.register(Exam_timetable)
admin.site.register(Timetable)
admin.site.register(Student_attendance)
admin.site.register(Grades)
admin.site.register(Calendar)
admin.site.register(Holiday)
