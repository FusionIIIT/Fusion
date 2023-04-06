from django.contrib import admin

from .models import *

admin.site.register(Hall)
admin.site.register(HallCaretaker)
admin.site.register(HallWarden)
admin.site.register(GuestRoomDetail)
admin.site.register(GuestRoomBooking)
admin.site.register(StaffSchedule)
admin.site.register(HostelNoticeBoard)
admin.site.register(HostelStudentAttendence)
admin.site.register(HallRoom)
admin.site.register(WorkerReport)