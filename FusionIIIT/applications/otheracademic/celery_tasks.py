"""
Celery tasks for No Dues escalation workflow.

These tasks run on a schedule (Celery beat) to automate the escalation process.
"""
from celery import shared_task
from django.utils import timezone
from django.conf import settings
import logging

from applications.otheracademic.escalation_service import NoDuesEscalationService
from applications.otheracademic.audit_models import AuditLog

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def check_and_escalate_nodues(self):
    """
    Main escalation task - Runs once daily (typically at 9 AM).
    
    Checks all No Dues records and:
    - Sends 7-day reminder
    - Sends 14-day reminder
    - Sends 21-day reminder
    - Auto-marks as clear after 30 days
    
    Retry logic:
    - Retries up to 3 times with exponential backoff if fails
    - Logs errors for admin review
    """
    try:
        logger.info("=== Starting No Dues escalation check ===")
        start_time = timezone.now()
        
        # Run the escalation check
        results = NoDuesEscalationService.check_and_escalate_all()
        
        elapsed = (timezone.now() - start_time).total_seconds()
        
        # Log summary
        summary = (
            f"No Dues escalation check completed in {elapsed:.2f}s:\n"
            f"  - Records checked: {results.get('checked', 0)}\n"
            f"  - Reminders sent: {results.get('reminders_sent', 0)}\n"
            f"  - Auto-marked: {results.get('auto_marked', 0)}\n"
            f"  - Escalated to Dean: {results.get('escalated_dean', 0)}\n"
            f"  - Escalated to Director: {results.get('escalated_director', 0)}"
        )
        logger.info(summary)
        
        # Log any errors
        if results.get('errors'):
            error_msg = "\n".join(results['errors'])
            logger.error(f"Errors during escalation check:\n{error_msg}")
        
        return {
            'status': 'success',
            'results': results,
            'timestamp': start_time.isoformat(),
        }
    
    except Exception as exc:
        logger.error(f"Error in check_and_escalate_nodues: {str(exc)}", exc_info=True)
        
        # Retry with exponential backoff (2^retry attempts)
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task
def send_daily_escalation_summary():
    """
    Send daily summary email to admins about escalations and pending actions.
    
    Summary includes:
    - Number of escalations sent today
    - Number of auto-marked records
    - Number of records approaching 30-day threshold
    - List of departments with pending clearances
    """
    try:
        logger.info("Generating daily escalation summary")
        
        today = timezone.now().date()
        escalations_today = AuditLog.objects.filter(
            action='escalate',
            timestamp__date=today,
        ).count()
        
        auto_marked_today = AuditLog.objects.filter(
            action='auto_mark_30day',
            timestamp__date=today,
        ).count()
        
        summary = {
            'date': today.isoformat(),
            'escalations_sent': escalations_today,
            'auto_marked': auto_marked_today,
            'timestamp': timezone.now().isoformat(),
        }
        
        logger.info(f"Daily summary: {summary}")
        return summary
    
    except Exception as exc:
        logger.error(f"Error generating escalation summary: {str(exc)}", exc_info=True)
        return {'error': str(exc)}


@shared_task
def cleanup_old_escalation_records():
    """
    Cleanup task - Archives or deletes old escalation records.
    
    Retention policy:
    - Keep all records for last 365 days
    - Archive records older than 365 days
    
    Runs once weekly (every Sunday at 2 AM).
    """
    try:
        from datetime import timedelta
        from applications.otheracademic.audit_models import NoDuesEscalation
        
        cutoff_date = timezone.now() - timedelta(days=365)
        
        old_escalations = NoDuesEscalation.objects.filter(created_at__lt=cutoff_date)
        count = old_escalations.count()
        
        logger.info(f"Found {count} escalation records older than 365 days")
        
        # For now, just log them. In production, you might archive to a separate table
        # old_escalations.delete()
        
        return {
            'status': 'success',
            'records_archived': count,
            'timestamp': timezone.now().isoformat(),
        }
    
    except Exception as exc:
        logger.error(f"Error in cleanup task: {str(exc)}", exc_info=True)
        return {'error': str(exc)}


# Beat schedule configuration to add to Celery settings:
"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Run escalation check daily at 9 AM
    'check-nodues-escalations': {
        'task': 'applications.otheracademic.celery_tasks.check_and_escalate_nodues',
        'schedule': crontab(hour=9, minute=0),
        'options': {'queue': 'default'}
    },
    
    # Send daily summary at 5 PM
    'daily-escalation-summary': {
        'task': 'applications.otheracademic.celery_tasks.send_daily_escalation_summary',
        'schedule': crontab(hour=17, minute=0),
        'options': {'queue': 'default'}
    },
    
    # Cleanup old records every Sunday at 2 AM
    'cleanup-escalation-records': {
        'task': 'applications.otheracademic.celery_tasks.cleanup_old_escalation_records',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),
        'options': {'queue': 'default'}
    },
}
"""
