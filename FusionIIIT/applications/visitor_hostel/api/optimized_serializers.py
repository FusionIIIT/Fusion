"""
Optimized serializers for Visitor Hostel API
Focus on performance improvements and reducing database queries
"""

from rest_framework import serializers
from django.db.models import Prefetch, Q
from applications.visitor_hostel.models import BookingDetail, RoomDetail, VisitorDetail, MealRecord, Bill

class OptimizedBookingListSerializer(serializers.ModelSerializer):
    """
    High-performance serializer for booking lists with minimal database queries
    """
    intender_name = serializers.SerializerMethodField()
    guest_name = serializers.SerializerMethodField()
    visitor_email = serializers.SerializerMethodField()
    room_numbers = serializers.SerializerMethodField()
    meal_count = serializers.SerializerMethodField()
    total_bill = serializers.SerializerMethodField()
    
    class Meta:
        model = BookingDetail
        fields = [
            'id', 'booking_from', 'booking_to', 'status', 
            'visitor_category', 'person_count', 'number_of_rooms',
            'intender_name', 'guest_name', 'visitor_email', 
            'room_numbers', 'meal_count', 'total_bill',
            'booking_date', 'is_offline', 'booking_source'
        ]
    
    def get_intender_name(self, obj):
        """Use prefetched intender data"""
        return obj.intender.get_full_name() or obj.intender.username
    
    def get_guest_name(self, obj):
        """Use prefetched visitor data"""
        visitors = obj.visitor.all()
        return visitors[0].visitor_name if visitors else 'N/A'
    
    def get_visitor_email(self, obj):
        """Use prefetched visitor data"""
        visitors = obj.visitor.all()
        return visitors[0].visitor_email if visitors else 'N/A'
    
    def get_room_numbers(self, obj):
        """Use prefetched room data"""
        return [room.room_number for room in obj.rooms.all()]
    
    def get_meal_count(self, obj):
        """Use prefetched meal data"""
        meals = getattr(obj, 'meal_records', [])
        return sum(
            meal.morning_tea + meal.breakfast + meal.lunch + 
            meal.eve_tea + meal.dinner for meal in meals
        )
    
    def get_total_bill(self, obj):
        """Use prefetched bill data"""
        bill = getattr(obj, 'bill_data', None)
        if bill:
            return bill.meal_bill + bill.room_bill + bill.extra_charges
        return None

    @classmethod
    def get_optimized_queryset(cls, base_queryset):
        """
        Return queryset optimized for this serializer
        Eliminates N+1 queries through strategic prefetching
        """
        return base_queryset.select_related(
            'intender', 'caretaker'
        ).prefetch_related(
            'rooms',
            'visitor',
            Prefetch(
                'mealrecord_set',
                queryset=MealRecord.objects.select_related('visitor'),
                to_attr='meal_records'
            ),
            Prefetch(
                'bill',
                queryset=Bill.objects.select_related('caretaker'),
                to_attr='bill_data'
            )
        )

class OptimizedRoomSerializer(serializers.ModelSerializer):
    """
    Optimized room serializer for availability checks
    """
    is_available = serializers.SerializerMethodField()
    current_occupant = serializers.SerializerMethodField()
    
    class Meta:
        model = RoomDetail
        fields = ['room_number', 'room_type', 'capacity', 'status', 'is_available', 'current_occupant']
    
    def get_is_available(self, obj):
        """Check availability based on prefetched booking data"""
        # This would be calculated in the view and passed via context
        return self.context.get('available_rooms', {}).get(obj.id, True)
    
    def get_current_occupant(self, obj):
        """Get current occupant from prefetched data"""
        # This would be calculated in the view and passed via context
        return self.context.get('room_occupants', {}).get(obj.id, None)

class OptimizedInventorySerializer(serializers.ModelSerializer):
    """
    Optimized inventory serializer with critical status calculation
    """
    is_critical = serializers.SerializerMethodField()
    last_updated = serializers.SerializerMethodField()
    
    class Meta:
        model = None  # Would import from models
        fields = ['item_name', 'quantity', 'threshold_quantity', 'is_critical', 'last_updated']
    
    def get_is_critical(self, obj):
        """Calculate critical status efficiently"""
        return obj.quantity <= obj.threshold_quantity
    
    def get_last_updated(self, obj):
        """Get last update timestamp"""
        return obj.updated_at.isoformat() if hasattr(obj, 'updated_at') else None

