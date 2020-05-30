from django.contrib import admin

from .models import (Cpda_application, Cpda_tracking, Cpda_bill)

class Cpda_app_admin(admin.ModelAdmin):
    list_display = ('id', 'status', 'applicant', 'requested_advance', 'request_timestamp')
    list_filter = ('status',)
    # search_fields = []

admin.site.register(Cpda_application, Cpda_app_admin)
admin.site.register(Cpda_tracking)
admin.site.register(Cpda_bill)