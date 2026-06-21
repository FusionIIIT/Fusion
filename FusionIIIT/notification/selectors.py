"""
Notification Selectors Module
==============================

This module contains read-only database queries for notifications and announcements.
Selectors should be used for all GET operations and data fetching.
They provide a clean interface for querying notification data.

Usage Example:
    from notification.selectors import get_user_notifications, get_announcements_for_user
    
    notifications = get_user_notifications(user=request.user)
    announcements = get_announcements_for_user(user=request.user)
"""

import logging
import re
from django.db.models import Q, QuerySet, Prefetch
from django.contrib.auth.models import User
from notifications.models import Notification
from .models import Announcements, AnnouncementRecipients
from applications.globals.models import ExtraInfo
from typing import Optional, List

logger = logging.getLogger(__name__)


# ============================================================================
# NOTIFICATION QUERIES
# ============================================================================

def get_user_notifications(
    user: User,
    unread_only: bool = False,
    include_deleted: bool = False,
    limit: Optional[int] = None,
    sort_by_priority: bool = True
) -> QuerySet:
    """
    Get all notifications for a user with optional priority-based sorting (T-NT-05).
    
    Args:
        user: User object
        unread_only: If True, return only unread notifications
        include_deleted: If True, include deleted notifications
        limit: Maximum number of notifications to return
        sort_by_priority: If True, sort by priority first, then timestamp
    
    Returns:
        QuerySet of Notification objects
    """
    # Use select_related to prevent N+1 queries on actor (sender) field
    queryset = Notification.objects.filter(recipient=user).select_related('actor')
    
    if not include_deleted:
        queryset = queryset.filter(deleted=False)
    
    if unread_only:
        queryset = queryset.filter(unread=True)
    
    # T-NT-05: Sort by priority first, then by timestamp
    if sort_by_priority:
        # Fallback to Python sorting since jsonfield backend doesn't support order_by('-data__priority')
        queryset = queryset.order_by('-timestamp')
        notifications = list(queryset)
        notifications.sort(key=lambda n: (
            n.data.get('priority', 4) if isinstance(n.data, dict) else 4, 
            -n.timestamp.timestamp()
        ))
        if limit:
            notifications = notifications[:int(limit)]
        return notifications
    else:
        queryset = queryset.order_by('-timestamp')
        if limit:
            queryset = queryset[:int(limit)]
        return queryset


def get_notification_by_id(notification_id: int, user: User) -> Optional[Notification]:
    """
    Get a specific notification for a user.
    
    Args:
        notification_id: Notification ID
        user: User object
    
    Returns:
        Notification object or None if not found
    """
    try:
        return Notification.objects.get(id=notification_id, recipient=user)
    except Notification.DoesNotExist:
        return None


def get_user_unread_count(user: User) -> int:
    """
    Get count of unread notifications for a user.
    
    Args:
        user: User object
    
    Returns:
        Count of unread notifications
    """
    return Notification.objects.filter(
        recipient=user,
        unread=True,
        deleted=False
    ).count()


def get_notifications_by_module(
    user: User,
    module: str,
    unread_only: bool = False
) -> QuerySet:
    """
    Get notifications for a specific module.
    
    Args:
        user: User object
        module: Module name (e.g., 'Leave Module')
        unread_only: If True, return only unread notifications
    
    Returns:
        QuerySet of notifications from specific module
    """
    queryset = Notification.objects.filter(
        recipient=user,
        data__module=module,
        deleted=False
    )
    
    if unread_only:
        queryset = queryset.filter(unread=True)
    
    return queryset.order_by('-timestamp')


def get_notifications_by_sender(
    recipient: User,
    sender: User
) -> QuerySet:
    """
    Get all notifications sent by a specific user to recipient.
    
    Args:
        recipient: User receiving notifications
        sender: User sending notifications
    
    Returns:
        QuerySet of notifications from specific sender
    """
    return Notification.objects.filter(
        recipient=recipient,
        actor_object_id=sender.id,
        deleted=False
    ).order_by('-timestamp')


