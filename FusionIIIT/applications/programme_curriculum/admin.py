from django.contrib import admin
from .models import Programme, Discipline, Curriculum, Semester, Course, Batch, CourseSlot

# admin.site.site_title = "Programme and Curriculum Management"
# admin.site.site_header = "Programme and Curriculum Management"

# Register your models here.
admin.site.register(Discipline)
admin.site.register(Programme)
admin.site.register(Curriculum)
admin.site.register(Semester)
admin.site.register(Course)
admin.site.register(Batch)
admin.site.register(CourseSlot)