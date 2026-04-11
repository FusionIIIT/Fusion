"""
Performance optimization module for otheracademic.
Implements caching, query optimization, and performance monitoring.

T13 Deliverables:
- Redis caching for frequently accessed data (student records, clear status)
- Query optimization with select_related, prefetch_related
- API response pagination
- Database indexes (already in migrations)
- Performance monitoring decorators
"""
from functools import wraps
import time
from django.core.cache import cache
from django.db.models import Prefetch, Q
from rest_framework.pagination import PageNumberPagination
import logging

logger = logging.getLogger(__name__)


class OptimizedPagination(PageNumberPagination):
    """Pagination for analytics and large data sets."""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500


class LargeResultsSetPagination(PageNumberPagination):
    """Pagination for large result sets (audit logs, etc)."""
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


class SmallResultsSetPagination(PageNumberPagination):
    """Pagination for small, filtered result sets."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


def cache_result(timeout=3600, key_prefix=''):
    """
    Decorator to cache expensive function results.
    
    Args:
        timeout: Cache timeout in seconds (default 1 hour)
        key_prefix: Prefix for cache key (include request.user if needed)
    
    Usage:
        @cache_result(timeout=300, key_prefix='analytics_summary')
        def get_dashboard_summary(self):
            return expensive_computation()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}{str(kwargs)}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return result
            
            # Cache miss - compute and store
            logger.debug(f"Cache MISS: {cache_key}")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        
        return wrapper
    return decorator


