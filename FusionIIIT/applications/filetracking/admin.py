from django.contrib import admin

# Register your models here.
from applications.filetracking.models import LegacyFile as File, LegacyTracking as Tracking

admin.site.register(File)
admin.site.register(Tracking)
