from django.contrib import admin

from .models import (DepartmentInfo, Designation, ExtraInfo, Faculty, Feedback,
                     HoldsDesignation, Issue, IssueImage, Staff,ModuleAccess)

# Register your models here.

class ExtraInfoAdmin(admin.ModelAdmin):
    model = ExtraInfo
    search_fields = ('user__username',)

class HoldsDesignationAdmin(admin.ModelAdmin):
    model = HoldsDesignation
    search_fields = ('user__username',)


admin.site.register(IssueImage)
admin.site.register(ExtraInfo, ExtraInfoAdmin)
admin.site.register(Issue)
admin.site.register(Feedback)
admin.site.register(Staff)
admin.site.register(Faculty)
admin.site.register(DepartmentInfo)
admin.site.register(Designation)
admin.site.register(ModuleAccess)
admin.site.register(HoldsDesignation, HoldsDesignationAdmin)
