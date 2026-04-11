"""
T22: Analytics service for No Dues clearance metrics and reporting.
"""
from django.utils import timezone
from django.db.models import Count, Q, Avg, F
from datetime import timedelta, datetime
from applications.otheracademic.models import NoDues
from applications.academic_information.models import Student
from applications.otheracademic.audit_models import NoDuesEscalation, NoDuesClearanceHistory
from applications.otheracademic.analytics_models import Analytics


class AnalyticsService:
    """Service for generating and aggregating analytics data."""
    
    DEPARTMENTS = [
        'library', 'hostel', 'mess', 'ece', 'physics_lab', 'mechatronics_lab',
        'cc', 'workshop', 'signal_processing_lab', 'vlsi', 'design_studio',
        'design_project', 'bank', 'icard_dsa', 'account', 'btp_supervisor',
        'discipline_office', 'student_gymkhana', 'alumni', 'placement_cell',
    ]
    
    @staticmethod
    def generate_daily_analytics():
        """Generate daily analytics snapshot."""
        results = {}
        
        # Total No Dues records
        total_records = NoDues.objects.count()
        results['total_records'] = total_records
        Analytics.log_metric('total_records', total_records, aggregation_type='daily')
        
        # Count by status
        cleared_count = 0
        notclear_count = 0
        pending_count = total_records
        
        for dept_prefix in AnalyticsService.DEPARTMENTS:
            clear_field = f"{dept_prefix}_clear"
            notclear_field = f"{dept_prefix}_notclear"
            
            cleared = NoDues.objects.filter(**{f"{clear_field}": True}).count()
            notclear = NoDues.objects.filter(**{f"{notclear_field}": True}).count()
            pending = NoDues.objects.filter(
                **{f"{clear_field}": False, f"{notclear_field}": False}
            ).count()
            
            cleared_count += cleared
            notclear_count += notclear
            pending_count = min(pending_count, pending)
        
        cleared_count = cleared_count // len(AnalyticsService.DEPARTMENTS)
        notclear_count = notclear_count // len(AnalyticsService.DEPARTMENTS)
        pending_count = total_records - cleared_count - notclear_count
        
        Analytics.log_metric('cleared_count', cleared_count, aggregation_type='daily')
        Analytics.log_metric('notclear_count', notclear_count, aggregation_type='daily')
        Analytics.log_metric('pending_count', pending_count, aggregation_type='daily')
        
        results['cleared_count'] = cleared_count
        results['notclear_count'] = notclear_count
        results['pending_count'] = pending_count
        
        # Average clearance time
        history = NoDuesClearanceHistory.objects.filter(new_status='clear')
        if history.exists():
            avg_time = (history.aggregate(
                avg_time=Avg(F('changed_at') - F('no_dues__created_at'))
            )['avg_time'] or timedelta(0)).total_seconds() / 86400  # Convert to days
            
            Analytics.log_metric('avg_clearance_time', avg_time, aggregation_type='daily')
            results['avg_clearance_time'] = round(avg_time, 2)
        
        # Escalation rate
        total_escalations = NoDuesEscalation.objects.count()
        escalation_rate = (total_escalations / total_records * 100) if total_records > 0 else 0
        Analytics.log_metric('escalation_rate', escalation_rate, aggregation_type='daily')
        results['escalation_rate'] = round(escalation_rate, 2)
        
        # Escalation type counts
        for escalation_type in ['reminder_7day', 'reminder_14day', 'reminder_21day', 'auto_mark_30day']:
            count = NoDuesEscalation.objects.filter(
                escalation_type=escalation_type,
                status='sent'
            ).count()
            
            metric_key = f"{escalation_type}_sent"
            Analytics.log_metric(metric_key, count, aggregation_type='daily')
            results[metric_key] = count
        
        return results
    
    @staticmethod
    def get_department_analytics(department):
        """Get analytics for specific department."""
        clear_field = f"{department}_clear"
        notclear_field = f"{department}_notclear"
        
        total = NoDues.objects.count()
        cleared = NoDues.objects.filter(**{clear_field: True}).count()
        notclear = NoDues.objects.filter(**{notclear_field: True}).count()
        pending = total - cleared - notclear
        
        clear_rate = (cleared / total * 100) if total > 0 else 0
        
        return {
            'department': department,
            'total': total,
            'cleared': cleared,
            'notclear': notclear,
            'pending': pending,
            'clear_rate': round(clear_rate, 2),
            'completion_rate': round(((cleared + notclear) / total * 100) if total > 0 else 0, 2),
        }
    
    @staticmethod
    def get_all_departments_analytics():
        """Get analytics for all departments."""
        return [
            AnalyticsService.get_department_analytics(dept)
            for dept in AnalyticsService.DEPARTMENTS
        ]
    
    @staticmethod
    def get_escalation_analytics(days=30):
        """Get escalation statistics for time period."""
        cutoff = timezone.now() - timedelta(days=days)
        
        escalations = NoDuesEscalation.objects.filter(created_at__gte=cutoff)
        
        return {
            'period_days': days,
            'total_escalations': escalations.count(),
            'by_type': escalations.values('escalation_type').annotate(count=Count('id')),
            'by_status': escalations.values('status').annotate(count=Count('id')),
            'by_department': escalations.values('department').annotate(count=Count('id')),
            'escalations_resolved': escalations.filter(status='completed').count(),
            'escalations_pending': escalations.filter(status='pending').count(),
        }
    
    @staticmethod
    def get_clearance_timeline(days=30):
        """Get timeline of clearances over time period."""
        cutoff = timezone.now() - timedelta(days=days)
        
        timeline = []
        for i in range(days):
            date = (timezone.now() - timedelta(days=i)).date()
            count = NoDuesClearanceHistory.objects.filter(
                changed_at__date=date,
                new_status='clear'
            ).count()
            
            timeline.append({
                'date': date.isoformat(),
                'cleared_count': count,
            })
        
        return sorted(timeline, key=lambda x: x['date'])
    
    @staticmethod
    def get_turnaround_time_analytics():
        """Get turnaround time statistics."""
        from django.db.models import DurationField, ExpressionWrapper
        
        history = NoDuesClearanceHistory.objects.filter(
            new_status='clear',
            changed_at__isnull=False,
        )
        
        if not history.exists():
            return {
                'avg_days': 0,
                'min_days': 0,
                'max_days': 0,
                'median_days': 0,
            }
        
        times_in_seconds = history.annotate(
            duration_seconds=ExpressionWrapper(
                F('changed_at') - F('no_dues__created_at'),
                output_field=DurationField()
            )
        ).values_list('duration_seconds', flat=True)
        
        times_in_days = [t.total_seconds() / 86400 for t in times_in_seconds if t]
        
        if not times_in_days:
            return {
                'avg_days': 0,
                'min_days': 0,
                'max_days': 0,
                'median_days': 0,
            }
        
        times_in_days.sort()
        
        return {
            'avg_days': round(sum(times_in_days) / len(times_in_days), 1),
            'min_days': round(min(times_in_days), 1),
            'max_days': round(max(times_in_days), 1),
            'median_days': round(times_in_days[len(times_in_days) // 2], 1),
            'total_samples': len(times_in_days),
        }
    
    @staticmethod
    def get_dashboard_summary():
        """Get comprehensive dashboard summary."""
        return {
            'summary': {
                'total_records': NoDues.objects.count(),
                'total_students': StudentDB.objects.count(),
                'total_escalations': NoDuesEscalation.objects.count(),
                'pending_escalations': NoDuesEscalation.objects.filter(status='pending').count(),
            },
            'departments': AnalyticsService.get_all_departments_analytics(),
            'escalations': AnalyticsService.get_escalation_analytics(days=30),
            'turnaround_time': AnalyticsService.get_turnaround_time_analytics(),
            'timeline': AnalyticsService.get_clearance_timeline(days=30),
        }
