from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from .models import Programme, Discipline, Curriculum, Semester, Course, Batch, CourseSlot,CourseInstructor, NewProposalFile,Proposal_Tracking


class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)

class DisciplineAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('programmes', )

class CurriculumAdmin(admin.ModelAdmin):
    list_display = ('programme', 'name', 'version', 'working_curriculum', 'no_of_semester')
    list_filter = ('programme', 'working_curriculum',)

class SemesterAdmin(admin.ModelAdmin):
    list_display = ('curriculum', 'semester_no', 'instigate_semester', 'start_semester', 'end_semester')
    list_filter = ('curriculum',)

class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'credit',)

class BatchAdmin(admin.ModelAdmin):
    list_display = ('name', 'discipline', 'year', 'curriculum',)
    list_filter = ('discipline', 'year', 'curriculum',)

class CourseSlotAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'course_slot_info','semester')
    list_filter = ('type', 'courses',)
class NewProposalFileAdmin(admin.ModelAdmin):
    list_display = ('uploader','designation', 'code', 'name',)
    
class ProposalTrackingAdmin(admin.ModelAdmin):
    list_display = ('current_id','current_design', 'receive_id', 'receive_design',)

# Register your models here.
admin.site.register(Discipline, DisciplineAdmin)
admin.site.register(Programme, ProgrammeAdmin)
admin.site.register(Curriculum, CurriculumAdmin)
admin.site.register(Semester, SemesterAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Batch, BatchAdmin)
admin.site.register(CourseSlot, CourseSlotAdmin)
admin.site.register(CourseInstructor)
admin.site.register(NewProposalFile,NewProposalFileAdmin)
admin.site.register(Proposal_Tracking,ProposalTrackingAdmin)