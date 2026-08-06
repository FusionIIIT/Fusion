from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from .models import Programme, Discipline, Curriculum, Semester, Course, Batch, CourseSlot, CourseInstructor, NewProposalFile, Proposal_Tracking, Thesis
from .models_student_management import StudentBatchUpload, PhdStudentBatchUpload


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

class ThesisAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'discipline', 'programme_type', 'credit', 'working_thesis')
    list_filter = ('discipline', 'programme_type', 'working_thesis')

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
admin.site.register(Thesis, ThesisAdmin)
admin.site.register(Batch, BatchAdmin)
admin.site.register(CourseSlot, CourseSlotAdmin)
admin.site.register(CourseInstructor)
admin.site.register(NewProposalFile, NewProposalFileAdmin)
admin.site.register(Proposal_Tracking, ProposalTrackingAdmin)


@admin.register(PhdStudentBatchUpload)
class PhdStudentBatchUploadAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'roll_number', 'application_no', 'discipline',
        'admission_semester', 'year', 'admission_type',
        'gate_qualified', 'gate_rank', 'reported_status',
    )
    list_filter = ('discipline', 'year', 'admission_semester', 'reported_status', 'gate_qualified', 'category')
    search_fields = ('name', 'roll_number', 'application_no', 'institute_email', 'discipline')
    ordering = ['-year', 'admission_semester', 'roll_number']


@admin.register(StudentBatchUpload)
class StudentBatchUploadAdmin(admin.ModelAdmin):
    list_display = ('name', 'roll_number', 'programme_type', 'branch', 'year', 'reported_status')
    list_filter = ('programme_type', 'year', 'reported_status', 'category')
    search_fields = ('name', 'roll_number', 'jee_app_no', 'institute_email')