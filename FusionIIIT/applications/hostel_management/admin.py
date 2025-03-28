from django.contrib import admin

from .models import *

admin.site.register(Hall)
admin.site.register(HallCaretaker)
admin.site.register(HallWarden)

admin.site.register(GuestRoomBooking)
admin.site.register(StaffSchedule)
admin.site.register(HostelNoticeBoard)
admin.site.register(HostelStudentAttendence)
admin.site.register(HallRoom)
admin.site.register(WorkerReport)
admin.site.register(HostelInventory)
admin.site.register(HostelFine)
admin.site.register(HostelLeave)
admin.site.register(HostelComplaint)
admin.site.register(StudentDetails)
admin.site.register(HostelAllotment)
admin.site.register(GuestRoom)
admin.site.register(HostelTransactionHistory)
admin.site.register(HostelHistory)

