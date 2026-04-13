"""
Analytics and Feedback models for T22 (Analytics Dashboard) and T23 (User Feedback).
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import json


class Analytics(models.Model):
    """T22: Aggregated metrics for No Dues clearance process."""
    
    METRIC_CHOICES = [
        ('total_records', 'Total No Dues Records'),
        ('cleared_count', 'Total Cleared'),
        ('notclear_count', 'Total Not Clear'),
        ('pending_count', 'Pending Clearance'),
        ('avg_clearance_time', 'Average Days to Clear'),
        ('escalation_rate', 'Escalation Rate (%)'),
        ('department_clear_rate', 'Department Clear Rate (%)'),
        ('7day_reminders_sent', '7-Day Reminders Sent'),
        ('14day_reminders_sent', '14-Day Reminders Sent'),
        ('21day_reminders_sent', '21-Day Reminders Sent'),
        ('auto_marked_30day', 'Auto-Marked After 30 Days'),
    ]
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    metric_type = models.CharField(max_length=50, choices=METRIC_CHOICES, db_index=True)
    department = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    value = models.JSONField(default=dict)  # Can store int, float, dict, etc.
    
    # Metadata
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    aggregation_type = models.CharField(
        max_length=20,
        choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')],
        default='daily'
    )
    
    class Meta:
        db_table = 'otheracademic_analytics'
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['metric_type', 'timestamp']),
            models.Index(fields=['department', 'timestamp']),
        ]
        verbose_name_plural = 'Analytics'
    
    def __str__(self):
        return f"{self.metric_type} ({self.aggregation_type}) - {self.timestamp}"
    
    @staticmethod
    def log_metric(metric_type, value, department=None, period_start=None, period_end=None, aggregation_type='daily'):
        """Create a new metric entry."""
        return Analytics.objects.create(
            metric_type=metric_type,
            value={'value': value} if not isinstance(value, dict) else value,
            department=department,
            period_start=period_start,
            period_end=period_end,
            aggregation_type=aggregation_type,
        )
    
    @staticmethod
    def get_metric(metric_type, department=None, days=30):
        """Get metric data for time range."""
        cutoff = timezone.now() - timedelta(days=days)
        qs = Analytics.objects.filter(
            metric_type=metric_type,
            timestamp__gte=cutoff,
        )
        if department:
            qs = qs.filter(department=department)
        return qs.order_by('-timestamp')
    
    @staticmethod
    def get_dashboard_summary():
        """Get all key metrics for dashboard."""
        today = timezone.now().date()
        one_month_ago = today - timedelta(days=30)
        
        return {
            'today': Analytics.objects.filter(
                period_start=today,
                aggregation_type='daily'
            ).values('metric_type', 'value'),
            'this_month': Analytics.objects.filter(
                period_start__gte=one_month_ago,
                aggregation_type='daily'
            ).values('metric_type').annotate(
                avg_value=models.Avg(models.F('value__value'))
            ),
        }


class Feedback(models.Model):
    """T23: User feedback on No Dues clearance process."""
    
    RATING_CHOICES = [
        (1, 'Very Poor'),
        (2, 'Poor'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Excellent'),
    ]
    
    CATEGORY_CHOICES = [
        ('process_clarity', 'Process Clarity'),
        ('ease_of_use', 'Ease of Use'),
        ('timeline', 'Timeline'),
        ('communication', 'Communication'),
        ('support', 'Support Quality'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks', db_index=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, db_index=True)
    rating = models.IntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=200)
    comment = models.TextField(max_length=5000)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_anonymous = models.BooleanField(default=False)
    helpful_count = models.IntegerField(default=0)
    
    # Admin response
    admin_response = models.TextField(null=True, blank=True)
    responded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedback_responses'
    )
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'otheracademic_feedback'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['category', 'rating']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        author = 'Anonymous' if self.is_anonymous else self.user.username
        return f"{self.title} ({author}, {self.rating}/5)"
    
    @staticmethod
    def get_aggregated_ratings():
        """Get summary statistics for all feedback."""
        from django.db.models import Avg, Count
        
        return {
            'average_rating': Feedback.objects.aggregate(avg=Avg('rating'))['avg'] or 0,
            'total_feedback': Feedback.objects.count(),
            'by_category': Feedback.objects.values('category').annotate(
                avg_rating=Avg('rating'),
                count=Count('id')
            ),
            'by_rating': Feedback.objects.values('rating').annotate(
                count=Count('id')
            ).order_by('rating'),
        }
    
    @staticmethod
    def get_recent_feedback(limit=10):
        """Get recent feedback sorted by rating (lowest first)."""
        return Feedback.objects.filter(
            admin_response__isnull=False
        ).order_by('rating', '-created_at')[:limit]


class FeedbackHelpfulness(models.Model):
    """T23: Track if feedback was marked as helpful."""
    
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name='helpfulness_votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_helpful = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'otheracademic_feedback_helpfulness'
        unique_together = ('feedback', 'user')
        indexes = [
            models.Index(fields=['feedback', 'user']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.feedback.id} - {'Helpful' if self.is_helpful else 'Not helpful'}"


class SystemHealthCheck(models.Model):
    """T24: Store results of system health checks."""
    
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    check_type = models.CharField(max_length=100, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    message = models.TextField()
    details = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'otheracademic_health_check'
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['check_type', 'status']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.check_type} - {self.status}"
    
    @staticmethod
    def log_check(check_type, status, message, details=None):
        """Log a health check result."""
        return SystemHealthCheck.objects.create(
            check_type=check_type,
            status=status,
            message=message,
            details=details or {},
        )


class APICallLog(models.Model):
    """T24: Track API calls for monitoring and verification."""
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    endpoint = models.CharField(max_length=200, db_index=True)
    method = models.CharField(max_length=10)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status_code = models.IntegerField(db_index=True)
    response_time_ms = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    ip_address = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        db_table = 'otheracademic_api_call_log'
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['endpoint', 'method']),
            models.Index(fields=['user', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.status_code}"
    
    @staticmethod
    def get_endpoint_stats(endpoint=None, days=7):
        """Get statistics for API endpoint calls."""
        from django.db.models import Count, Avg
        
        cutoff = timezone.now() - timedelta(days=days)
        qs = APICallLog.objects.filter(timestamp__gte=cutoff)
        
        if endpoint:
            qs = qs.filter(endpoint=endpoint)
        
        return qs.values('endpoint', 'method').annotate(
            call_count=Count('id'),
            avg_response_time=Avg('response_time_ms'),
            error_count=Count('id', filter=models.Q(status_code__gte=400)),
        )
