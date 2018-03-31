from django.contrib import admin

from applications.leave import models

leave_models = (models.LeaveType, models.Leave, models.LeavesCount, models.LeaveRequest,
                models.LeaveSegment, models.ReplacementSegment, models.LeaveAdministrators,
                models.LeaveMigration)

admin.site.register(leave_models)
