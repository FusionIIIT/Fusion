from django.contrib import admin

from .models import *

class Cpda_app_admin(admin.ModelAdmin):
    list_display = ('__str__', 'status', 'requested_advance', 'request_timestamp')
    list_filter = ('status',)
    # search_fields = []

class Cpda_track_admin(admin.ModelAdmin):
    list_display = ('__str__', 'review_status', 'reviewer_id', 'reviewer_design')
    list_filter = ('review_status',)
    # search_fields = []

admin.site.register(Cpda_application, Cpda_app_admin)
admin.site.register(Cpda_tracking, Cpda_track_admin)
admin.site.register(Cpda_bill)

admin.site.register(Ltc_application)
admin.site.register(Ltc_tracking)
admin.site.register(Ltc_eligible_user)

admin.site.register(Establishment_variables)