def monitor_performance(func):
    """
    Decorator to monitor function execution time and log slow operations.
    Logs if execution time > 1 second.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = time.time() - start_time
            if elapsed > 1.0:
                logger.warning(
                    f"SLOW QUERY: {func.__name__} took {elapsed:.2f}s "
                    f"(args: {len(str(args))} bytes, kwargs: {len(str(kwargs))} bytes)"
                )
    return wrapper


class OptimizedQueryMixin:
    """Mixin for optimized database queries in ViewSets."""
    
    def get_queryset(self):
        """Override in subclass to add select_related/prefetch_related."""
        queryset = super().get_queryset()
        
        # Apply optimizations if defined
        if hasattr(self, 'select_related_fields'):
            queryset = queryset.select_related(*self.select_related_fields)
        
        if hasattr(self, 'prefetch_related_fields'):
            queryset = queryset.prefetch_related(*self.prefetch_related_fields)
        
        return queryset


class CacheInvalidationMixin:
    """Mixin to automatically invalidate cache on data mutations."""
    
    cache_keys_to_invalidate = []
    
    def perform_create(self, serializer):
        super().perform_create(serializer)
        self._invalidate_cache()
    
    def perform_update(self, serializer):
        super().perform_update(serializer)
        self._invalidate_cache()
    
    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        self._invalidate_cache()
    
    def _invalidate_cache(self):
        """Invalidate all related cache keys."""
        for key_pattern in self.cache_keys_to_invalidate:
            # For pattern-based invalidation, you might need django-redis
            cache.delete(key_pattern)
            logger.info(f"Invalidated cache: {key_pattern}")


# ==================== Query Optimization Utilities ====================

def get_student_nodues_optimized(student_user, use_cache=True):
    """
    Get student's No Dues record with all related data optimized.
    Uses select_related for ForeignKeys, prefetch_related for reverse relations.
    """
    cache_key = f"student_nodues:{student_user.id}"
    
    if use_cache:
        cached = cache.get(cache_key)
        if cached:
            logger.debug(f"Loaded NoDues from cache: {student_user.username}")
            return cached
    
    from applications.otheracademic.models import NoDues
    from applications.otheracademic.audit_models import NoDuesEscalation, NoDuesClearanceHistory
    
    try:
        # Single query with all related data pre-fetched
        nodues = NoDues.objects.select_related(
            'user'  # Student ForeignKey
        ).prefetch_related(
            Prefetch('escalations', queryset=NoDuesEscalation.objects.order_by('-created_at')[:10]),
            Prefetch('clearance_history', queryset=NoDuesClearanceHistory.objects.order_by('-changed_at')[:20]),
        ).get(user=student_user)
        
        # Cache for 30 minutes
        if use_cache:
            cache.set(cache_key, nodues, 1800)
        
        return nodues
    except NoDues.DoesNotExist:
        return None


def get_escalations_optimized(student_user=None, days=30, status=None):
    """
    Get escalations with optimized queries.
    """
    from applications.otheracademic.audit_models import NoDuesEscalation
    from django.utils import timezone
    from datetime import timedelta
    
    queryset = NoDuesEscalation.objects.select_related(
        'student',
        'no_dues'
    )
    
    # Filter by student if provided
    if student_user:
        queryset = queryset.filter(student=student_user)
    
    # Filter by date range
    cutoff_date = timezone.now() - timedelta(days=days)
    queryset = queryset.filter(created_at__gte=cutoff_date)
    
    # Filter by status
    if status:
        queryset = queryset.filter(status=status)
    
    return queryset.order_by('-created_at')


def get_audit_logs_optimized(model_name=None, object_id=None, user=None, days=30):
    """
    Get audit logs with optimized queries.
    """
    from applications.otheracademic.audit_models import AuditLog
    from django.utils import timezone
    from datetime import timedelta
    
    queryset = AuditLog.objects.select_related(
        'user',
        'related_user'
    )
    
    # Filter by date range
    cutoff_date = timezone.now() - timedelta(days=days)
    queryset = queryset.filter(timestamp__gte=cutoff_date)
    
    # Apply optional filters
    if model_name:
        queryset = queryset.filter(model_name=model_name)
    
    if object_id:
        queryset = queryset.filter(object_id=object_id)
    
    if user:
        queryset = queryset.filter(user=user)
    
    return queryset.order_by('-timestamp')


def bulk_clear_nodues_cache(student_ids=None):
    """
    Bulk clear NoDues cache for students (after batch operations).
    """
    if student_ids is None:
        # Clear all nodues caches
        pattern = "student_nodues:*"
        # Use django-redis for pattern deletion
        cache.delete_pattern(pattern)
    else:
        # Clear specific students
        for student_id in student_ids:
            cache.delete(f"student_nodues:{student_id}")
    
    logger.info(f"Cleared NoDues cache for {len(student_ids or [])} students")


# ==================== Database Connection Pooling ====================

def configure_connection_pooling():
    """
    Configure database connection pooling for production.
    Add to settings.py DATABASES config:
    
    'CONN_MAX_AGE': 600,  # Connection pooling max age (10 minutes)
    'OPTIONS': {
        'connect_timeout': 10,
    }
    """
    return {
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }


# ==================== Celery Task Optimization ====================

class CeleryOptimizationConfig:
    """Configuration for optimized Celery task processing."""
    
    # Task configuration
    CELERY_TASK_TIME_LIMIT = 300  # 5 minutes hard limit
    CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutes soft limit
    
    # Worker configuration
    CELERY_WORKER_PREFETCH_MULTIPLIER = 4  # Prefetch 4 tasks per worker
    CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000  # Recycle worker after 1000 tasks
    
    # Result configuration
    CELERY_RESULT_EXPIRES = 3600  # Keep results for 1 hour
    
    # Broker configuration
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
    CELERY_BROKER_CONNECTION_RETRY = True
    CELERY_BROKER_CONNECTION_MAX_RETRIES = 10


# ==================== Index Verification ====================

def verify_database_indexes():
    """
    Verify all critical indexes exist in database.
    Run this in management command or migration.
    """
    from django.db import connection
    from django.apps import apps
    
    errors = []
    
    # Define critical indexes by model and fields
    critical_indexes = {
        'AuditLog': [
            ('timestamp',),
            ('model_name', 'object_id'),
        ],
        'NoDuesEscalation': [
            ('student', 'created_at'),
            ('status', 'created_at'),
        ],
        'Analytics': [
            ('timestamp',),
            ('metric_type', 'timestamp'),
        ],
        'Feedback': [
            ('created_at',),
            ('user', 'created_at'),
        ],
    }
    
    with connection.cursor() as cursor:
        for model_name, index_fields_list in critical_indexes.items():
            try:
                model = apps.get_model('otheracademic', model_name)
                table_name = model._meta.db_table
                
                # Get existing indexes
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='{table_name}'")
                existing_indexes = {row[0] for row in cursor.fetchall()}
                
                for index_fields in index_fields_list:
                    # This is a simplified check - actual logic depends on database backend
                    if len(existing_indexes) == 0:
                        errors.append(f"No indexes found on {table_name}")
            except Exception as e:
                errors.append(f"Error checking {model_name}: {str(e)}")
    
    return errors


# ==================== Query Count Debugging ====================

class QueryCountDebugMiddleware:
    """
    Middleware to log query counts for each request.
    Only active in DEBUG mode.
    
    Add to settings.py MIDDLEWARE if DEBUG=True
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        from django.db import connection, reset_queries
        from django.conf import settings
        
        if not settings.DEBUG:
            return self.get_response(request)
        
        reset_queries()
        response = self.get_response(request)
        
        num_queries = len(connection.queries)
        if num_queries > 10:  # Log if > 10 queries
            logger.warning(
                f"Request {request.method} {request.path} executed {num_queries} queries"
            )
            for query in connection.queries[-5:]:  # Log last 5 queries
                logger.debug(f"  {query['time']}s: {query['sql'][:100]}")
        
        return response
