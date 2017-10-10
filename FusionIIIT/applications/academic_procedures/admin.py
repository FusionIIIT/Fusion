from django.contrib import admin

from .models import FinalRegistrations, Register, Thesis

admin.site.register(Thesis)
admin.site.register(Register)
admin.site.register(FinalRegistrations)
