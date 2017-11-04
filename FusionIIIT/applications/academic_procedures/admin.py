from django.contrib import admin

from .models import BranchChange, FinalRegistrations, Register, Thesis, CoursesMtech

admin.site.register(Thesis)
admin.site.register(Register)
admin.site.register(FinalRegistrations)
admin.site.register(BranchChange)
admin.site.register(CoursesMtech)
