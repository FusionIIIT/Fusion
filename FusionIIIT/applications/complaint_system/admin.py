from django.contrib import admin

from .models import Caretaker, StudentComplain, ServiceProvider, Workers,  SectionIncharge, Warden, Complaint_Admin

admin.site.register(Caretaker)
admin.site.register(Workers)
admin.site.register(StudentComplain)
admin.site.register(ServiceProvider)
admin.site.register(SectionIncharge)
admin.site.register(Warden)
admin.site.register(Complaint_Admin)