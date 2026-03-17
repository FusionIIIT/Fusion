from django.contrib import admin

from .models import (Achievement, ChairmanVisit, Coauthor, Coinventor, Course,
                     Education, Experience, Has, Interest, MessageOfficer, Conference,
                     NotifyStudent, Patent, PlacementRecord, PlacementSchedule,
                     PlacementStatus, Project, Publication, Skill, Extracurricular,
                     StudentPlacement, StudentRecord, Role, CompanyDetails, Reference,
                     Company, JobPosting, JobApplication, InterviewSchedule,
                     InterviewPanel, JobOffer, Announcement, PlacementPolicy)


# Register your models here.
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('unique_id', 'project_name', 'project_status', 'sdate')


class SkillAdmin(admin.ModelAdmin):
    fields = ['skill']


class HasAdmin(admin.ModelAdmin):
    list_display = ('skill_id', 'unique_id')


class EducationAdmin(admin.ModelAdmin):
    list_display = ('unique_id', 'degree', 'institute', 'stream', 'sdate', 'edate')


class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('unique_id', 'title', 'status', 'company', 'location', 'sdate', 'edate')


class CourseAdmin(admin.ModelAdmin):
    list_display = ('unique_id', 'course_name', 'sdate', 'edate')


class PublicationAdmin(admin.ModelAdmin):
    list_display = ('unique_id', 'publication_title', 'publisher', 'publication_date')


class AchievementAdmin(admin.ModelAdmin):
    list_display = ('unique_id', 'achievement', 'achievement_type', 'issuer', 'date_earned')


class CoauthorAdmin(admin.ModelAdmin):
    list_display = ('publication_id', 'coauthor_name')


class InterestAdmin(admin.ModelAdmin):
    list_display = ('unique_id', 'interest')


class PatentAdmin(admin.ModelAdmin):
    list_display = ('unique_id', 'patent_name', 'patent_office', 'patent_date')


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
    list_display = ('company_name', 'location', 'visiting_date', 'timestamp')


class PlacementScheduleAdmin(admin.ModelAdmin):
    list_display = ('title', 'placement_date', 'location', 'time')


class ReferenceAdmin(admin.ModelAdmin):
    list_display = ('reference_name', 'post', 'email', 'mobile_number')


admin.site.register(Project, ProjectAdmin)
admin.site.register(Skill, SkillAdmin)
admin.site.register(Has, HasAdmin)
admin.site.register(Education, EducationAdmin)
admin.site.register(Experience, ExperienceAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Publication, PublicationAdmin)
admin.site.register(Achievement, AchievementAdmin)
admin.site.register(Coauthor, CoauthorAdmin)
admin.site.register(Patent, PatentAdmin)
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


class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'domain', 'contact_email', 'approval_status', 'created_at')
    list_filter = ('approval_status', 'domain')
    search_fields = ('name', 'contact_email')


class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'job_type', 'ctc', 'application_deadline', 'is_active')
    list_filter = ('job_type', 'is_active', 'company')
    search_fields = ('title', 'company__name')


class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'job_posting', 'status', 'applied_at')
    list_filter = ('status',)
    search_fields = ('student__id__user__username', 'job_posting__title')


class InterviewScheduleAdmin(admin.ModelAdmin):
    list_display = ('job_posting', 'date', 'time_slot', 'mode')
    list_filter = ('mode', 'date')


class InterviewPanelAdmin(admin.ModelAdmin):
    list_display = ('interview', 'application', 'result')
    list_filter = ('result',)


class JobOfferAdmin(admin.ModelAdmin):
    list_display = ('application', 'ctc_offered', 'status', 'response_deadline', 'extended_at')
    list_filter = ('status',)
    search_fields = ('application__student__id__user__username',)


class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'announcement_type', 'created_by', 'is_active', 'created_at')
    list_filter = ('announcement_type', 'is_active')
    search_fields = ('title',)


class PlacementPolicyAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_offers_allowed', 'allow_dream_company', 'is_active')
    list_filter = ('is_active',)


admin.site.register(Company, CompanyAdmin)
admin.site.register(JobPosting, JobPostingAdmin)
admin.site.register(JobApplication, JobApplicationAdmin)
admin.site.register(InterviewSchedule, InterviewScheduleAdmin)
admin.site.register(InterviewPanel, InterviewPanelAdmin)
admin.site.register(JobOffer, JobOfferAdmin)
admin.site.register(Announcement, AnnouncementAdmin)
admin.site.register(PlacementPolicy, PlacementPolicyAdmin)

