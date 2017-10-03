from django.contrib import admin

from .models import (Project, Language, Know, Skill, Has, Education,
                     Experience, Course, Publication, Achievement,
                     Coauthor, Patent, Coinventor, Interest, StudentPlacement,
                     MessageOfficer, NotifyStudent, PlacementStatus, PlacementRecord,
                     StudentRecord, ChairmanVisit, ContactCompany, PlacementSchedule)

# Register your models here.

admin.site.register(Project)
admin.site.register(Language)
admin.site.register(Know)
admin.site.register(Skill)
admin.site.register(Has)
admin.site.register(Education)
admin.site.register(Experience)
admin.site.register(Course)
admin.site.register(Publication)
admin.site.register(Achievement)
admin.site.register(Coauthor)
admin.site.register(Patent)
admin.site.register(Coinventor)
admin.site.register(Interest)
admin.site.register(StudentPlacement)
admin.site.register(MessageOfficer)
admin.site.register(NotifyStudent)
admin.site.register(PlacementStatus)
admin.site.register(PlacementRecord)
admin.site.register(StudentRecord)
admin.site.register(ChairmanVisit)
admin.site.register(ContactCompany)
admin.site.register(PlacementSchedule)
