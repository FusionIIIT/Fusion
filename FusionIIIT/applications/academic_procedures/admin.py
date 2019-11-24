from django.contrib import admin

from .models import (BranchChange, CoursesMtech, InitialRegistrations,
                     MinimumCredits, Register, Thesis,
                     StudentRegistrationCheck, FinalRegistrations,
                     ThesisTopicProcess, FeePayment, TeachingCreditRegistration,
                     SemesterMarks, MarkSubmissionCheck)

class RegisterAdmin(admin.ModelAdmin):
    model = Register
    search_fields = ('curr_id__course_code',)

class InitialRegistrationsAdmin(admin.ModelAdmin):
    model = InitialRegistrations
    search_fields = ('student_id__id__id',)

admin.site.register(Thesis)
admin.site.register(Register,RegisterAdmin)
admin.site.register(InitialRegistrationsAdmin)
admin.site.register(BranchChange)
admin.site.register(CoursesMtech)
admin.site.register(MinimumCredits)
admin.site.register(StudentRegistrationCheck)
admin.site.register(FinalRegistrations)
admin.site.register(ThesisTopicProcess)
admin.site.register(FeePayment)
admin.site.register(TeachingCreditRegistration)
admin.site.register(SemesterMarks)
admin.site.register(MarkSubmissionCheck)