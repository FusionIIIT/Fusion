from django.contrib import admin

from .models import (BranchChange, CoursesMtech, FinalRegistrations,
                     MinimumCredits, Register, Thesis)

class RegisterAdmin(admin.ModelAdmin):
    model = Register
    search_fields = ('curr_id__curriculum_id',)

admin.site.register(Thesis)
admin.site.register(Register,RegisterAdmin)
admin.site.register(FinalRegistrations)
admin.site.register(BranchChange)
admin.site.register(CoursesMtech)
admin.site.register(MinimumCredits)
