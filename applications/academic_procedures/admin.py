from django.contrib import admin

from .models import (BranchChange, CoursesMtech, FeePayments, FinalRegistration, InitialRegistration,StudentRegistrationChecks,
                     MinimumCredits, Register, Thesis, CourseRequested,
                     ThesisTopicProcess, FeePayment, TeachingCreditRegistration,
                     SemesterMarks, MarkSubmissionCheck,Dues,MTechGraduateSeminarReport,PhDProgressExamination,AssistantshipClaim,MessDue,Assistantship_status, course_registration)

class RegisterAdmin(admin.ModelAdmin):
    model = Register
    search_fields = ('curr_id__course_code',)

admin.site.register(Thesis)
admin.site.register(Register,RegisterAdmin)
admin.site.register(BranchChange)
admin.site.register(CoursesMtech)
admin.site.register(MinimumCredits)
admin.site.register(ThesisTopicProcess)
admin.site.register(FeePayment)
admin.site.register(TeachingCreditRegistration)
admin.site.register(SemesterMarks)
admin.site.register(MarkSubmissionCheck)
admin.site.register(Dues)
admin.site.register(AssistantshipClaim)
admin.site.register(PhDProgressExamination)
admin.site.register(MTechGraduateSeminarReport)
admin.site.register(MessDue)
admin.site.register(Assistantship_status)
admin.site.register(FeePayments)
admin.site.register(CourseRequested)
admin.site.register(InitialRegistration)
admin.site.register(FinalRegistration)
admin.site.register(StudentRegistrationChecks)
admin.site.register(course_registration)
