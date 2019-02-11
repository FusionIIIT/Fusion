from django.contrib import admin

from .models import (Achievement, ChairmanVisit, Coauthor, Coinventor, Course,
                     Education, Experience, Has, Interest, MessageOfficer,
                     NotifyStudent, Patent, PlacementRecord, PlacementSchedule,
                     PlacementStatus, Project, Publication, Skill,
                     StudentPlacement, StudentRecord)


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
