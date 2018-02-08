from django.contrib import admin

from .models import (Ambulance_request, Appointment, Complaint, Doctor,
                     Hospital_admit, Medicine, Prescribed_medicine,
                     Prescription, Schedule, Stock, Stockinventory)

admin.site.register(Doctor)
admin.site.register(Appointment)
admin.site.register(Ambulance_request)
admin.site.register(Hospital_admit)
admin.site.register(Complaint)
admin.site.register(Stock)
admin.site.register(Stockinventory)
admin.site.register(Prescription)
admin.site.register(Medicine)
admin.site.register(Prescribed_medicine)
admin.site.register(Schedule)
