from django.contrib import admin

from .models import Activity, Notification

# Register your models here.


admin.site.register(Notification)
admin.site.register(Activity)
