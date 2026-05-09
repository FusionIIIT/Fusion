from django.contrib import admin

from .models import (
    AccessZone,
    BlacklistAuditLog,
    BlacklistEntry,
    ConfigChangeLog,
    DataOperationLog,
    DenialLog,
    EntryExitLog,
    EscortAssignment,
    HostAuthority,
    RegistrationQuota,
    SecurityIncident,
    SystemConfig,
    VIPActivityLog,
    VerificationLog,
    Visit,
    Visitor,
    VisitorLocation,
    VisitorPass,
    VisitorRequest,
    VisitingHours,
)

admin.site.register(Visitor)
admin.site.register(BlacklistEntry)
admin.site.register(Visit)
admin.site.register(VisitorPass)
admin.site.register(VerificationLog)
admin.site.register(DenialLog)
admin.site.register(EntryExitLog)
admin.site.register(SecurityIncident)
admin.site.register(VisitorRequest)
admin.site.register(HostAuthority)
admin.site.register(RegistrationQuota)
admin.site.register(AccessZone)
admin.site.register(VisitorLocation)
admin.site.register(BlacklistAuditLog)
admin.site.register(EscortAssignment)
admin.site.register(VIPActivityLog)
admin.site.register(SystemConfig)
admin.site.register(ConfigChangeLog)
admin.site.register(VisitingHours)
admin.site.register(DataOperationLog)
