from django.contrib import admin

# Register your models here.

from applications.otheracademic.models import GraduateSeminarFormTable,LeaveFormTable,BonafideFormTableUpdated,AssistantshipClaimFormStatusUpd,NoDues,LeavePG,LeavePGUpdTable

admin.site.register(LeaveFormTable)

admin.site.register(BonafideFormTableUpdated)
admin.site.register(GraduateSeminarFormTable)

admin.site.register(AssistantshipClaimFormStatusUpd)

admin.site.register(NoDues)
admin.site.register(LeavePGUpdTable)
admin.site.register(LeavePG)


