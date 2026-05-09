from django.contrib import admin

from .models import Announcement, NotificationEventType, NotificationPreference


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display  = ("user", "module", "is_enabled", "updated_at")
    list_filter   = ("module", "is_enabled")
    search_fields = ("user__username",)
    ordering      = ("user", "module")


@admin.register(NotificationEventType)
class NotificationEventTypeAdmin(admin.ModelAdmin):
    list_display  = ("event_name", "module", "default_priority", "is_active", "registered_by", "created_at")
    list_filter   = ("module", "default_priority", "is_active")
    search_fields = ("event_name", "module", "registered_by__username")
    readonly_fields = ("event_id", "created_at")
    ordering      = ("module", "event_name")


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display  = ("title", "sender", "audience_type", "audience_value", "expiry_date", "created_at")
    list_filter   = ("audience_type",)
    search_fields = ("title", "sender__username", "message")
    readonly_fields = ("created_at",)
    ordering      = ("-created_at",)
