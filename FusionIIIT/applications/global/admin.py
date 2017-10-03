from django.contrib import admin
from .models import Student, ExtraInfo, Staff, Faculty, DepartmentInfo, Designation

# Register your models here.

admin.site.register(Student)
admin.site.register(ExtraInfo)
admin.site.register(Staff)
admin.site.register(Faculty)
admin.site.register(DepartmentInfo)
admin.site.register(Designation)
