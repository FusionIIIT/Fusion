from django.contrib import admin

from .models import (Ambulance_request, Appointment, Complaint, Counter,
                     Doctor, Expiry, Hospital, Hospital_admit, Medicine,
                     Prescribed_medicine, Prescription, Schedule, Stock)

admin.site.register(Doctor)
admin.site.register(Appointment)
admin.site.register(Ambulance_request)
admin.site.register(Hospital_admit)
admin.site.register(Complaint)
admin.site.register(Stock)
admin.site.register(Counter)
admin.site.register(Expiry)
admin.site.register(Hospital)
admin.site.register(Prescription)
admin.site.register(Medicine)
admin.site.register(Prescribed_medicine)
admin.site.register(Schedule)
