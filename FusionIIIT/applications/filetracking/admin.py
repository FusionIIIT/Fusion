from django.contrib import admin
from .models import File, Tracking


class FileAdmin(admin.ModelAdmin):
    list_display = ('id', 'uploader', 'designation',
                    'subject', 'upload_date', 'is_read')
    search_fields = ('uploader__user__username', 'subject', 'description')
    list_filter = ('is_read',)


admin.site.register(File, FileAdmin)


class TrackingAdmin(admin.ModelAdmin):
    list_display = ('file_id', 'current_id', 'receiver_id',
                    'receive_date', 'forward_date', 'is_read')
    search_fields = ('file_id__subject',
                     'current_id__user__username', 'receiver_id__username')
    list_filter = ('is_read',)


admin.site.register(Tracking, TrackingAdmin)
