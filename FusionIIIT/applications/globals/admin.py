from django.contrib import admin

from .models import (DepartmentInfo, Designation, ExtraInfo, Faculty, Feedback,
                     HoldsDesignation, Issue, IssueImage, Staff, ModuleAccess,
                     SystemAdminAccess, UserActivityLog)

# Register your models here.

class ExtraInfoAdmin(admin.ModelAdmin):
    model = ExtraInfo
    search_fields = ('user__username',)

class HoldsDesignationAdmin(admin.ModelAdmin):
    model = HoldsDesignation
    search_fields = ('user__username',)
    list_display = ('user', 'working', 'designation', 'start_time', 'end_time')
    list_filter = ('designation',)


class SystemAdminAccessAdmin(admin.ModelAdmin):
    model = SystemAdminAccess
    search_fields = ('user__username', 'assigned_by__username')
    list_display = ('user', 'assigned_by', 'created_at')

    def save_model(self, request, obj, form, change):
        if not obj.assigned_by_id:
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)


class UserActivityLogAdmin(admin.ModelAdmin):
    model = UserActivityLog
    list_display = ('created_at', 'user', 'role', 'action', 'method', 'resource')
    list_filter = ('role', 'method', 'created_at')
    search_fields = ('user__username', 'action', 'resource')
    readonly_fields = ('user', 'role', 'action', 'method', 'resource', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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
admin.site.register(SystemAdminAccess, SystemAdminAccessAdmin)
admin.site.register(UserActivityLog, UserActivityLogAdmin)