def get_recent_notifications(
    user: User,
    days: int = 7,
    limit: int = 50
) -> QuerySet:
    """
    Get recent notifications from the last N days.
    
    Args:
        user: User object
        days: Number of days to look back
        limit: Maximum number of notifications
    
    Returns:
        QuerySet of recent notifications
    """
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    return Notification.objects.filter(
        recipient=user,
        timestamp__gte=cutoff_date,
        deleted=False
    ).order_by('-timestamp')[:limit]


# ============================================================================
# ANNOUNCEMENT QUERIES
# ============================================================================

def get_announcements_for_user(user: User) -> QuerySet:
    """
    Get all announcements visible to the user based on their profile.
    Sorts by priority first, then by creation date (T-NT-05: Priority-based sorting).
    Filters out expired announcements (T-NT-02: Automatic expiry).
    
    Args:
        user: User object
    
    Returns:
        QuerySet of Announcements
    """
    from django.utils import timezone
    
    # T-NT-02: Filter out expired announcements
    announcements = Announcements.objects.filter(
        is_active=True,
        is_published=True
    ).select_related('created_by', 'department').exclude(
        expiry_date__lt=timezone.now()  # Exclude if expiry_date is in the past
    )
    
    # Staff and admins see all announcements
    if user.is_staff or user.is_superuser:
        # T-NT-05: Sort by priority (lower number = higher priority), then by created_at
        return announcements.order_by('priority', '-created_at')
    
    # Get user's profile information
    try:
        extra_info = user.extrainfo
    except ExtraInfo.DoesNotExist:
        return announcements.filter(target_group='all_users').order_by('priority', '-created_at')
    
    user_type = extra_info.user_type
    department = extra_info.department
    username = (user.username or '').upper()
    
    # Build filter query
    filter_query = Q(target_group='all_users')
    
    # Filter by user type
    if user_type == 'student':
        filter_query |= Q(target_group='students')

        # Roll-number based targeting via `batch` code
        if 'BCS' in username:
            filter_query |= Q(target_group='batch', batch__iexact='BCS')
        if 'BEC' in username:
            filter_query |= Q(target_group='batch', batch__iexact='BEC')
        if 'BME' in username:
            filter_query |= Q(target_group='batch', batch__iexact='BME')
        if re.match(r'^\d{2}B[A-Z]{2}\d{3}$', username):
            filter_query |= Q(target_group='batch', batch__iexact='UG')
        if re.match(r'^\d{2}M[A-Z]{2}\d{3}$', username):
            filter_query |= Q(target_group='batch', batch__iexact='PG')
        
        # Filter by batch if student
        if hasattr(extra_info, 'student') and extra_info.student:
            filter_query |= Q(
                target_group='batch',
                batch=extra_info.student.batch
            )
    elif user_type == 'faculty':
        filter_query |= Q(target_group='faculty')
    elif user_type == 'staff':
        filter_query |= Q(target_group='staff')
    
    # Filter by department
    if department:
        filter_query |= Q(
            target_group='department',
            department=department
        )
    
    # Filter by specific users
    filter_query |= Q(
        target_group='specific_users',
        recipients__user=extra_info
    )
    
    # T-NT-05: Sort by priority first, then by created_at
    return announcements.filter(filter_query).distinct().order_by('priority', '-created_at')


def get_announcements_by_module(
    module: str,
    is_published: bool = True
) -> QuerySet:
    """
    Get all announcements for a specific module.
    
    Args:
        module: Module name
        is_published: If True, only published announcements
    
    Returns:
        QuerySet of announcements
    """
    queryset = Announcements.objects.filter(
        module=module,
        is_active=True
    )
    
    if is_published:
        queryset = queryset.filter(is_published=True)
    
    return queryset.order_by('-created_at')


def get_announcements_by_department(
    department_id: int,
    is_published: bool = True
) -> QuerySet:
    """
    Get all announcements for a specific department.
    
    Args:
        department_id: Department ID
        is_published: If True, only published announcements
    
    Returns:
        QuerySet of announcements
    """
    queryset = Announcements.objects.filter(
        department_id=department_id,
        is_active=True
    )
    
    if is_published:
        queryset = queryset.filter(is_published=True)
    
    return queryset.order_by('-created_at')


