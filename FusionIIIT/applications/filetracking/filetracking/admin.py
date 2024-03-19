from django.contrib import admin

# Register your models here.
from applications.filetracking.models import File, Tracking

admin.site.register(File)
admin.site.register(Tracking)
