from django.contrib import admin

from .models import (DepartmentInfo, Designation, ExtraInfo, Faculty, Feedback,
                     HoldsDesignation, Issue, IssueImage, Staff)

# Register your models here.
admin.site.register(IssueImage)
admin.site.register(ExtraInfo)
admin.site.register(Issue)
admin.site.register(Feedback)
admin.site.register(Staff)
admin.site.register(Faculty)
admin.site.register(DepartmentInfo)
admin.site.register(Designation)
admin.site.register(HoldsDesignation)
