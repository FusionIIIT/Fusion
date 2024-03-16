from django.contrib import admin

# Register your models here.
from applications.otheracademic.models import GraduateSeminarFormTable,LeaveFormTable,BonafideFormTableUpdated,AssistantshipClaimFormStatusUpd
admin.site.register(LeaveFormTable)

admin.site.register(BonafideFormTableUpdated)
admin.site.register(GraduateSeminarFormTable)

admin.site.register(AssistantshipClaimFormStatusUpd)
