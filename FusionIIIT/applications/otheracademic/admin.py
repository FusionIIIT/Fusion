from django.contrib import admin

# Register your models here.
from applications.otheracademic.models import LeaveFormTable,GraduateSeminarForm,BonafideFormTable,BonafideFormTableUpdated,GraduateSeminarFormTable,AssistantshipClaimForm
admin.site.register(LeaveFormTable)
admin.site.register(GraduateSeminarForm)
admin.site.register(BonafideFormTable)
admin.site.register(BonafideFormTableUpdated)
admin.site.register(GraduateSeminarFormTable)
admin.site.register(AssistantshipClaimForm)

