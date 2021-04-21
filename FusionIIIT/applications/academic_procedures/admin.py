from django.contrib import admin

from .models import (BranchChange, CoursesMtech, InitialRegistration,
                     MinimumCredits, Register, Thesis,
                     StudentRegistrationChecks, FinalRegistration,
                     ThesisTopicProcess, FeePayments, TeachingCreditRegistration,
                     SemesterMarks, MarkSubmissionCheck,Dues,MTechGraduateSeminarReport,PhDProgressExamination,
                     AssistantshipClaim, CourseRequested,course_registration)


class RegisterAdmin(admin.ModelAdmin):
    model = Register
    search_fields = ('curr_id__course_code',)

class InitialRegistrationsAdmin(admin.ModelAdmin):
    model = InitialRegistration
    raw_id_fields = ("student_id",)
    search_fields = ('student_id__id__id',)

class StudentRegistrationCheckAdmin(admin.ModelAdmin):
    model = StudentRegistrationChecks
    raw_id_fields = ("student_id",)

admin.site.register(Thesis)
admin.site.register(Register,RegisterAdmin)
admin.site.register(InitialRegistration,InitialRegistrationsAdmin)
admin.site.register(BranchChange)
admin.site.register(CoursesMtech)
admin.site.register(MinimumCredits)
admin.site.register(StudentRegistrationChecks, StudentRegistrationCheckAdmin)
admin.site.register(FinalRegistration)
admin.site.register(ThesisTopicProcess)
admin.site.register(FeePayments)
admin.site.register(TeachingCreditRegistration)
admin.site.register(SemesterMarks)
admin.site.register(MarkSubmissionCheck)
admin.site.register(Dues)
admin.site.register(AssistantshipClaim)
admin.site.register(PhDProgressExamination)
admin.site.register(MTechGraduateSeminarReport)
admin.site.register(CourseRequested)
admin.site.register(course_registration)

