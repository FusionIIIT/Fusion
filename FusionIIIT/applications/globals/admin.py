from django.contrib import admin

from .models import (DepartmentInfo, Designation, ExtraInfo, Faculty,
                     HoldsDesignation, Staff)

admin.site.register(ExtraInfo)
admin.site.register(Staff)
admin.site.register(Faculty)
admin.site.register(DepartmentInfo)
admin.site.register(Designation)
admin.site.register(HoldsDesignation)
