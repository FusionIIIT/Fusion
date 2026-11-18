from django.contrib import admin

from .models import (ChairmanVisit, Coauthor, Coinventor, Interest, MessageOfficer, Conference,
                     NotifyStudent, PlacementRecord, PlacementSchedule,
                     PlacementStatus, Extracurricular,
                     StudentPlacement, StudentRecord, Role, CompanyDetails, Reference)

# The student profile models (Project, Skill, Has, Education, Experience, Course,
# Publication, Achievement, Patent) are registered in globals/admin.py.


# Register your models here.
class CoauthorAdmin(admin.ModelAdmin):
    list_display = ('publication_id', 'coauthor_name')


class InterestAdmin(admin.ModelAdmin):
    list_display = ('unique_id', 'interest')


class CoinventorAdmin(admin.ModelAdmin):
    list_display = ('patent_id', 'coinventor_name')


class StudentPlacementAdmin(admin.ModelAdmin):
    list_display = ('unique_id', 'debar', 'future_aspect', 'placed_type', 'placement_date',
                    'package')


class MessageOfficerAdmin(admin.ModelAdmin):
    fields = ['timestamp']


class NotifyStudentAdmin(admin.ModelAdmin):
    list_display = ('placement_type', 'company_name', 'ctc')


class PlacementStatusAdmin(admin.ModelAdmin):
    list_display = ('notify_id', 'unique_id', 'placed', 'timestamp')


class PlacementRecordAdmin(admin.ModelAdmin):
    list_display = ('placement_type', 'name', 'ctc', 'year', 'test_score', 'test_type')


class StudentRecordAdmin(admin.ModelAdmin):
    list_display = ('record_id', 'unique_id')


class ChairmanVisitAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'location', 'visiting_date', 'start_date', 'end_date', 'timestamp')


class PlacementScheduleAdmin(admin.ModelAdmin):
    list_display = ('title', 'placement_date', 'location', 'time')


class ReferenceAdmin(admin.ModelAdmin):
    list_display = ('reference_name', 'post', 'email', 'mobile_number')


admin.site.register(Coauthor, CoauthorAdmin)
admin.site.register(Coinventor, CoinventorAdmin)
admin.site.register(Interest, InterestAdmin)
admin.site.register(StudentPlacement, StudentPlacementAdmin)
admin.site.register(MessageOfficer, MessageOfficerAdmin)
admin.site.register(NotifyStudent, NotifyStudentAdmin)
admin.site.register(PlacementStatus, PlacementStatusAdmin)
admin.site.register(PlacementRecord, PlacementRecordAdmin)
admin.site.register(StudentRecord, StudentRecordAdmin)
admin.site.register(ChairmanVisit, ChairmanVisitAdmin)
admin.site.register(PlacementSchedule, PlacementScheduleAdmin)
admin.site.register(Role)
admin.site.register(CompanyDetails)
admin.site.register(Reference)
admin.site.register(Extracurricular)
admin.site.register(Conference)
