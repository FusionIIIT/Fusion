from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from .models import Programme, Discipline, Curriculum, Semester, Course, Batch, CourseSlot

# admin.site.site_title = "Programme and Curriculum Management"
# admin.site.site_header = "Programme and Curriculum Management"

class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category',)
    list_filter = ('category',)

class DisciplineAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('programmes', )

class CurriculumAdmin(admin.ModelAdmin):
    list_display = ('programme', 'name', 'version', 'working_curriculum', 'no_of_semester')
    list_filter = ('programme', 'working_curriculum',)

class SemesterAdmin(admin.ModelAdmin):
    list_display = ('curriculum', 'semester_no',)
    list_filter = ('curriculum',)

class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'credit',)

class BatchAdmin(admin.ModelAdmin):
    list_display = ('name', 'discipline', 'year', 'curriculum',)
    list_filter = ('discipline', 'year', 'curriculum',)

class CourseSlotAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'semester', 'course_slot_info',)
    list_filter = ('semester', 'type', 'for_batches', 'courses',)


# Register your models here.
admin.site.register(Discipline, DisciplineAdmin)
admin.site.register(Programme, ProgrammeAdmin)
admin.site.register(Curriculum, CurriculumAdmin)
admin.site.register(Semester, SemesterAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Batch, BatchAdmin)
admin.site.register(CourseSlot, CourseSlotAdmin)