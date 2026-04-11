from django.contrib import admin

# Register your models here.

from applications.otheracademic.models import GraduateSeminarFormTable,LeaveFormTable,BonafideFormTableUpdated,AssistantshipClaimFormStatusUpd,NoDues,LeavePG,LeavePGUpdTable
from applications.otheracademic.analytics_models import Analytics, Feedback, FeedbackHelpfulness, SystemHealthCheck, APICallLog
from applications.otheracademic.audit_models import AuditLog, NoDuesEscalation, NoDuesClearanceHistory

admin.site.register(LeaveFormTable)

admin.site.register(BonafideFormTableUpdated)
admin.site.register(GraduateSeminarFormTable)

admin.site.register(AssistantshipClaimFormStatusUpd)

admin.site.register(NoDues)
admin.site.register(LeavePGUpdTable)
admin.site.register(LeavePG)

# T14: Escalation & Reminders
admin.site.register(NoDuesEscalation)

# T16: Audit Logging
admin.site.register(AuditLog)
admin.site.register(NoDuesClearanceHistory)

# T22: Analytics Dashboard
admin.site.register(Analytics)

# T23: User Feedback System
admin.site.register(Feedback)
admin.site.register(FeedbackHelpfulness)

# T24: System Verification & Monitoring
admin.site.register(SystemHealthCheck)
admin.site.register(APICallLog)


