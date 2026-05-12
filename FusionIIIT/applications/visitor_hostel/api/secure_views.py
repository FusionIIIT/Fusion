"""
Secure API Views for Visitor Hostel with proper RBAC implementation
Demonstrates proper authentication, authorization, and data filtering
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from applications.visitor_hostel.models import BookingDetail, Bill, Inventory
from applications.visitor_hostel.logging_config import vh_logger
from applications.visitor_hostel.security.rbac import (
    VHBookingPermission, VHStaffPermission, VHInchargePermission,
    VHDataFilter, require_vh_permission, require_vh_staff, require_vh_incharge,
    VHPermission, validate_booking_access, get_user_vh_roles, has_permission
)
from applications.visitor_hostel.api.serializers import (
    RequestBookingSerializer, ConfirmBookingSerializer, CancelBookingSerializer
)
from applications.visitor_hostel.selectors import (
    get_active_bookings_queryset, get_pending_bookings_queryset,
    get_completed_bookings_for_user, get_booking_by_id
)
from applications.visitor_hostel.services import (
    create_booking_request, confirm_booking_service, cancel_booking_service
)

# ============================================================
# SECURE BOOKING VIEWS
# ============================================================

class SecureActiveBookingsApiView(APIView):
    """
    SECURE VERSION: Active bookings with proper RBAC
    - Authentication required
    - Data filtered based on user role
    - Proper permission checks
    """
    authentication_classes = []  # Will be set by DRF settings
    permission_classes = [IsAuthenticated, VHBookingPermission]
    
    @require_vh_permission(VHPermission.VIEW_OWN_BOOKINGS)
    def get(self, request):
        """Get active bookings with role-based filtering"""
        try:
            vh_logger.log_api_request(request, 'SecureActiveBookings', request.user)
            
            # Get base queryset
            base_queryset = get_active_bookings_queryset()
            
            # Apply role-based filtering
            filtered_bookings = VHDataFilter.filter_bookings_for_user(base_queryset, request.user)
            
            # Log access attempt
            vh_logger.log_security_event('booking_data_access', request.user, {
                'action': 'view_active_bookings',
                'user_roles': get_user_vh_roles(request.user),
                'total_bookings': base_queryset.count(),
                'accessible_bookings': filtered_bookings.count()
            }, request)
            
            # Serialize and return data
            bookings_data = []
            for booking in filtered_bookings:
                bookings_data.append({
                    'id': booking.id,
                    'booking_from': booking.booking_from,
                    'booking_to': booking.booking_to,
                    'status': booking.status,
                    'person_count': booking.person_count,
                    'intender_name': booking.intender.get_full_name(),
                    # Only include sensitive data for staff
                    **(self._get_sensitive_booking_data(booking, request.user) if has_permission(request.user, VHPermission.VIEW_ALL_BOOKINGS) else {})
                })
            
            return Response({
                'success': True,
                'data': bookings_data,
                'meta': {
                    'user_permissions': get_user_vh_roles(request.user),
                    'filtered_view': not has_permission(request.user, VHPermission.VIEW_ALL_BOOKINGS)
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            vh_logger.log_api_error(request, 'SecureActiveBookings', e, request.user)
            return Response({
                'error': 'Failed to retrieve bookings',
                'details': str(e) if request.user.is_staff else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_sensitive_booking_data(self, booking, user):
        """Get sensitive booking data for authorized users only"""
        return {
            'visitor_details': list(booking.visitor.values('visitor_name', 'visitor_email')),
            'room_numbers': [room.room_number for room in booking.rooms.all()],
            'contact_details': booking.visitor.first().visitor_phone if booking.visitor.exists() else None
        }

class SecurePendingBookingsApiView(APIView):
    """
    SECURE VERSION: Pending bookings (Staff only)
    """
    authentication_classes = []
    permission_classes = [IsAuthenticated, VHStaffPermission]
    
    @require_vh_staff
    def get(self, request):
        """Get pending bookings - VH staff only"""
        try:
            vh_logger.log_api_request(request, 'SecurePendingBookings', request.user)
            
            pending_bookings = get_pending_bookings_queryset()
            
            # Log staff access
            vh_logger.log_security_event('staff_data_access', request.user, {
                'action': 'view_pending_bookings',
                'booking_count': pending_bookings.count()
            }, request)
            
            bookings_data = []
            for booking in pending_bookings:
                bookings_data.append({
                    'id': booking.id,
                    'booking_from': booking.booking_from,
                    'booking_to': booking.booking_to,
                    'intender_name': booking.intender.get_full_name(),
                    'intender_email': booking.intender.email,
                    'person_count': booking.person_count,
                    'visitor_category': booking.visitor_category,
                    'booking_date': booking.booking_date,
                    'purpose': booking.purpose,
                    'visitor_details': list(booking.visitor.values('visitor_name', 'visitor_email', 'visitor_phone'))
                })
            
            return Response({
                'success': True,
                'data': bookings_data,
                'meta': {
                    'staff_view': True,
                    'user_role': get_user_vh_roles(request.user)
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            vh_logger.log_api_error(request, 'SecurePendingBookings', e, request.user)
            return Response({
                'error': 'Failed to retrieve pending bookings'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SecureBookingDetailApiView(APIView):
    """
    SECURE VERSION: Booking detail with access control
    """
    authentication_classes = []
    permission_classes = [IsAuthenticated]
    
    def get(self, request, booking_id):
        """Get booking detail with access validation"""
        try:
            # Validate access to specific booking
            allowed, booking = validate_booking_access(request.user, booking_id, 'view')
            
            if not allowed:
                return Response({
                    'error': 'Access denied - you can only view your own bookings'
                }, status=status.HTTP_403_FORBIDDEN)
            
            if not booking:
                return Response({
                    'error': 'Booking not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            vh_logger.log_api_request(request, 'SecureBookingDetail', request.user)
            
            # Build response based on user permissions
            booking_data = {
                'id': booking.id,
                'booking_from': booking.booking_from,
                'booking_to': booking.booking_to,
                'status': booking.status,
                'person_count': booking.person_count,
                'number_of_rooms': booking.number_of_rooms,
                'visitor_category': booking.visitor_category,
                'purpose': booking.purpose,
                'booking_date': booking.booking_date
            }
            
            # Add detailed information for staff or booking owner
            if VHDataFilter.can_access_booking(booking, request.user):
                booking_data.update({
                    'intender': {
                        'name': booking.intender.get_full_name(),
                        'email': booking.intender.email,
                        'username': booking.intender.username
                    },
                    'visitor_details': list(booking.visitor.values(
                        'visitor_name', 'visitor_email', 'visitor_phone', 
                        'visitor_address', 'visitor_organization'
                    )),
                    'room_details': [
                        {'room_number': room.room_number, 'room_type': room.room_type}
                        for room in booking.rooms.all()
                    ]
                })
            
            # Add staff-only information
            if has_permission(request.user, VHPermission.VIEW_ALL_BOOKINGS):
                booking_data.update({
                    'internal_notes': getattr(booking, 'internal_notes', None),
                    'caretaker_assigned': booking.caretaker.username if booking.caretaker else None,
                    'admin_actions_available': True
                })
            
            return Response({
                'success': True,
                'data': booking_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            vh_logger.log_api_error(request, 'SecureBookingDetail', e, request.user)
            return Response({
                'error': 'Failed to retrieve booking details'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============================================================
# SECURE BOOKING OPERATIONS
# ============================================================

class SecureRequestBookingApiView(APIView):
    """
    SECURE VERSION: Request booking with proper validation
    """
    authentication_classes = []
    permission_classes = [IsAuthenticated]
    
    @require_vh_permission(VHPermission.CREATE_BOOKING)
    def post(self, request):
        """Create booking request with security validation"""
        try:
            vh_logger.log_api_request(request, 'SecureRequestBooking', request.user)
            
            serializer = RequestBookingSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'error': 'Invalid booking data',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Security check: Users can only create bookings for themselves
            # (unless they are staff)
            if not has_permission(request.user, VHPermission.VIEW_ALL_BOOKINGS):
                # Non-staff users can only book for themselves
                if request.data.get('intender_id') and int(request.data['intender_id']) != request.user.id:
                    vh_logger.log_security_event('unauthorized_booking_attempt', request.user, {
                        'attempted_intender_id': request.data.get('intender_id'),
                        'user_id': request.user.id
                    }, request)
                    return Response({
                        'error': 'You can only create bookings for yourself'
                    }, status=status.HTTP_403_FORBIDDEN)
            
            # Create booking
            booking = create_booking_request(
                intender=request.user,
                **serializer.validated_data
            )
            
            vh_logger.log_booking_operation('create_request', booking.id, request.user, {
                'dates': f"{booking.booking_from} to {booking.booking_to}",
                'person_count': booking.person_count
            })
            
            return Response({
                'success': True,
                'booking_id': booking.id,
                'message': 'Booking request created successfully',
                'status': booking.status
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            vh_logger.log_api_error(request, 'SecureRequestBooking', e, request.user)
            return Response({
                'error': 'Failed to create booking request',
                'details': str(e) if request.user.is_staff else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SecureConfirmBookingApiView(APIView):
    """
    SECURE VERSION: Confirm booking (VH Incharge only)
    """
    authentication_classes = []
    permission_classes = [IsAuthenticated, VHInchargePermission]
    
    @require_vh_incharge
    def post(self, request):
        """Confirm booking - Incharge only"""
        try:
            vh_logger.log_api_request(request, 'SecureConfirmBooking', request.user)
            
            serializer = ConfirmBookingSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'error': 'Invalid confirmation data',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            booking_id = serializer.validated_data['booking_id']
            
            # Validate booking exists
            try:
                booking = get_booking_by_id(booking_id)
            except BookingDetail.DoesNotExist:
                return Response({
                    'error': 'Booking not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Business rule: Only pending/forward bookings can be confirmed
            if booking.status not in ['Pending', 'Forward']:
                return Response({
                    'error': f'Cannot confirm booking with status: {booking.status}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Confirm booking
            confirmed_booking = confirm_booking_service(
                booking_id=booking_id,
                approved_by=request.user,
                **{k: v for k, v in serializer.validated_data.items() if k != 'booking_id'}
            )
            
            vh_logger.log_booking_operation('confirm', booking_id, request.user, {
                'previous_status': booking.status,
                'new_status': confirmed_booking.status
            })
            
            return Response({
                'success': True,
                'booking_id': booking_id,
                'message': 'Booking confirmed successfully',
                'status': confirmed_booking.status
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            vh_logger.log_api_error(request, 'SecureConfirmBooking', e, request.user)
            return Response({
                'error': 'Failed to confirm booking',
                'details': str(e) if request.user.is_staff else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SecureCancelBookingApiView(APIView):
    """
    SECURE VERSION: Cancel booking with proper authorization
    """
    authentication_classes = []
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Cancel booking with role-based authorization"""
        try:
            vh_logger.log_api_request(request, 'SecureCancelBooking', request.user)
            
            serializer = CancelBookingSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'error': 'Invalid cancellation data',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            booking_id = serializer.validated_data['booking_id']
            
            # Validate booking access and modification rights
            allowed, booking = validate_booking_access(request.user, booking_id, 'cancel')
            
            if not allowed or not booking:
                return Response({
                    'error': 'Access denied - you cannot cancel this booking'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if user can modify this booking
            if not VHDataFilter.can_modify_booking(booking, request.user):
                vh_logger.log_security_event('unauthorized_booking_modification', request.user, {
                    'booking_id': booking_id,
                    'booking_status': booking.status,
                    'action': 'cancel'
                }, request)
                return Response({
                    'error': 'Cannot cancel booking in current status or insufficient permissions'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Cancel booking
            cancelled_booking = cancel_booking_service(
                booking_id=booking_id,
                cancelled_by=request.user,
                reason=serializer.validated_data.get('reason', 'User requested cancellation')
            )
            
            vh_logger.log_booking_operation('cancel', booking_id, request.user, {
                'reason': serializer.validated_data.get('reason'),
                'previous_status': booking.status
            })
            
            return Response({
                'success': True,
                'booking_id': booking_id,
                'message': 'Booking cancelled successfully',
                'status': cancelled_booking.status
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            vh_logger.log_api_error(request, 'SecureCancelBooking', e, request.user)
            return Response({
                'error': 'Failed to cancel booking',
                'details': str(e) if request.user.is_staff else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============================================================
# SECURE INVENTORY VIEWS
# ============================================================

class SecureInventoryListApiView(APIView):
    """
    SECURE VERSION: Inventory list with role-based access
    """
    authentication_classes = []
    permission_classes = [IsAuthenticated, VHStaffPermission]
    
    @require_vh_permission(VHPermission.VIEW_INVENTORY)
    def get(self, request):
        """Get inventory list - VH staff only"""
        try:
            vh_logger.log_api_request(request, 'SecureInventoryList', request.user)
            
            # Only staff can view inventory
            if not has_permission(request.user, VHPermission.VIEW_INVENTORY):
                return Response({
                    'error': 'Inventory access restricted to VH staff'
                }, status=status.HTTP_403_FORBIDDEN)
            
            inventory_items = Inventory.objects.all()
            
            vh_logger.log_security_event('inventory_access', request.user, {
                'action': 'view_inventory_list',
                'item_count': inventory_items.count()
            }, request)
            
            inventory_data = []
            for item in inventory_items:
                inventory_data.append({
                    'id': item.id,
                    'item_name': item.item_name,
                    'quantity': item.quantity,
                    'threshold_quantity': item.threshold_quantity,
                    'is_critical': item.quantity <= item.threshold_quantity,
                    'last_updated': item.updated_at if hasattr(item, 'updated_at') else None
                })
            
            return Response({
                'success': True,
                'data': inventory_data,
                'meta': {
                    'user_permissions': get_user_vh_roles(request.user),
                    'total_items': len(inventory_data),
                    'critical_items': len([item for item in inventory_data if item['is_critical']])
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            vh_logger.log_api_error(request, 'SecureInventoryList', e, request.user)
            return Response({
                'error': 'Failed to retrieve inventory data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)