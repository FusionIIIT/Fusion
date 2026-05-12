"""
Performance Optimization Tools for Visitor Hostel Module
Provides caching, query optimization, and performance monitoring
"""

import time
import logging
from functools import wraps
from django.core.cache import cache
from django.conf import settings
from django.db import connection
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.http import JsonResponse
import hashlib

# Performance logger
perf_logger = logging.getLogger('visitor_hostel.performance')

# ============================================================
# CACHING DECORATORS
# ============================================================

def cache_result(timeout=300, key_prefix='vh_cache', vary_on_user=True):
    """
    Cache decorator for functions with automatic cache key generation
    
    Args:
        timeout: Cache timeout in seconds (default 5 minutes)
        key_prefix: Prefix for cache keys
        vary_on_user: Include user ID in cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and parameters
            cache_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            if vary_on_user and hasattr(args[0], 'user'):
                cache_data += f":user:{args[0].user.id}"
            
            cache_key = f"{key_prefix}:{hashlib.md5(cache_data.encode()).hexdigest()}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                perf_logger.debug(f"Cache HIT for {func.__name__}: {cache_key}")
                return result
            
            # Execute function and cache result
            perf_logger.debug(f"Cache MISS for {func.__name__}: {cache_key}")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator

def cache_api_response(timeout=300):
    """
    Cache decorator for API views
    """
    def decorator(func):
        @wraps(func)
        @method_decorator(cache_page(timeout))
        @method_decorator(vary_on_cookie)
        def wrapper(self, request, *args, **kwargs):
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator

# ============================================================
# PERFORMANCE MONITORING
# ============================================================

class QueryCountMiddleware:
    """
    Middleware to monitor database query counts
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only monitor visitor hostel API requests
        if '/visitorhostel/api' not in request.path:
            return self.get_response(request)

        # Reset query count
        initial_queries = len(connection.queries)
        start_time = time.time()
        
        # Process request
        response = self.get_response(request)
        
        # Calculate metrics
        end_time = time.time()
        total_queries = len(connection.queries) - initial_queries
        response_time = end_time - start_time
        
        # Log performance metrics
        perf_logger.info(
            f"API Performance | {request.method} {request.path} | "
            f"Queries: {total_queries} | Response Time: {response_time:.3f}s | "
            f"Status: {response.status_code}"
        )
        
        # Add performance headers in debug mode
        if settings.DEBUG:
            response['X-DB-Queries'] = str(total_queries)
            response['X-Response-Time'] = f"{response_time:.3f}s"
            
        # Warn if performance thresholds exceeded
        if total_queries > 10:
            perf_logger.warning(
                f"High query count detected: {total_queries} queries for {request.path}"
            )
        
        if response_time > 2.0:
            perf_logger.warning(
                f"Slow response detected: {response_time:.3f}s for {request.path}"
            )
            
        return response

def monitor_performance(func_name=None):
    """
    Decorator to monitor function performance
    """
    def decorator(func):
        name = func_name or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            initial_queries = len(connection.queries)
            
            try:
                result = func(*args, **kwargs)
                
                # Calculate metrics
                end_time = time.time()
                execution_time = end_time - start_time
                query_count = len(connection.queries) - initial_queries
                
                # Log performance
                perf_logger.info(
                    f"Function Performance | {name} | "
                    f"Time: {execution_time:.3f}s | Queries: {query_count}"
                )
                
                return result
                
            except Exception as e:
                end_time = time.time()
                execution_time = end_time - start_time
                
                perf_logger.error(
                    f"Function Error | {name} | "
                    f"Time: {execution_time:.3f}s | Error: {str(e)}"
                )
                raise
                
        return wrapper
    return decorator

# ============================================================
# OPTIMIZED QUERY HELPERS
# ============================================================

class OptimizedQueryMixin:
    """
    Mixin to provide optimized query methods for views
    """
    
    def get_optimized_bookings(self, base_queryset):
        """
        Returns bookings with optimized prefetching
        """
        return base_queryset.select_related(
            'intender', 'caretaker'
        ).prefetch_related(
            'rooms', 'visitor'
        )
    
    def get_optimized_bookings_with_meals(self, base_queryset):
        """
        Returns bookings with meals prefetched
        """
        return self.get_optimized_bookings(base_queryset).prefetch_related(
            'mealrecord_set'
        )

