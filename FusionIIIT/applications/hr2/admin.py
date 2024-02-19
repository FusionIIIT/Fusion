from django.contrib import admin

from .models import Employee,EmpConfidentialDetails,ForeignService,EmpDependents,EmpAppraisalForm,WorkAssignemnt, LTCform

# Register your models here.

admin.site.register(Employee)
admin.site.register(EmpConfidentialDetails)
admin.site.register(EmpDependents)
admin.site.register(ForeignService)
admin.site.register(EmpAppraisalForm)
admin.site.register(WorkAssignemnt)
admin.site.register(LTCform)