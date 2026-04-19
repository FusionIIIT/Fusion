from django.contrib import admin
from .models import (
    Employee, EmpConfidentialDetails, EmpDependents, ForeignService, 
    EmpAppraisalForm, WorkAssignemnt, LTCform, CPDAAdvanceform, 
    CPDAReimbursementform, LeaveForm, LeaveClaim, LeaveBalance, 
    LeavePerYear, Appraisalform
)

# Register existing models
admin.site.register(Employee)
admin.site.register(EmpConfidentialDetails)
admin.site.register(EmpDependents)
admin.site.register(ForeignService)
admin.site.register(EmpAppraisalForm)
admin.site.register(WorkAssignemnt)
admin.site.register(LTCform)
admin.site.register(CPDAAdvanceform)
admin.site.register(CPDAReimbursementform)
admin.site.register(LeaveForm)
admin.site.register(LeaveClaim)
admin.site.register(LeaveBalance)
admin.site.register(LeavePerYear)
admin.site.register(Appraisalform)