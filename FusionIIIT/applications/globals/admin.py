from django.contrib import admin

from .models import (DepartmentInfo, Designation, ExtraInfo, Faculty, Feedback,
                     HoldsDesignation, Issue, IssueImage, Staff,ModuleAccess)

# Register your models here.

class ExtraInfoAdmin(admin.ModelAdmin):
    model = ExtraInfo
    search_fields = ('user__username',)

class HoldsDesignationAdmin(admin.ModelAdmin):
    model = HoldsDesignation
    search_fields = ('user__username',)


admin.site.register(IssueImage)
admin.site.register(ExtraInfo, ExtraInfoAdmin)
admin.site.register(Issue)
admin.site.register(Feedback)
admin.site.register(Staff)
admin.site.register(Faculty)
admin.site.register(DepartmentInfo)
admin.site.register(Designation)
admin.site.register(ModuleAccess)
admin.site.register(HoldsDesignation, HoldsDesignationAdmin)


# Student profile records (models_profile.py), moved here from placement_cell.
from .models_profile import (Achievement, Course, Education, Experience, Has,  # noqa: E402
                             Patent, Project, Publication, Skill)


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


class PatentAdmin(admin.ModelAdmin):
    list_display = ('unique_id', 'patent_name', 'patent_office', 'patent_date')


admin.site.register(Project, ProjectAdmin)
admin.site.register(Skill, SkillAdmin)
admin.site.register(Has, HasAdmin)
admin.site.register(Education, EducationAdmin)
admin.site.register(Experience, ExperienceAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Publication, PublicationAdmin)
admin.site.register(Achievement, AchievementAdmin)
admin.site.register(Patent, PatentAdmin)
