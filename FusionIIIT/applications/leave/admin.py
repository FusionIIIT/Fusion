from django.contrib import admin

from applications.leave import models

leave_models = (models.LeaveType, models.Leave, models.LeavesCount, models.LeaveRequest,
                models.LeaveSegment, models.ReplacementSegment, models.LeaveAdministrators,
                models.LeaveMigration, models.RestrictedHoliday, models.ClosedHoliday, 
                models.VacationHoliday, models.LeaveSegmentOffline, models.LeaveOffline, 
                models.ReplacementSegmentOffline)

admin.site.register(leave_models)

elm_models = (models.ELMPolicy, models.ELMCalendar, models.ELMCalendarDate,
              models.ELMRouteConfiguration, models.ELMWorkflowTask,
              models.ELMAccountTransaction, models.ELMChangeRequest,
              models.ELMYearEndRun, models.ELMActionLog)
admin.site.register(elm_models)