def bulk_fetch_meals_for_bookings(booking_ids):
    """
    Efficiently fetch meal records for multiple bookings
    
    Args:
        booking_ids: List of booking IDs
        
    Returns:
        Dict mapping booking_id to list of meal records
    """
    from applications.visitor_hostel.models import MealRecord
    
    meals_dict = {}
    if not booking_ids:
        return meals_dict
        
    meals = MealRecord.objects.filter(
        booking_id__in=booking_ids
    ).select_related('booking', 'visitor')
    
    for meal in meals:
        if meal.booking_id not in meals_dict:
            meals_dict[meal.booking_id] = []
        meals_dict[meal.booking_id].append(meal)
    
    return meals_dict

def bulk_fetch_bills_for_bookings(booking_ids):
    """
    Efficiently fetch bills for multiple bookings
    
    Args:
        booking_ids: List of booking IDs
        
    Returns:
        Dict mapping booking_id to bill object
    """
    from applications.visitor_hostel.models import Bill
    
    bills_dict = {}
    if not booking_ids:
        return bills_dict
        
    bills = Bill.objects.filter(
        booking_id__in=booking_ids
    ).select_related('booking', 'caretaker')
    
    for bill in bills:
        bills_dict[bill.booking_id] = bill
    
    return bills_dict

# ============================================================
# CACHE INVALIDATION
# ============================================================

def invalidate_booking_caches(booking_id):
    """
    Invalidate caches related to a specific booking
    """
    cache_patterns = [
        f'vh_cache:*booking*{booking_id}*',
        'vh_cache:*active_bookings*',
        'vh_cache:*pending_bookings*',
        'vh_cache:*dashboard*'
    ]
    
    # Note: This is a simplified version. In production, use cache.delete_many()
    # or implement proper cache tagging
    for pattern in cache_patterns:
        try:
            cache.delete(pattern)
        except:
            pass

def invalidate_room_availability_caches():
    """
    Invalidate room availability caches
    """
    cache_patterns = [
        'vh_cache:*available_rooms*',
        'vh_cache:*room_availability*'
    ]
    
    for pattern in cache_patterns:
        try:
            cache.delete(pattern)
        except:
            pass

# ============================================================
# PAGINATION HELPERS
# ============================================================

class OptimizedPagination:
    """
    Optimized pagination for large datasets
    """
    
    @staticmethod
    def paginate_queryset(queryset, page_size=20, page=1):
        """
        Efficiently paginate a queryset
        """
        offset = (page - 1) * page_size
        limit = page_size
        
        # Use offset/limit instead of Django's paginator for better performance
        items = list(queryset[offset:offset + limit])
        
        # Get total count efficiently
        if offset == 0:
            # For first page, we can estimate if there are more pages
            has_next = len(items) == page_size
            total_count = None  # Don't calculate unless needed
        else:
            # For other pages, we might need the count
            total_count = queryset.count()
            has_next = offset + len(items) < total_count
        
        return {
            'items': items,
            'page': page,
            'page_size': page_size,
            'has_next': has_next,
            'count': len(items),
            'total_count': total_count
        }

# ============================================================
# PERFORMANCE ANALYSIS TOOLS
# ============================================================

def analyze_query_performance(func):
    """
    Decorator to analyze query performance in detail
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not settings.DEBUG:
            return func(*args, **kwargs)
        
        # Reset query log
        connection.queries_log.clear()
        
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        # Analyze queries
        queries = connection.queries
        query_count = len(queries)
        query_time = sum(float(q['time']) for q in queries)
        
        # Detect potential N+1 queries
        similar_queries = {}
        for query in queries:
            sql_pattern = query['sql'][:100]  # First 100 chars as pattern
            similar_queries[sql_pattern] = similar_queries.get(sql_pattern, 0) + 1
        
        n_plus_one_suspects = [
            (pattern, count) for pattern, count in similar_queries.items() 
            if count > 3
        ]
        
        # Log detailed analysis
        perf_logger.info(
            f"Query Analysis | {func.__name__} | "
            f"Total Time: {end_time - start_time:.3f}s | "
            f"Query Count: {query_count} | "
            f"Query Time: {query_time:.3f}s"
        )
        
        if n_plus_one_suspects:
            perf_logger.warning(
                f"Potential N+1 queries detected in {func.__name__}: {n_plus_one_suspects}"
            )
        
        return result
    return wrapper

# ============================================================
# API RESPONSE OPTIMIZATION
# ============================================================

def optimize_json_response(data):
    """
    Optimize JSON response data for better performance
    """
    # Convert datetime objects to strings to avoid serialization overhead
    if isinstance(data, dict):
        for key, value in data.items():
            if hasattr(value, 'isoformat'):
                data[key] = value.isoformat()
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, dict):
                data[i] = optimize_json_response(item)
    
    return data