"""
Celery Tasks for Notification Module
=====================================

This module contains Celery Beat tasks for background job execution.

Tasks:
    - expire_announcements: Auto-deactivate expired announcements (T-NT-02)
"""

from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from .models import Announcements
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def expire_announcements(self):
    """
    Celery task to automatically deactivate expired announcements (T-NT-02).
    
    This task should run periodically (daily recommended) to mark announcements
    as inactive when they reach their expiry_date.
    
    Task ID: T-NT-02
    Business Rule: BR-NT-06
    
    Returns:
        dict: Summary of expired announcements
    """
    try:
        # Get current time
        now = timezone.now()
        
        # Find all published announcements that have passed their expiry_date
        expired_announcements = Announcements.objects.filter(
            is_published=True,
            is_active=True,
            expiry_date__isnull=False,
            expiry_date__lt=now  # expiry_date is in the past
        )
        
        # Count before deactivation
        count = expired_announcements.count()
        
        # Deactivate all expired announcements
        expired_announcements.update(is_active=False)
        
        # Log the action
        logger.info(f"Expired {count} announcements as of {now}")
        
        # Return summary
        summary = {
            'status': 'success',
            'expired_count': count,
            'timestamp': str(now),
            'message': f"Successfully deactivated {count} expired announcements."
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error in expire_announcements task: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'message': 'Failed to process expired announcements.'
        }


@shared_task(bind=True)
def notify_about_expiring_announcements(self, days_before=1):
    """
    Celery task to notify announcement creators about upcoming expirations (T-NT-02).
    
    This task can be scheduled to run daily and notifies creators when their
    announcements are about to expire.
    
    Args:
        days_before: Number of days before expiry to send notification (default: 1)
    
    Returns:
        dict: Summary of notifications sent
    """
    try:
        from datetime import timedelta
        
        # Calculate the target date range
        future_date = timezone.now() + timedelta(days=days_before)
        start_of_day = future_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = future_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Find announcements expiring in the next N days
        expiring_soon = Announcements.objects.filter(
            is_published=True,
            is_active=True,
            expiry_date__gte=start_of_day,
            expiry_date__lte=end_of_day
        )
        
        count = 0
        for announcement in expiring_soon:
            try:
                if announcement.created_by and announcement.created_by.email:
                    send_mail(
                        subject=f'Announcement Expiring Soon: {announcement.message[:50]}',
                        message=f'Your announcement "{announcement.message[:50]}..." will expire on {announcement.expiry_date}.',
                        from_email='notification@iiitdmj.ac.in',
                        recipient_list=[announcement.created_by.email],
                        fail_silently=True,
                    )
                    count += 1
            except Exception as e:
                logger.warning(f"Failed to notify creator for announcement {announcement.id}: {str(e)}")
                continue
        
        logger.info(f"Sent {count} expiration notifications.")
        
        return {
            'status': 'success',
            'notifications_sent': count,
            'timestamp': str(timezone.now()),
            'message': f"Successfully notified {count} users about upcoming expiration."
        }
        
    except Exception as e:
        logger.error(f"Error in notify_about_expiring_announcements task: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'message': 'Failed to process expiration notifications.'
        }


@shared_task(bind=True)
def cleanup_old_notifications(self, days_old=30):
    """
    Celery task to archive/cleanup old notifications (Optional enhancement to BR-NT-09).
    
    Keeps notifications for at least N days before allowing deletion.
    This prevents storage bloat over time.
    
    Args:
        days_old: Number of days old to consider for cleanup (default: 30)
    
    Returns:
        dict: Summary of cleanup
    """
    try:
        from datetime import timedelta
        from notifications.models import Notification
        
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        # Count old notifications before deletion (optional: archive first)
        old_notifications = Notification.objects.filter(
            timestamp__lt=cutoff_date,
            deleted=False
        )
        
        count = old_notifications.count()
        
        # Option 1: Just mark as deleted instead of hard-deleting (safer)
        # old_notifications.update(deleted=True)
        
        # Option 2: Actually delete (use with caution)
        # old_notifications.delete()
        
        logger.info(f"Identified {count} notifications older than {days_old} days for cleanup.")
        
        return {
            'status': 'success',
            'old_notifications_count': count,
            'days_threshold': days_old,
            'timestamp': str(timezone.now()),
            'message': f"Identified {count} notifications older than {days_old} days."
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_notifications task: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'message': 'Failed to cleanup old notifications.'
        }
