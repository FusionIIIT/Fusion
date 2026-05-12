"""
High-Performance API Views for Visitor Hostel Module
Optimized for handling large datasets with minimal database queries
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Prefetch
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie

from applications.visitor_hostel.models import BookingDetail, RoomDetail, MealRecord
from applications.visitor_hostel.selectors import get_confirmed_or_checkedin_bookings_for_staff
from applications.visitor_hostel.performance_optimizations import (
    monitor_performance, cache_result, OptimizedPagination,
    bulk_fetch_meals_for_bookings, optimize_json_response
)
from applications.visitor_hostel.api.optimized_serializers import (
    OptimizedBookingListSerializer, OptimizedAPIResponseBuilder
)
from applications.visitor_hostel.logging_config import vh_logger

class HighPerformanceActiveBookingsApiView(APIView):
    """
    HIGH-PERFORMANCE VERSION of ActiveBookingsApiView
    
    Optimizations:
    - Eliminates N+1 queries with strategic prefetching
    - Implements intelligent caching
    - Uses bulk operations for meal records
    - Optimized pagination
    - Performance monitoring
    """
    
    @method_decorator(cache_page(60))  # Cache for 1 minute
    @method_decorator(vary_on_cookie)
    @monitor_performance('active_bookings_api')
    def get(self, request):
        """
        Get active bookings with optimized queries and caching
        """
        try:
            vh_logger.log_api_request(request, 'ActiveBookingsOptimized', request.user)
            
            # Check user permissions
            user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
            is_staff = ('VhIncharge' in user_roles or 'VhCaretaker' in user_roles 
                       or request.user.is_staff)
            
            # Get pagination parameters
            page = int(request.GET.get('page', 1))
            page_size = min(int(request.GET.get('page_size', 20)), 100)  # Max 100 items
            
            # Build optimized base queryset
            active_bookings = self._get_optimized_active_bookings_queryset(is_staff, request.user)
            
            # Apply filters
            active_bookings = self._apply_filters(active_bookings, request.GET)
            
            # Use optimized pagination
            paginated_data = OptimizedPagination.paginate_queryset(
                active_bookings, page_size=page_size, page=page
            )
            
            # Build optimized response
            response_data = OptimizedAPIResponseBuilder.build_booking_list_response(
                paginated_data['items'], request, page, page_size
            )
            
            # Add performance metadata
            response_data['meta'].update({
                'query_optimization': 'enabled',
                'cache_strategy': 'page_level',
                'api_version': 'v2_optimized'
            })
            
            return Response(optimize_json_response(response_data), status=status.HTTP_200_OK)
            
        except Exception as e:
            vh_logger.log_api_error(request, 'ActiveBookingsOptimized', e, request.user)
            return Response({
                'error': 'Failed to fetch active bookings',
                'details': str(e) if request.user.is_staff else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_optimized_active_bookings_queryset(self, is_staff, user):
        """
        Build highly optimized queryset for active bookings
        """
        base_queryset = BookingDetail.objects.filter(
            Q(status="Confirmed") | Q(status="CheckedIn"),
            booking_to__gte=timezone.now().date()
        )
        
        # Apply user-based filtering
        if not is_staff:
            base_queryset = base_queryset.filter(intender=user)
        
        # OPTIMIZATION: Strategic prefetching to eliminate N+1 queries
        optimized_queryset = base_queryset.select_related(
            'intender',           # For intender details
            'caretaker'           # For caretaker details
        ).prefetch_related(
            'rooms',              # For room numbers
            'visitor',            # For visitor details
            Prefetch(
                'mealrecord_set',
                queryset=MealRecord.objects.select_related('visitor'),
                to_attr='prefetched_meals'
            )
        ).order_by('-booking_date', 'booking_from')
        
        return optimized_queryset
    
    def _apply_filters(self, queryset, filters):
        """
        Apply query filters efficiently
        """
        # Status filter
        if 'status' in filters:
            queryset = queryset.filter(status=filters['status'])
        
        # Date range filter
        if 'from_date' in filters:
            queryset = queryset.filter(booking_from__gte=filters['from_date'])
        
        if 'to_date' in filters:
            queryset = queryset.filter(booking_to__lte=filters['to_date'])
        
        # Category filter
        if 'category' in filters:
            queryset = queryset.filter(visitor_category=filters['category'])
        
        # Search filter (optimized)
        if 'search' in filters and filters['search']:
            search_term = filters['search']
            queryset = queryset.filter(
                Q(intender__username__icontains=search_term) |
                Q(visitor__visitor_name__icontains=search_term) |
                Q(rooms__room_number__icontains=search_term)
            ).distinct()
        
        return queryset

class HighPerformanceRoomAvailabilityApiView(APIView):
    """
    HIGH-PERFORMANCE room availability checking
    """
    
    @cache_result(timeout=180, key_prefix='room_availability')  # Cache for 3 minutes
    @monitor_performance('room_availability_api')
    def get(self, request):
        """
        Get room availability with advanced caching and optimization
        """
        try:
            date_from = request.GET.get('from')
            date_to = request.GET.get('to')
            category = request.GET.get('category')
            
            if not date_from or not date_to:
                return Response({
                    'error': 'Both from and to dates are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Parse dates
            from datetime import datetime
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'error': 'Invalid date format. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get available rooms using optimized selector
            available_rooms = self._get_available_rooms_optimized(from_date, to_date, category)
            
            # Build optimized response
            response_data = OptimizedAPIResponseBuilder.build_room_availability_response(
                available_rooms, from_date, to_date, {
                    'category_filter': category
                }
            )
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            vh_logger.log_api_error(request, 'RoomAvailabilityOptimized', e, request.user)
            return Response({
                'error': 'Failed to check room availability',
                'details': str(e) if request.user.is_staff else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_available_rooms_optimized(self, from_date, to_date, category=None):
        """
        Optimized room availability calculation using database-level operations
        """
        # OPTIMIZATION: Use subquery to exclude booked rooms
        booked_rooms_subquery = BookingDetail.objects.filter(
            Q(booking_from__lte=from_date, booking_to__gte=from_date) |
            Q(booking_from__gte=from_date, booking_to__lte=to_date) |
            Q(booking_from__lte=to_date, booking_to__gte=to_date),
            status__in=['Confirmed', 'CheckedIn', 'Forward', 'Pending']
        ).values_list('rooms__id', flat=True)
        
        # Build available rooms query
        available_rooms = RoomDetail.objects.exclude(id__in=booked_rooms_subquery)
        
        if category:
            available_rooms = available_rooms.filter(room_number__startswith=category)
        
        return available_rooms.order_by('room_number')

class HighPerformanceDashboardApiView(APIView):
    """
    HIGH-PERFORMANCE dashboard with aggregated data and caching
    """
    
    @method_decorator(cache_page(300))  # Cache for 5 minutes
    @monitor_performance('dashboard_api')
    def get(self, request):
        """
        Get dashboard data with optimized aggregations
        """
        try:
            # Check permissions
            user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
            is_staff = ('VhIncharge' in user_roles or 'VhCaretaker' in user_roles 
                       or request.user.is_staff)
            
            if not is_staff:
                return Response({
                    'error': 'Only VH staff can access dashboard data'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get aggregated statistics
            dashboard_data = self._get_dashboard_statistics()
            
            # Add real-time alerts
            dashboard_data['alerts'] = self._get_real_time_alerts()
            
            # Add performance metrics
            dashboard_data['meta'] = {
                'cache_enabled': True,
                'last_updated': timezone.now().isoformat(),
                'data_freshness': '5_minutes'
            }
            
            return Response(dashboard_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            vh_logger.log_api_error(request, 'DashboardOptimized', e, request.user)
            return Response({
                'error': 'Failed to load dashboard data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_dashboard_statistics(self):
        """
        Get dashboard statistics with optimized queries
        """
        from django.db.models import Count, Sum
        from django.utils import timezone
        
        today = timezone.now().date()
        
        # OPTIMIZATION: Single query for booking statistics
        booking_stats = BookingDetail.objects.filter(
            booking_to__gte=today
        ).aggregate(
            total_bookings=Count('id'),
            pending_count=Count('id', filter=Q(status='Pending')),
            confirmed_count=Count('id', filter=Q(status='Confirmed')),
            checkedin_count=Count('id', filter=Q(status='CheckedIn')),
            forward_count=Count('id', filter=Q(status='Forward')),
            total_guests=Sum('person_count')
        )
        
        # OPTIMIZATION: Single query for room statistics
        room_stats = RoomDetail.objects.aggregate(
            total_rooms=Count('id'),
            available_rooms=Count('id', filter=~Q(
                id__in=BookingDetail.objects.filter(
                    booking_from__lte=today,
                    booking_to__gte=today,
                    status__in=['Confirmed', 'CheckedIn']
                ).values_list('rooms__id', flat=True)
            ))
        )
        
        return {
            'bookings': booking_stats,
            'rooms': room_stats,
            'occupancy_rate': (
                (room_stats['total_rooms'] - room_stats['available_rooms']) / 
                room_stats['total_rooms'] * 100
                if room_stats['total_rooms'] > 0 else 0
            )
        }
    
    def _get_real_time_alerts(self):
        """
        Get real-time alerts for dashboard
        """
        from django.utils import timezone
        from applications.visitor_hostel.services import detect_overstays, detect_due_checkouts
        
        alerts = []
        
        try:
            # Check for overstays
            overstays = detect_overstays()
            if overstays.exists():
                alerts.append({
                    'type': 'overstay',
                    'severity': 'high',
                    'count': overstays.count(),
                    'message': f'{overstays.count()} guest(s) have overstayed their checkout time'
                })
            
            # Check for due checkouts
            due_checkouts = detect_due_checkouts()
            if due_checkouts.exists():
                alerts.append({
                    'type': 'due_checkout',
                    'severity': 'medium',
                    'count': due_checkouts.count(),
                    'message': f'{due_checkouts.count()} guest(s) are due for checkout today'
                })
                
        except Exception as e:
            vh_logger.logger.warning(f"Failed to fetch real-time alerts: {str(e)}")
        
        return alerts

# ============================================================
# PERFORMANCE COMPARISON VIEW
# ============================================================

class PerformanceComparisonApiView(APIView):
    """
    View to compare performance between optimized and original implementations
    For development and testing purposes only
    """
    
    def get(self, request):
        """
        Run performance comparison tests
        """
        if not request.user.is_staff:
            return Response({
                'error': 'Only staff can access performance comparison'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # This would run both optimized and original versions and compare
        results = {
            'test_timestamp': timezone.now().isoformat(),
            'comparison_results': {
                'note': 'Performance comparison would be implemented here',
                'recommendation': 'Use HighPerformance views for production'
            }
        }
        
        return Response(results, status=status.HTTP_200_OK)