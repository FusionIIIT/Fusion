"""
Django Admin Configuration for Notification Module
===================================================

This module registers notification models with Django Admin for management UI.
Admins can create, edit, and publish announcements from the Django admin panel.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import Announcements, AnnouncementRecipients


@admin.register(Announcements)
class AnnouncementsAdmin(admin.ModelAdmin):
    """Admin interface for managing announcements"""
    
    list_display = [
        'message_preview',
        'module',
        'target_group_display',
        'created_by',
        'status_display',
        'published_date',
        'created_date',
    ]
    
    list_filter = [
        'target_group',
        'module',
        'is_published',
        'is_active',
        'created_at',
    ]
    
    search_fields = [
        'message',
        'module',
        'created_by__username',
    ]
    
    fieldsets = (
        ('Content', {
            'fields': ('message', 'module'),
        }),
        ('Targeting', {
            'fields': (
                'target_group',
                'department',
                'batch',
            ),
            'description': 'Define who should see this announcement',
        }),
        ('Status', {
            'fields': (
                'is_published',
                'is_active',
                'published_at',
            ),
        }),
        ('Metadata', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = [
        'created_by',
        'created_at',
        'updated_at',
    ]
    
    ordering = ['-created_at']
    
    def message_preview(self, obj):
        """Display first 50 characters of message"""
        preview = obj.message[:50]
        if len(obj.message) > 50:
            preview += '...'
        return preview
    message_preview.short_description = 'Message'
    
    def target_group_display(self, obj):
        """Display target group with nice formatting"""
        colors = {
            'all_users': '#1f77b4',
            'students': '#ff7f0e',
            'faculty': '#2ca02c',
            'staff': '#d62728',
            'specific_users': '#9467bd',
            'department': '#8c564b',
            'batch': '#e377c2',
        }
        color = colors.get(obj.target_group, '#000000')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_target_group_display()
        )
    target_group_display.short_description = 'Target Group'
    
    def status_display(self, obj):
        """Display publication status"""
        if not obj.is_active:
            return format_html(
                '<span style="color: red; font-weight: bold;">Inactive</span>'
            )
        elif obj.is_published:
            return format_html(
                '<span style="color: green; font-weight: bold;">Published</span>'
            )
        else:
            return format_html(
                '<span style="color: orange; font-weight: bold;">Draft</span>'
            )
    status_display.short_description = 'Status'
    
    def published_date(self, obj):
        """Display published date"""
        if obj.published_at:
            return obj.published_at.strftime('%Y-%m-%d %H:%M')
        return '-'
    published_date.short_description = 'Published Date'
    
    def created_date(self, obj):
        """Display created date"""
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_date.short_description = 'Created Date'
    
    def save_model(self, request, obj, form, change):
        """Override save to set created_by and create notifications on publish"""
        if not change:  # New object
            obj.created_by = request.user
        
        # Auto-set published_at when publishing
        if obj.is_published and not obj.published_at:
            from django.utils import timezone
            obj.published_at = timezone.now()
        
        super().save_model(request, obj, form, change)
        
        # ALWAYS create notifications if the announcement is published
        # (this is simpler and more reliable than checking if it was just published)
        if obj.is_published:
            from .services import NotificationService
            count = NotificationService.create_announcement_notifications(obj)
            if count > 0:
                self.message_user(
                    request,
                    f'Announcement published! {count} notifications sent to users.'
                )
    
    actions = [
        'publish_announcement',
        'unpublish_announcement',
        'activate_announcement',
        'deactivate_announcement',
    ]
    
    def publish_announcement(self, request, queryset):
        """Action to publish selected announcements"""
        from django.utils import timezone
        from .services import NotificationService
        
        total_notifications = 0
        
        for announcement in queryset:
            if not announcement.is_published:
                announcement.is_published = True
                announcement.published_at = timezone.now()
                announcement.save()
                
                # Create notifications for this announcement
                count = NotificationService.create_announcement_notifications(announcement)
                total_notifications += count
        
        updated = queryset.count()
        self.message_user(
            request,
            f'{updated} announcement(s) published! {total_notifications} notifications sent in total.'
        )
    publish_announcement.short_description = 'Publish selected announcements'
    
    def unpublish_announcement(self, request, queryset):
        """Action to unpublish selected announcements"""
        updated = queryset.update(is_published=False)
        self.message_user(
            request,
            f'{updated} announcement(s) have been unpublished.'
        )
    unpublish_announcement.short_description = 'Unpublish selected announcements'
    
    def activate_announcement(self, request, queryset):
        """Action to activate selected announcements"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} announcement(s) have been activated.'
        )
    activate_announcement.short_description = 'Activate selected announcements'
    
    def deactivate_announcement(self, request, queryset):
        """Action to deactivate selected announcements"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} announcement(s) have been deactivated.'
        )
    deactivate_announcement.short_description = 'Deactivate selected announcements'


@admin.register(AnnouncementRecipients)
class AnnouncementRecipientsAdmin(admin.ModelAdmin):
    """Admin interface for managing announcement recipients"""
    
    list_display = [
        'announcement_preview',
        'user_info',
        'read_status',
        'read_date',
        'created_date',
    ]
    
    list_filter = [
        'is_read',
        'announcement__module',
        'created_at',
        'read_at',
    ]
    
    search_fields = [
        'announcement__message',
        'user__user__username',
        'user__user__email',
    ]
    
    fieldsets = (
        ('Assignment', {
            'fields': (
                'announcement',
                'user',
            ),
        }),
        ('Read Status', {
            'fields': (
                'is_read',
                'read_at',
            ),
        }),
        ('Metadata', {
            'fields': (
                'created_at',
            ),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = [
        'created_at',
    ]
    
    ordering = ['-created_at']
    
    def announcement_preview(self, obj):
        """Display announcement preview"""
        preview = obj.announcement.message[:40]
        if len(obj.announcement.message) > 40:
            preview += '...'
        return preview
    announcement_preview.short_description = 'Announcement'
    
    def user_info(self, obj):
        """Display user information"""
        return f"{obj.user.user.get_full_name()} ({obj.user.user.username})"
    user_info.short_description = 'Recipient'
    
    def read_status(self, obj):
        """Display read status"""
        if obj.is_read:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Read</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Unread</span>'
            )
    read_status.short_description = 'Status'
    
    def read_date(self, obj):
        """Display when announcement was read"""
        if obj.read_at:
            return obj.read_at.strftime('%Y-%m-%d %H:%M')
        return '-'
    read_date.short_description = 'Read Date'
    
    def created_date(self, obj):
        """Display when recipient was assigned"""
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_date.short_description = 'Assigned Date'
    
    actions = [
        'mark_as_read',
        'mark_as_unread',
    ]
    
    def mark_as_read(self, request, queryset):
        """Mark selected recipients as read"""
        from django.utils import timezone
        
        updated = queryset.update(
            is_read=True,
            read_at=timezone.now()
        )
        
        self.message_user(
            request,
            f'{updated} recipient(s) marked as read.'
        )
    mark_as_read.short_description = 'Mark selected as read'
    
    def mark_as_unread(self, request, queryset):
        """Mark selected recipients as unread"""
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(
            request,
            f'{updated} recipient(s) marked as unread.'
        )
    mark_as_unread.short_description = 'Mark selected as unread'
