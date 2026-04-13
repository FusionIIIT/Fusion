"""
T22/T23: Celery tasks for analytics aggregation and feedback processing.
"""
from celery import shared_task
from django.utils import timezone
from applications.otheracademic.analytics_service import AnalyticsService
from applications.otheracademic.analytics_models import Feedback, SystemHealthCheck
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def aggregate_daily_analytics(self):
    """
    Generate and aggregate daily analytics metrics.
    Runs once daily (typically at 10 AM).
    """
    try:
        logger.info("=== Starting daily analytics aggregation ===")
        start_time = timezone.now()
        
        results = AnalyticsService.generate_daily_analytics()
        
        elapsed = (timezone.now() - start_time).total_seconds()
        
        logger.info(f"Daily analytics completed in {elapsed:.2f}s")
        logger.info(f"Results: {results}")
        
        SystemHealthCheck.log_check(
            'daily_analytics',
            'success',
            f'Daily analytics generated in {elapsed:.2f}s',
            {'results': results, 'elapsed_seconds': elapsed}
        )
        
        return {
            'status': 'success',
            'elapsed_seconds': elapsed,
            'results': results,
        }
    
    except Exception as exc:
        logger.error(f"Error in daily analytics aggregation: {str(exc)}", exc_info=True)
        
        SystemHealthCheck.log_check(
            'daily_analytics',
            'error',
            f'Daily analytics failed: {str(exc)}',
            {'error': str(exc)}
        )
        
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task
def generate_weekly_analytics_summary():
    """
    Generate weekly summary of all analytics.
    Runs once weekly (typically Monday 11 AM).
    """
    try:
        logger.info("=== Generating weekly analytics summary ===")
        
        summary = AnalyticsService.get_dashboard_summary()
        
        logger.info(f"Weekly summary generated: {len(summary)} sections")
        
        SystemHealthCheck.log_check(
            'weekly_analytics_summary',
            'success',
            'Weekly analytics summary generated',
            summary
        )
        
        return {
            'status': 'success',
            'summary': summary,
            'timestamp': timezone.now().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Error generating weekly analytics: {str(e)}", exc_info=True)
        return {'error': str(e)}


@shared_task
def send_unanswered_feedback_reminder():
    """
    Send reminder to admins about unanswered feedback.
    Runs daily (typically at 2 PM).
    """
    try:
        logger.info("=== Checking for unanswered feedback ===")
        
        unanswered = Feedback.objects.filter(admin_response__isnull=True).count()
        
        if unanswered > 0:
            # Could send email notification here
            logger.info(f"Found {unanswered} unanswered feedback entries")
            
            SystemHealthCheck.log_check(
                'unanswered_feedback_check',
                'warning' if unanswered > 5 else 'success',
                f'{unanswered} feedback entries need response',
                {'count': unanswered}
            )
            
            return {
                'status': 'success',
                'unanswered_count': unanswered,
            }
        else:
            logger.info("All feedback has been answered")
            return {'status': 'success', 'unanswered_count': 0}
    
    except Exception as e:
        logger.error(f"Error checking feedback: {str(e)}", exc_info=True)
        return {'error': str(e)}


@shared_task
def cleanup_old_analytics():
    """
    Clean up old analytics records (keep last 365 days).
    Runs weekly (typically Sunday 3 AM).
    """
    try:
        logger.info("=== Cleaning up old analytics records ===")
        
        from datetime import timedelta
        from applications.otheracademic.analytics_models import Analytics, APICallLog
        
        cutoff_date = timezone.now() - timedelta(days=365)
        
        # Delete old analytics
        old_analytics_count, _ = Analytics.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()
        
        # Delete old API logs
        old_logs_count, _ = APICallLog.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()
        
        logger.info(f"Deleted {old_analytics_count} old analytics, {old_logs_count} old API logs")
        
        return {
            'status': 'success',
            'deleted_analytics': old_analytics_count,
            'deleted_logs': old_logs_count,
        }
    
    except Exception as e:
        logger.error(f"Error cleaning analytics: {str(e)}", exc_info=True)
        return {'error': str(e)}


@shared_task
def run_system_health_check():
    """
    Run comprehensive system health check.
    Runs daily (typically at 6 AM).
    """
    try:
        logger.info("=== Running system health check ===")
        
        from applications.otheracademic.verification_service import VerificationService
        
        results = VerificationService.run_full_verification()
        
        logger.info(f"Health check completed: {results.get('summary')}")
        
        return results
    
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}", exc_info=True)
        return {'error': str(e)}


# Beat schedule configuration to add to celery.py:
"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Existing escalation tasks...
    
    # T22: Analytics tasks
    'aggregate-daily-analytics': {
        'task': 'applications.otheracademic.analytics_tasks.aggregate_daily_analytics',
        'schedule': crontab(hour=10, minute=0),
        'options': {'queue': 'default'}
    },
    
    'generate-weekly-analytics': {
        'task': 'applications.otheracademic.analytics_tasks.generate_weekly_analytics_summary',
        'schedule': crontab(day_of_week=1, hour=11, minute=0),  # Monday 11 AM
        'options': {'queue': 'default'}
    },
    
    # T23: Feedback tasks
    'feedback-reminder': {
        'task': 'applications.otheracademic.analytics_tasks.send_unanswered_feedback_reminder',
        'schedule': crontab(hour=14, minute=0),
        'options': {'queue': 'default'}
    },
    
    # Cleanup
    'cleanup-analytics': {
        'task': 'applications.otheracademic.analytics_tasks.cleanup_old_analytics',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),  # Sunday 3 AM
        'options': {'queue': 'default'}
    },
    
    # T24: Health checks
    'system-health-check': {
        'task': 'applications.otheracademic.analytics_tasks.run_system_health_check',
        'schedule': crontab(hour=6, minute=0),
        'options': {'queue': 'default'}
    },
}
"""
