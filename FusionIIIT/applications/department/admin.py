from django.contrib import admin

# Register your models here.
from .models import(Announcements, SpecialRequest,Department)

admin.site.register(Announcements)
admin.site.register(SpecialRequest)
admin.site.register(Department)