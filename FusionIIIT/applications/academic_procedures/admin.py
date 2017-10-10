from django.contrib import admin
from .models import Register, Thesis, FinalRegistrations

admin.site.register(Thesis)
admin.site.register(Register)
admin.site.register(FinalRegistrations)