def get_announcements_for_batch(
    batch: str,
    is_published: bool = True
) -> QuerySet:
    """
    Get all announcements for a specific batch.
    
    Args:
        batch: Batch code
        is_published: If True, only published announcements
    
    Returns:
        QuerySet of announcements
    """
    queryset = Announcements.objects.filter(
        batch=batch,
        target_group='batch',
        is_active=True
    )
    
    if is_published:
        queryset = queryset.filter(is_published=True)
    
    return queryset.order_by('-created_at')


def get_announcement_by_id(announcement_id: int) -> Optional[Announcements]:
    """
    Get a specific announcement by ID.
    
    Args:
        announcement_id: Announcement ID
    
    Returns:
        Announcement object or None
    """
    try:
        return Announcements.objects.get(id=announcement_id)
    except Announcements.DoesNotExist:
        return None


def get_announcements_by_creator(user: User) -> QuerySet:
    """
    Get all announcements created by a specific user.
    
    Args:
        user: User object (creator)
    
    Returns:
        QuerySet of announcements
    """
    return Announcements.objects.filter(created_by=user).order_by('-created_at')


def get_user_announcement_recipients(announcement: Announcements) -> QuerySet:
    """
    Get all specific users who should receive an announcement.
    
    Args:
        announcement: Announcement object
    
    Returns:
        QuerySet of AnnouncementRecipients
    """
    return AnnouncementRecipients.objects.filter(
        announcement=announcement
    ).select_related('user__user')


def get_unread_announcements_for_user(user: User) -> QuerySet:
    """
    Get unread announcements for a user (for specific_users target group).
    
    Args:
        user: User object
    
    Returns:
        QuerySet of unread announcements
    """
    try:
        extra_info = user.extrainfo
    except ExtraInfo.DoesNotExist:
        return AnnouncementRecipients.objects.none()
    
    return AnnouncementRecipients.objects.filter(
        user=extra_info,
        is_read=False,
        announcement__is_published=True,
        announcement__is_active=True
    ).select_related('announcement').order_by('-created_at')


def get_recent_announcements(days: int = 7, limit: int = 10) -> QuerySet:
    """
    Get recent announcements from the last N days.
    
    Args:
        days: Number of days to look back
        limit: Maximum number of announcements
    
    Returns:
        QuerySet of recent announcements
    """
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    return Announcements.objects.filter(
        created_at__gte=cutoff_date,
        is_active=True,
        is_published=True
    ).order_by('-created_at')[:limit]


def get_announcement_count_by_user(user: User) -> int:
    """
    Get total count of announcements visible to user.
    
    Args:
        user: User object
    
    Returns:
        Count of announcements
    """
    return get_announcements_for_user(user).count()


# ============================================================================
# ANNOUNCEMENT STATISTICS
# ============================================================================

def get_announcement_statistics(announcement: Announcements) -> dict:
    """
    Get statistics about an announcement.
    
    Args:
        announcement: Announcement object
    
    Returns:
        Dictionary with statistics
    """
    total_recipients = AnnouncementRecipients.objects.filter(
        announcement=announcement
    ).count()
    
    read_recipients = AnnouncementRecipients.objects.filter(
        announcement=announcement,
        is_read=True
    ).count()
    
    unread_recipients = total_recipients - read_recipients
    
    return {
        'total_recipients': total_recipients,
        'read_count': read_recipients,
        'unread_count': unread_recipients,
        'read_percentage': (read_recipients / total_recipients * 100) if total_recipients > 0 else 0,
    }


# ============================================================================
# BULK QUERIES
# ============================================================================

def get_all_user_notifications_and_announcements(user: User) -> dict:
    """
    Get both notifications and announcements for a user in one query.
    
    Args:
        user: User object
    
    Returns:
        Dictionary with notifications and announcements
    """
    return {
        'notifications': get_user_notifications(user),
        'announcements': get_announcements_for_user(user),
        'unread_count': get_user_unread_count(user),
    }
