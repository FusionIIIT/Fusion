from django.contrib import admin

from .models import *
# from .models import CPDAReimbursementform
# Register your models here.

admin.site.register(Employee)
admin.site.register(EmpConfidentialDetails)
admin.site.register(EmpDependents)
admin.site.register(ForeignService)
admin.site.register(EmpAppraisalForm)
admin.site.register(WorkAssignemnt)
admin.site.register(LeaveBalance)
admin.site.register(LeaveForm)
admin.site.register(LTCform)
admin.site.register(Appraisalform)
admin.site.register(CPDAAdvanceform)    
admin.site.register(CPDAReimbursementform)