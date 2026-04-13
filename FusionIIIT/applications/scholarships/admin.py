from django.contrib import admin
from .models import (
    Award_and_scholarship, Release, Application, Mcm,
    Director_gold, Director_silver, Proficiency_dm, Previous_winner,
    ExtendedScholarshipType, ScholarshipApplication,
    Award, AwardRecipient, MeritList, MeritListEntry, ScholarshipEligibilityLog
)


@admin.register(Award_and_scholarship)
class AwardAndScholarshipAdmin(admin.ModelAdmin):
    list_display = ('award_name', 'award_type')
    search_fields = ('award_name',)


@admin.register(Release)
class ReleaseAdmin(admin.ModelAdmin):
    list_display = ('award', 'batch', 'programme', 'startdate', 'enddate', 'notif_visible')
    list_filter = ('award', 'programme', 'notif_visible')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'award', 'status', 'created_at')
    list_filter = ('status', 'award')
    search_fields = ('student__id__id',)


@admin.register(ExtendedScholarshipType)
class ExtendedScholarshipTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'amount', 'frequency', 'max_backlogs', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name',)
    filter_horizontal = ('applicable_programmes', 'applicable_batches')


@admin.register(ScholarshipApplication)
class ScholarshipApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'scholarship_type', 'academic_year', 'semester', 'status', 'application_date')
    list_filter = ('status', 'academic_year', 'scholarship_type')
    search_fields = ('student__id__id', 'scholarship_type__name')
    readonly_fields = ('application_date', 'category_at_application')


@admin.register(Award)
class GeneralAwardAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'prize_amount', 'certificate_provided', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name',)
    filter_horizontal = ('applicable_programmes',)


@admin.register(AwardRecipient)
class AwardRecipientAdmin(admin.ModelAdmin):
    list_display = ('student', 'award', 'academic_year', 'award_date', 'certificate_issued')
    list_filter = ('award', 'academic_year', 'certificate_issued')
    search_fields = ('student__id__id', 'award__name')


@admin.register(MeritList)
class MeritListAdmin(admin.ModelAdmin):
    list_display = ('batch', 'programme', 'academic_year', 'semester', 'generated_date')
    list_filter = ('batch', 'academic_year')


@admin.register(MeritListEntry)
class MeritListEntryAdmin(admin.ModelAdmin):
    list_display = ('merit_list', 'student', 'rank', 'cgpa', 'eligible_for_scholarships')
    list_filter = ('merit_list', 'eligible_for_scholarships')


admin.site.register(Mcm)
admin.site.register(Director_gold)
admin.site.register(Director_silver)
admin.site.register(Proficiency_dm)
admin.site.register(Previous_winner)
admin.site.register(ScholarshipEligibilityLog)
