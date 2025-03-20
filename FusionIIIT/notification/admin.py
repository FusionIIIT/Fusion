from django.contrib import admin
from .models import Announcements, AnnouncementRecipients

# Customize the admin interface for Announcements
@admin.register(Announcements)
class AnnouncementsAdmin(admin.ModelAdmin):
    list_display = ('created_by', 'created_at', 'message', 'target_group', 'department', 'batch')
    search_fields = ('message', 'created_by__username', 'department')
    list_filter = ('target_group', 'department', 'created_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

# Customize the admin interface for AnnouncementRecipients
@admin.register(AnnouncementRecipients)
class AnnouncementRecipientsAdmin(admin.ModelAdmin):
    list_display = ('announcement', 'user')
    search_fields = ('announcement__message', 'user__user__username')
    list_filter = ('announcement__target_group',)