# ============================================================
# BULK SERIALIZATION HELPERS
# ============================================================

class BulkSerializationMixin:
    """
    Mixin for efficient bulk serialization
    """
    
    @classmethod
    def serialize_bulk(cls, queryset, many=True, context=None):
        """
        Efficiently serialize large querysets
        """
        if hasattr(cls, 'get_optimized_queryset'):
            queryset = cls.get_optimized_queryset(queryset)
        
        serializer = cls(queryset, many=many, context=context or {})
        return serializer.data

class OptimizedPaginatedSerializer:
    """
    Custom paginated serializer for high-performance API responses
    """
    
    def __init__(self, queryset, serializer_class, page_size=20, page=1, context=None):
        self.queryset = queryset
        self.serializer_class = serializer_class
        self.page_size = page_size
        self.page = page
        self.context = context or {}
    
    def get_paginated_data(self):
        """
        Return paginated data with optimized queries
        """
        # Calculate offset and limit
        offset = (self.page - 1) * self.page_size
        limit = self.page_size
        
        # Optimize queryset if serializer supports it
        if hasattr(self.serializer_class, 'get_optimized_queryset'):
            optimized_queryset = self.serializer_class.get_optimized_queryset(self.queryset)
        else:
            optimized_queryset = self.queryset
        
        # Get paginated items
        items = list(optimized_queryset[offset:offset + limit])
        
        # Serialize data
        serializer = self.serializer_class(items, many=True, context=self.context)
        
        # Calculate pagination metadata
        has_next = len(items) == self.page_size
        has_previous = self.page > 1
        
        return {
            'results': serializer.data,
            'pagination': {
                'page': self.page,
                'page_size': self.page_size,
                'has_next': has_next,
                'has_previous': has_previous,
                'count': len(items)
            }
        }

# ============================================================
# PERFORMANCE OPTIMIZED API RESPONSE BUILDERS
# ============================================================

class OptimizedAPIResponseBuilder:
    """
    Builder class for creating optimized API responses
    """
    
    @staticmethod
    def build_booking_list_response(queryset, request=None, page=1, page_size=20):
        """
        Build optimized booking list response
        """
        # Use optimized pagination
        from applications.visitor_hostel.performance_optimizations import OptimizedPagination
        
        paginated_data = OptimizedPagination.paginate_queryset(
            queryset, page_size=page_size, page=page
        )
        
        # Serialize with optimized serializer
        serialized_data = OptimizedBookingListSerializer(
            paginated_data['items'], 
            many=True,
            context={'request': request} if request else {}
        ).data
        
        return {
            'success': True,
            'data': serialized_data,
            'pagination': {
                'page': paginated_data['page'],
                'page_size': paginated_data['page_size'],
                'has_next': paginated_data['has_next'],
                'count': paginated_data['count']
            },
            'meta': {
                'total_items': paginated_data.get('total_count'),
                'cache_hit': False  # Would be set by caching layer
            }
        }
    
    @staticmethod
    def build_room_availability_response(rooms, date_from, date_to, context=None):
        """
        Build optimized room availability response
        """
        serializer_context = context or {}
        serializer_context.update({
            'date_from': date_from,
            'date_to': date_to
        })
        
        serialized_data = OptimizedRoomSerializer(
            rooms, many=True, context=serializer_context
        ).data
        
        return {
            'success': True,
            'data': serialized_data,
            'meta': {
                'date_range': {
                    'from': date_from.isoformat() if hasattr(date_from, 'isoformat') else str(date_from),
                    'to': date_to.isoformat() if hasattr(date_to, 'isoformat') else str(date_to)
                },
                'total_rooms': len(serialized_data),
                'available_rooms': len([r for r in serialized_data if r['is_available']])
            }
        }

# ============================================================
# CACHING-AWARE SERIALIZERS
# ============================================================

class CachedSerializerMixin:
    """
    Mixin to add caching support to serializers
    """
    
    def to_representation(self, instance):
        """
        Override to add caching for expensive calculations
        """
        # Generate cache key based on object and serializer
        cache_key = f"serializer:{self.__class__.__name__}:{instance.pk}:{getattr(instance, 'updated_at', 'no_timestamp')}"
        
        # Try to get from cache
        from django.core.cache import cache
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        # Serialize and cache
        data = super().to_representation(instance)
        cache.set(cache_key, data, timeout=300)  # Cache for 5 minutes
        
        return data