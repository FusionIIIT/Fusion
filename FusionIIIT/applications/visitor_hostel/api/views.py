"""DRF API views for visitor_hostel.

Endpoints are added incrementally and delegate to selectors/services.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.utils import timezone

from applications.visitor_hostel.models import Bill, BookingDetail, Inventory
from applications.visitor_hostel.logging_config import vh_logger, handle_api_exception, create_error_response, log_errors
from applications.visitor_hostel.performance_optimizations import (
    cache_api_response, monitor_performance, OptimizedQueryMixin, 
    bulk_fetch_meals_for_bookings, optimize_json_response
)
from applications.visitor_hostel.api.optimized_serializers import (
    OptimizedBookingListSerializer, OptimizedAPIResponseBuilder
)
from applications.visitor_hostel.api.serializers import (
    AddInventorySerializer,
    BillGenerationSerializer,
    CancelBookingRequestSerializer,
    CancelBookingReviewSerializer,
    CancelBookingSerializer,
    CheckInSerializer,
    CheckOutSerializer,
    ConfirmBookingSerializer,
    DateRangeSerializer,
    EditRoomStatusSerializer,
    ForwardBookingSerializer,
    RecordMealSerializer,
    ReportDaysSerializer,
    RejectBookingSerializer,
    RequestBookingSerializer,
    SettleBillSerializer,
    UpdateBookingSerializer,
    UpdateInventorySerializer,
    UpdateVisitorInfoSerializer,
)
from applications.visitor_hostel.selectors import (
    get_active_bookings_queryset,
    get_available_rooms_between_dates,
    get_bills_in_range,
    get_vhcaretaker_user,
    has_overlapping_bookings,
    get_pending_bookings_queryset,
    get_vhincharge_user_legacy_preferred,
    get_completed_bookings_for_user,
    get_booking_by_id,
    get_cancel_requested_bookings_for_staff,
    get_cancel_requested_bookings_for_user_future,
    get_bookings_for_last_n_days,
    get_completed_or_canceled_bookings_for_staff,
    get_replenishment_requests_for_last_n_days,
    get_meals_for_booking,  # UC-VH-010: For meal booking indicators
)
from applications.visitor_hostel.services import (
    add_to_inventory_service,
    approve_cancel_booking_request_service,
    bill_generation_service_from_data,
    cancel_booking_request_service,
    cancel_booking_service,
    check_in_service,
    check_out_service,
    calculate_room_bill_for_booking,
    confirm_booking_service,
    detect_no_shows,
    detect_overstays,
    get_overstay_details,
    trigger_overstay_alerts,
    # BR-VH-010: Due checkout alert services  
    detect_due_checkouts,
    get_due_checkout_details,
    trigger_due_checkout_alerts,
    edit_room_status_service,
    forward_booking_service,
    record_meal_service,
    reject_cancel_booking_request_service,
    request_booking_service_from_data,
    reject_booking_service,
    settle_bill_service,
    update_booking_and_get_forwarded_rooms,
    update_inventory_service,
    update_visitor_info_service,
    # UC-VH-011: Inventory threshold & replenishment services
    check_inventory_thresholds,
    create_replenishment_request_service,
    approve_replenishment_request_service,
    reject_replenishment_request_service,
    update_inventory_quantity_service,
    get_critical_inventory_items,
    get_pending_replenishment_requests,
    mark_replenishment_received_service,
    estimate_cancellation_charges_for_booking,
    VisitorHostelServiceError,
)
from notification.views import visitors_hostel_notif
import datetime


class VisitorHostelApiHealthView(APIView):
    """Simple health endpoint for API routing verification."""

    def get(self, request):
        return Response({"module": "visitor_hostel", "status": "ok"})


class PendingBookingsApiView(APIView):
    def get(self, request):
        # Security: Role-specific visibility by view mode.
        # view=queue    -> operational queue (pending/forward)
        # view=bookings -> personal/staff booking list including rejected flows
        view_mode = request.query_params.get('view', 'queue')
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_incharge = 'VhIncharge' in user_roles or request.user.is_staff
        is_caretaker = 'VhCaretaker' in user_roles

        if view_mode == 'bookings':
            if is_incharge:
                pending_bookings = BookingDetail.objects.select_related('intender', 'caretaker').filter(
                    Q(status='Forward') |
                    Q(status='Rejected', forwarded_date__isnull=False)
                ).order_by('-booking_date', 'booking_from')
            elif is_caretaker:
                pending_bookings = BookingDetail.objects.select_related('intender', 'caretaker').filter(
                    Q(status='Pending') |
                    Q(status='Forward', caretaker=request.user) |
                    Q(status='Rejected', caretaker=request.user)
                ).order_by('-booking_date', 'booking_from')
            else:
                pending_bookings = BookingDetail.objects.select_related('intender', 'caretaker').filter(
                    Q(status='Pending') | Q(status='Forward') | Q(status='Rejected'),
                    intender=request.user,
                ).order_by('-booking_date', 'booking_from')
        else:
            if is_incharge:
                pending_bookings = BookingDetail.objects.select_related('intender', 'caretaker').filter(
                    status='Forward'
                ).order_by('booking_from')
            elif is_caretaker:
                pending_bookings = get_pending_bookings_queryset()
            else:
                pending_bookings = BookingDetail.objects.select_related('intender', 'caretaker').filter(
                    Q(status='Pending') | Q(status='Forward'),
                    intender=request.user,
                ).order_by('booking_from')
        
        data = [
            {
                'id': booking.id,
                'intender': booking.intender.username,
                'intender_name': booking.intender.get_full_name() or booking.intender.username,
                'booking_from': booking.booking_from,
                'booking_to': booking.booking_to,
                'status': booking.status,
                'guest_name': booking.visitor.first().visitor_name if booking.visitor.exists() else 'N/A',
                'guest_email': booking.visitor.first().visitor_email if booking.visitor.exists() else 'N/A',
                'visitor_category': booking.visitor_category,
                'person_count': booking.person_count,
                'number_of_rooms': booking.number_of_rooms,
                'created_at': str(booking.booking_date),
                # UC-VH-006: Include offline booking fields
                'is_offline': booking.is_offline,
                'booking_source': booking.booking_source,
                'intender_name_offline': booking.intender_name,
                'intender_phone_offline': booking.intender_phone,
                'intender_relation': booking.intender_relation,
            }
            for booking in pending_bookings
        ]
        return Response({'results': data})


class ActiveBookingsApiView(APIView):
    def get(self, request):
        # Security: Filter by user role
        # VhIncharge/VhCaretaker: See ALL active bookings
        # Regular users: See only their own bookings
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = 'VhIncharge' in user_roles or 'VhCaretaker' in user_roles or request.user.is_staff
        
        active_bookings = get_active_bookings_queryset()
        if not is_staff:
            # Regular user: only their own bookings
            active_bookings = active_bookings.filter(intender=request.user)
        
        # OPTIMIZATION: Bulk fetch meal records to avoid N+1 queries
        booking_ids = [booking.id for booking in active_bookings]
        meal_records_dict = {}
        try:
            from applications.visitor_hostel.models import MealRecord
            meal_records = MealRecord.objects.filter(booking_id__in=booking_ids)
            
            for meal in meal_records:
                if meal.booking_id not in meal_records_dict:
                    meal_records_dict[meal.booking_id] = []
                meal_records_dict[meal.booking_id].append(meal)
        except Exception:
            meal_records_dict = {}

        data = []
        for booking in active_bookings:
            # OPTIMIZATION: Use pre-fetched meal records
            booking_meals = meal_records_dict.get(booking.id, [])
            has_meals = len(booking_meals) > 0
            total_meals = sum(
                meal.morning_tea + meal.breakfast + meal.lunch + meal.eve_tea + meal.dinner
                for meal in booking_meals
            ) if has_meals else 0
            meal_booking_count = len(booking_meals)
            
            # OPTIMIZATION: Use pre-fetched visitor data
            first_visitor = booking.visitor.first() if booking.visitor.exists() else None
            guest_name = first_visitor.visitor_name if first_visitor else 'N/A'
            visitor_email = first_visitor.visitor_email if first_visitor else 'N/A'
            
            data.append({
                'id': booking.id,
                'intender': booking.intender.username,
                'intender_name': booking.intender.get_full_name() or booking.intender.username,
                'booking_from': booking.booking_from,
                'booking_to': booking.booking_to,
                'status': booking.status,
                'guest_name': guest_name,
                'visitor_email': visitor_email,
                'visitor_category': booking.visitor_category,
                'person_count': booking.person_count,
                'number_of_rooms': booking.number_of_rooms,
                'created_at': str(booking.booking_date),
                # UC-VH-006: Include offline booking fields
                'is_offline': booking.is_offline,
                'booking_source': booking.booking_source,
                # UC-VH-010: Meal booking status
                'has_meal_bookings': has_meals,
                'total_meals_booked': total_meals,
                'meal_booking_count': meal_booking_count,
            })
        return Response({'results': data})


class RoomAvailabilityApiView(APIView):
    def get(self, request):
        serializer = DateRangeSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        rooms = get_available_rooms_between_dates(
            serializer.validated_data['start_date'],
            serializer.validated_data['end_date'],
            category=serializer.validated_data.get('category') or None,
        )
        return Response({'available_rooms': [room.room_number for room in rooms]})


class ConfirmBookingApiView(APIView):
    """
    Enhanced Booking Confirmation API with comprehensive logging
    
    - Enforces VhIncharge authorization
    - Logs all booking confirmation operations  
    - Provides user-friendly error handling
    """
    
    def post(self, request):
        try:
            # Log API request
            vh_logger.log_api_request(request, 'ConfirmBooking', request.user)
            
            # SECURITY: Only VhIncharge can confirm bookings and allocate rooms
            user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
            is_incharge = 'VhIncharge' in user_roles or request.user.is_staff
            
            if not is_incharge:
                # Log security violation
                vh_logger.log_security_event(
                    'UNAUTHORIZED_BOOKING_CONFIRMATION',
                    f"User {request.user.username} attempted to confirm booking without VhIncharge role",
                    user=request.user,
                    ip=self._get_client_ip(request)
                )
                return create_error_response(
                    'Only VhIncharge can confirm bookings and allocate rooms.',
                    status_code=403,
                    error_code='INSUFFICIENT_PERMISSIONS'
                )
            
            serializer = ConfirmBookingSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            booking = get_booking_by_id(serializer.validated_data['booking_id'])
            if booking.status != 'Forward':
                return Response(
                    {'detail': 'Only forwarded bookings can be confirmed by VhIncharge.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            overlap_exists = has_overlapping_bookings(
                booking_from=booking.booking_from,
                booking_to=booking.booking_to,
                statuses=['Confirmed', 'CheckedIn'],
                intender=booking.intender,
                exclude_booking_id=booking.id,
            )
            if overlap_exists:
                return Response(
                    {'detail': 'Overlapping confirmed booking exists for this intender in selected dates.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Log booking operation
            vh_logger.log_booking_operation(
                'CONFIRM',
                serializer.validated_data['booking_id'],
                request.user,
                {
                    'category': serializer.validated_data['category'],
                    'rooms': serializer.validated_data['rooms'],
                    'original_status': booking.status
                }
            )

            confirm_booking_service(
                booking_id=serializer.validated_data['booking_id'],
                category=serializer.validated_data['category'],
                rooms=serializer.validated_data['rooms'],
                acting_user=request.user,
                notify_fn=visitors_hostel_notif,
            )

            # Log successful confirmation
            vh_logger.log_booking_operation(
                'CONFIRM_SUCCESS',
                serializer.validated_data['booking_id'],
                request.user,
                {'rooms_allocated': serializer.validated_data['rooms']}
            )

            return Response({
                'detail': 'Booking confirmed and rooms allocated successfully.',
                'security_note': 'Room allocation completed by VhIncharge as required.'
            }, status=status.HTTP_200_OK)

        except VisitorHostelServiceError as exc:
            # Log business rule violation
            vh_logger.log_business_rule_violation(
                'BOOKING_CONFIRMATION_FAILED',
                str(exc),
                {'booking_id': serializer.validated_data.get('booking_id'), 'user': request.user.username},
                user=request.user
            )
            return create_error_response(str(exc), status_code=400, error_code='BUSINESS_RULE_VIOLATION')
        except Exception as exc:
            return handle_api_exception(request, exc, 'ConfirmBooking')


class CancelBookingApiView(APIView):
    def post(self, request):
        # UC-VH-004: Caretaker confirms/finalizes cancellation requests.
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_caretaker = ('VhCaretaker' in user_roles)
        
        if not is_caretaker:
            return Response(
                {'detail': 'Permission denied. Only VhCaretaker can finalize cancellation.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = CancelBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking = get_booking_by_id(serializer.validated_data['booking_id'])
        if booking.status != 'CancelRequested':
            return Response(
                {'detail': 'Only cancellation requests can be finalized.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cancellation_charges = cancel_booking_service(
            booking_id=serializer.validated_data['booking_id'],
            remark=serializer.validated_data.get('remark', ''),
            charges=serializer.validated_data.get('charges'),
            acting_user=request.user,
            notify_fn=visitors_hostel_notif,
        )
        return Response(
            {
                'detail': 'Booking cancelled.',
                'cancellation_charges': int(cancellation_charges or 0),
            },
            status=status.HTTP_200_OK,
        )


class CancelBookingRequestApiView(APIView):
    def post(self, request):
        # Security: Only booking intender can request cancellation
        serializer = CancelBookingRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Import BookingDetail locally to check ownership
        from applications.visitor_hostel.models import BookingDetail
        try:
            booking = BookingDetail.objects.get(id=serializer.validated_data['booking_id'])
        except BookingDetail.DoesNotExist:
            return Response({'detail': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # Only allow the booking intender to request cancellation
        is_intender = booking.intender == request.user
        
        if not is_intender:
            return Response(
                {'detail': 'Permission denied. Only booking intender can request cancellation.'},
                status=status.HTTP_403_FORBIDDEN
            )

        allowed_statuses = {'Pending', 'Forward', 'Confirmed'}
        if booking.status not in allowed_statuses:
            return Response(
                {
                    'detail': (
                        'Cancellation request is allowed only for pending, forwarded, or confirmed bookings.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        estimated_cancellation_charges = estimate_cancellation_charges_for_booking(booking)

        cancel_booking_request_service(
            booking_id=serializer.validated_data['booking_id'],
            remark=serializer.validated_data.get('remark', ''),
        )

        caretaker_user = get_vhcaretaker_user()
        if caretaker_user:
            visitors_hostel_notif(request.user, caretaker_user, 'cancellation_request_placed')
        incharge_user = get_vhincharge_user_legacy_preferred()
        if incharge_user:
            visitors_hostel_notif(request.user, incharge_user, 'cancellation_request_placed')
        return Response(
            {
                'detail': 'Cancellation request placed.',
                'estimated_cancellation_charges': int(estimated_cancellation_charges or 0),
            },
            status=status.HTTP_200_OK,
        )


class CancelRequestedBookingsApiView(APIView):
    def get(self, request):
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = ('VhIncharge' in user_roles or 'VhCaretaker' in user_roles or request.user.is_staff)

        if is_staff:
            bookings = get_cancel_requested_bookings_for_staff()
        else:
            bookings = get_cancel_requested_bookings_for_user_future(request.user)

        data = [
            {
                'id': booking.id,
                'intender': booking.intender.username,
                'intender_name': booking.intender.get_full_name() or booking.intender.username,
                'booking_from': booking.booking_from,
                'booking_to': booking.booking_to,
                'status': booking.status,
                'visitor_email': booking.visitor.first().visitor_email if booking.visitor.exists() else 'N/A',
                'visitor_category': booking.visitor_category,
                'number_of_rooms': booking.number_of_rooms,
                'remark': booking.remark,
                'estimated_cancellation_charges': int(
                    estimate_cancellation_charges_for_booking(booking)
                ),
            }
            for booking in bookings
        ]
        return Response({'results': data}, status=status.HTTP_200_OK)


class ApproveCancelBookingRequestApiView(APIView):
    def post(self, request):
        # Security: Only caretaker can approve/finalize cancellation requests
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_caretaker = 'VhCaretaker' in user_roles

        if not is_caretaker:
            return Response(
                {'detail': 'Permission denied. Only VhCaretaker can approve cancellation requests.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CancelBookingReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking = get_booking_by_id(serializer.validated_data['booking_id'])
        if booking.status != 'CancelRequested':
            return Response(
                {'detail': 'Booking is not in cancellation-request state.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        approve_cancel_booking_request_service(
            booking_id=serializer.validated_data['booking_id'],
            remark=serializer.validated_data.get('remark', ''),
        )
        try:
            cancellation_charges = cancel_booking_service(
                booking_id=serializer.validated_data['booking_id'],
                remark=serializer.validated_data.get('remark', ''),
                charges=None,
                acting_user=request.user,
                notify_fn=visitors_hostel_notif,
                payment_mode='online',
                transaction_id=serializer.validated_data.get('transaction_id', ''),
            )
        except VisitorHostelServiceError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                'detail': 'Cancellation request approved and booking cancelled by caretaker.',
                'cancellation_charges': int(cancellation_charges or 0),
            },
            status=status.HTTP_200_OK,
        )


class RejectCancelBookingRequestApiView(APIView):
    def post(self, request):
        # Security: Only caretaker can reject cancellation requests
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_caretaker = 'VhCaretaker' in user_roles

        if not is_caretaker:
            return Response(
                {'detail': 'Permission denied. Only VhCaretaker can reject cancellation requests.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CancelBookingReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reject_cancel_booking_request_service(
            booking_id=serializer.validated_data['booking_id'],
            remark=serializer.validated_data.get('remark', ''),
        )
        return Response({'detail': 'Cancellation request rejected by caretaker.'}, status=status.HTTP_200_OK)


class RejectBookingApiView(APIView):
    def post(self, request):
        # Security: VhIncharge and VhCaretaker can reject bookings
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_incharge = ('VhIncharge' in user_roles or request.user.is_staff)
        is_caretaker = ('VhCaretaker' in user_roles)
        is_staff = (is_incharge or is_caretaker)
        
        if not is_staff:
            return Response(
                {'detail': 'Permission denied. Only VhIncharge/VhCaretaker can reject bookings.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = RejectBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking = get_booking_by_id(serializer.validated_data['booking_id'])
        if is_caretaker and booking.status != 'Pending':
            return Response(
                {'detail': 'VhCaretaker can reject only pending bookings.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if is_incharge and booking.status != 'Forward':
            return Response(
                {'detail': 'VhIncharge can reject only forwarded bookings.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reject_booking_service(
            booking_id=serializer.validated_data['booking_id'],
            remark=serializer.validated_data.get('remark', ''),
            acting_user=request.user,
        )
        return Response({'detail': 'Booking rejected.'}, status=status.HTTP_200_OK)


class ForwardBookingApiView(APIView):
    def post(self, request):
        # Security: Only VhCaretaker can forward bookings to VhIncharge
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_caretaker = 'VhCaretaker' in user_roles
        
        if not is_caretaker:
            return Response(
                {'detail': 'Permission denied. Only VhCaretaker can forward bookings.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ForwardBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking = get_booking_by_id(serializer.validated_data['booking_id'])
        if booking.status != 'Pending':
            return Response(
                {'detail': 'Only pending bookings can be forwarded.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        modified_category = booking.visitor_category
        forward_booking_service(
            booking_id=serializer.validated_data['booking_id'],
            modified_category=modified_category,
            rooms=serializer.validated_data.get('rooms', []),
            remark=serializer.validated_data.get('remark', ''),
            bill_settlement=serializer.validated_data.get('bill_settlement') or None,
            acting_user=request.user,
        )
        incharge_user = get_vhincharge_user_legacy_preferred()
        if incharge_user:
            visitors_hostel_notif(request.user, incharge_user, 'booking_forwarded')
        return Response({'detail': 'Booking forwarded.'}, status=status.HTTP_200_OK)


class CheckOutApiView(APIView):
    def post(self, request):
        # Security: Only VhCaretaker/VhIncharge can check-out visitors
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = ('VhIncharge' in user_roles or 'VhCaretaker' in user_roles 
                    or request.user.is_staff)
        
        if not is_staff:
            return Response(
                {'detail': 'Permission denied. Only VhCaretaker/VhIncharge can perform check-out.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = CheckOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking = get_booking_by_id(serializer.validated_data['booking_id'])
        if booking.status != 'CheckedIn':
            return Response(
                {'detail': 'Only checked-in bookings can be checked out.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        check_out_service(
            booking_id=serializer.validated_data['booking_id'],
            meal_bill=serializer.validated_data['meal_bill'],
            room_bill=serializer.validated_data.get('room_bill'),
            extra_charges=serializer.validated_data.get('extra_charges', 0),
            payment_mode=serializer.validated_data['payment_mode'],
            transaction_id=serializer.validated_data.get('transaction_id', ''),
            payment_screenshot=serializer.validated_data.get('payment_screenshot'),
            offline_bill_id=serializer.validated_data.get('offline_bill_id', ''),
            offline_bill_photo=serializer.validated_data.get('offline_bill_photo'),
            bill_settlement=serializer.validated_data.get('bill_settlement'),
            acting_user=request.user,
        )
        try:
            visitors_hostel_notif(request.user, booking.intender, 'booking_checkout_done')
        except Exception:
            # Notification failure should not break checkout completion.
            pass
        return Response({'detail': 'Checkout completed.'}, status=status.HTTP_200_OK)


class CheckInApiView(APIView):
    def post(self, request):
        # Security: Only VhCaretaker/VhIncharge can check-in visitors
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = ('VhIncharge' in user_roles or 'VhCaretaker' in user_roles 
                    or request.user.is_staff)
        
        if not is_staff:
            return Response(
                {'detail': 'Permission denied. Only VhCaretaker/VhIncharge can perform check-in.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = CheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking = get_booking_by_id(serializer.validated_data['booking_id'])
        if booking.status != 'Confirmed':
            return Response(
                {'detail': 'Only confirmed bookings can be checked in.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            check_in_service(
                booking_id=serializer.validated_data['booking_id'],
                visitor_name=serializer.validated_data['name'],
                visitor_phone=serializer.validated_data['phone'],
                visitor_email=serializer.validated_data.get('email', ''),
                visitor_address=serializer.validated_data.get('address', ''),
                check_in_date=datetime.date.today(),
            )
        except VisitorHostelServiceError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            visitors_hostel_notif(request.user, booking.intender, 'booking_checkin_done')
        except Exception:
            # Notification failure should not block successful check-in.
            pass
        return Response({'detail': 'Check-in completed.'}, status=status.HTTP_200_OK)


class UpdateBookingApiView(APIView):
    def post(self, request):
        # Security: Only booking intender OR staff can update booking
        serializer = UpdateBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Import BookingDetail locally to check ownership
        from applications.visitor_hostel.models import BookingDetail
        try:
            booking = BookingDetail.objects.get(id=serializer.validated_data['booking_id'])
        except BookingDetail.DoesNotExist:
            return Response({'detail': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # Only allow the booking intender OR staff to update booking
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = ('VhIncharge' in user_roles or 'VhCaretaker' in user_roles 
                    or request.user.is_staff)
        is_intender = booking.intender == request.user
        
        if not (is_intender or is_staff):
            return Response(
                {'detail': 'Permission denied. Only booking intender can update booking.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # SECURITY FIX: Only allow modification of PENDING bookings (before VhIncharge confirmation)
        if booking.status != 'Pending':
            return Response(
                {'detail': f'Booking modification is only allowed for pending bookings. Current status: {booking.status}. Once confirmed by VhIncharge, bookings cannot be modified.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        forwarded_rooms = update_booking_and_get_forwarded_rooms(
            booking_id=serializer.validated_data['booking_id'],
            person_count=serializer.validated_data.get('number_of_people', 1),
            purpose_of_visit=serializer.validated_data['purpose_of_visit'],
            booking_from=serializer.validated_data['booking_from'],
            booking_to=serializer.validated_data['booking_to'],
            number_of_rooms=serializer.validated_data['number_of_rooms'],
        )
        data = {
            str(key): [room.room_number for room in value]
            for key, value in forwarded_rooms.items()
        }
        return Response({'forwarded_rooms': data}, status=status.HTTP_200_OK)


class UpdateVisitorInfoApiView(APIView):
    def post(self, request):
        # Security: Only booking intender OR staff can update visitor info
        serializer = UpdateVisitorInfoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Import BookingDetail locally to check ownership
        from applications.visitor_hostel.models import BookingDetail
        try:
            booking = BookingDetail.objects.get(id=serializer.validated_data['booking_id'])
        except BookingDetail.DoesNotExist:
            return Response({'detail': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # Only allow the booking intender OR staff to update visitor info
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = ('VhIncharge' in user_roles or 'VhCaretaker' in user_roles 
                    or request.user.is_staff)
        is_intender = booking.intender == request.user
        
        if not (is_intender or is_staff):
            return Response(
                {'detail': 'Permission denied. Only booking intender or staff can update visitor information.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # UC-VH-003: Only allow modification if booking is Pending
        if booking.status != 'Pending':
            return Response(
                {'detail': 'Visitor information can only be modified for pending bookings.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        visitor = update_visitor_info_service(
            booking_id=serializer.validated_data['booking_id'],
            visitor_name=serializer.validated_data.get('visitor_name'),
            visitor_email=serializer.validated_data.get('visitor_email'),
            visitor_phone=serializer.validated_data.get('visitor_phone'),
            visitor_organization=serializer.validated_data.get('visitor_organization'),
            visitor_address=serializer.validated_data.get('visitor_address'),
            nationality=serializer.validated_data.get('nationality'),
        )
        
        return Response({
            'detail': 'Visitor information updated successfully.',
            'visitor_name': visitor.visitor_name,
            'visitor_email': visitor.visitor_email,
            'visitor_phone': visitor.visitor_phone,
            'visitor_organization': visitor.visitor_organization,
            'visitor_address': visitor.visitor_address,
            'nationality': visitor.nationality,
        }, status=status.HTTP_200_OK)


class RecordMealApiView(APIView):
    def post(self, request):
        # Security: Only VhCaretaker/VhIncharge can record meals
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = ('VhIncharge' in user_roles or 'VhCaretaker' in user_roles 
                    or request.user.is_staff)
        
        if not is_staff:
            return Response(
                {'detail': 'Permission denied. Only VhCaretaker/VhIncharge can record meals.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = RecordMealSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record_meal_service(
            booking_id=serializer.validated_data['booking_id'],
            visitor_id=serializer.validated_data['visitor_id'],
            meal_date=datetime.datetime.today(),
            m_tea=serializer.validated_data.get('m_tea', 0),
            breakfast=serializer.validated_data.get('breakfast', 0),
            lunch=serializer.validated_data.get('lunch', 0),
            eve_tea=serializer.validated_data.get('eve_tea', 0),
            dinner=serializer.validated_data.get('dinner', 0),
        )
        return Response({'detail': 'Meal record updated.'}, status=status.HTTP_200_OK)


class GetMealRecordsApiView(APIView):
    """
    GET /api/meals/records/<booking_id>/
    Get meal records for a specific booking (UC-VH-010)
    """
    def get(self, request, booking_id):
        # Security: User can only view meal records for their own booking UNLESS staff
        try:
            booking = get_booking_by_id(booking_id)
        except BookingDetail.DoesNotExist:
            return Response(
                {'detail': 'Booking not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = 'VhIncharge' in user_roles or 'VhCaretaker' in user_roles or request.user.is_staff
        is_owner = booking.intender == request.user
        
        if not (is_owner or is_staff):
            return Response(
                {'detail': 'Permission denied. You can only view meal records for your own bookings.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        meal_records = get_meals_for_booking(booking.id)
        meal_data = []
        total_cost = 0
        
        for meal_record in meal_records:
            meal_cost = (
                (meal_record.morning_tea * 10) +
                (meal_record.breakfast * 50) +
                (meal_record.lunch * 100) +
                (meal_record.eve_tea * 10) +
                (meal_record.dinner * 100)
            )
            total_cost += meal_cost
            
            meal_data.append({
                'id': meal_record.id,
                'meal_date': meal_record.meal_date,
                'visitor_name': meal_record.visitor.visitor_name,
                'visitor_id': meal_record.visitor.id,
                'meals': {
                    'morning_tea': meal_record.morning_tea,
                    'breakfast': meal_record.breakfast,
                    'lunch': meal_record.lunch,
                    'eve_tea': meal_record.eve_tea,
                    'dinner': meal_record.dinner,
                },
                'total_meals': (
                    meal_record.morning_tea + meal_record.breakfast + 
                    meal_record.lunch + meal_record.eve_tea + meal_record.dinner
                ),
                'meal_cost': meal_cost,
            })
        
        return Response({
            'booking_id': booking.id,
            'meal_records': meal_data,
            'total_cost': total_cost,
            'record_count': len(meal_data),
            'has_meals': len(meal_data) > 0
        }, status=status.HTTP_200_OK)


class AddInventoryApiView(APIView):
    def post(self, request):
        # Security: UC-VH-011 allows both VhIncharge and VhCaretaker to add inventory items
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_incharge = 'VhIncharge' in user_roles or request.user.is_staff
        is_caretaker = 'VhCaretaker' in user_roles
        
        if not (is_incharge or is_caretaker):
            return Response(
                {'detail': 'Permission denied. Only VhIncharge and VhCaretaker can add inventory items.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = AddInventorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        consumable = 'true' if serializer.validated_data['consumable'] else 'false'
        
        # UC-VH-011: Enhanced inventory with threshold management (BR-VH-007)
        # VhIncharge requirement: Bill photo is mandatory for inventory replenishment
        item = add_to_inventory_service(
            item_name=serializer.validated_data['item_name'],
            bill_number=serializer.validated_data['bill_number'],
            quantity=serializer.validated_data['quantity'],
            cost=serializer.validated_data['cost'],
            consumable=consumable,
            threshold_quantity=serializer.validated_data.get('threshold_quantity', 5),
            unit=serializer.validated_data.get('unit', 'pieces'),
            category=serializer.validated_data.get('category', ''),
            remark=serializer.validated_data.get('remark', ''),
            bill_photo=serializer.validated_data['bill_photo'],  # Required bill photo
        )
        return Response({
            'detail': 'Inventory item added successfully.',
            'item': {
                'id': item.id,
                'item_name': item.item_name,
                'quantity': item.quantity,
                'threshold_quantity': item.threshold_quantity,
                'unit': item.unit,
                'category': item.category,
                'is_critical': item.is_critical,
            }
        }, status=status.HTTP_201_CREATED)


class UpdateInventoryApiView(APIView):
    def post(self, request):
        # Security: Only VhIncharge can update inventory items
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_incharge = 'VhIncharge' in user_roles or request.user.is_staff
        
        if not is_incharge:
            return Response(
                {'detail': 'Permission denied. Only VhIncharge can update inventory items.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UpdateInventorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        update_inventory_service(
            item_id=serializer.validated_data['id'],
            quantity=serializer.validated_data['quantity'],
            bill_number=serializer.validated_data['bill_number'],
            cost=serializer.validated_data['cost'],
            bill_photo=serializer.validated_data['bill_photo'],  # Required bill photo
        )
        return Response({'detail': 'Inventory updated.'}, status=status.HTTP_200_OK)


class InventoryListApiView(APIView):
    def get(self, request):
        # Security: Only VhIncharge/VhCaretaker can view inventory list
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = 'VhIncharge' in user_roles or 'VhCaretaker' in user_roles or request.user.is_staff

        if not is_staff:
            return Response(
                {'detail': 'Permission denied. Only VhIncharge/VhCaretaker can view inventory.'},
                status=status.HTTP_403_FORBIDDEN
            )

        inventory_items = Inventory.objects.all().order_by('item_name')
        data = [
            {
                'id': item.id,
                'item_name': item.item_name,
                'quantity': item.quantity,
                'threshold_quantity': item.threshold_quantity,
                'unit': item.unit,
                'category': item.category,
                'consumable': item.consumable,
                'is_critical': item.is_critical,
                'pending_replenishment': item.pending_replenishment,
                'total_stock': item.total_stock,
                'inuse': item.inuse,
                'serviceable': item.serviceable,
            }
            for item in inventory_items
        ]

        return Response({'results': data}, status=status.HTTP_200_OK)


class EditRoomStatusApiView(APIView):
    def post(self, request):
        # Security: Only VhIncharge can edit room status
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_incharge = 'VhIncharge' in user_roles or request.user.is_staff
        
        if not is_incharge:
            return Response(
                {'detail': 'Permission denied. Only VhIncharge can edit room status.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = EditRoomStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        edit_room_status_service(
            room_number=serializer.validated_data['room_number'],
            room_status=serializer.validated_data['room_status'],
        )
        return Response({'detail': 'Room status updated.'}, status=status.HTTP_200_OK)


class BillBetweenDatesApiView(APIView):
    def get(self, request):
        # Security: Only VhIncharge/VhCaretaker can access bill reports
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = 'VhIncharge' in user_roles or 'VhCaretaker' in user_roles or request.user.is_staff
        
        if not is_staff:
            return Response(
                {'detail': 'Permission denied. Only VhIncharge/VhCaretaker can generate bill reports.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = DateRangeSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        bill_range_bw_dates = get_bills_in_range(
            serializer.validated_data['start_date'],
            serializer.validated_data['end_date'],
        )
        meal_total = 0
        room_total = 0
        extra_total = 0
        records = []
        for bill in bill_range_bw_dates:
            meal_total = meal_total + bill.meal_bill
            room_total = room_total + bill.room_bill
            extra_total = extra_total + int(getattr(bill, 'extra_charges', 0) or 0)
            total = bill.meal_bill + bill.room_bill + int(getattr(bill, 'extra_charges', 0) or 0)
            records.append(
                {
                    'bill_id': bill.id,
                    'booking_id': bill.booking.id,
                    'meal_bill': bill.meal_bill,
                    'room_bill': bill.room_bill,
                    'extra_charges': int(getattr(bill, 'extra_charges', 0) or 0),
                    'total_bill': total,
                }
            )
        return Response(
            {
                'meal_total': meal_total,
                'room_total': room_total,
                'extra_total': extra_total,
                'total_bill': meal_total + room_total + extra_total,
                'records': records,
            },
            status=status.HTTP_200_OK,
        )


class BookingReportsApiView(APIView):
    """UC-VH-012: Booking reports by day window for VH In-Charge."""

    def get(self, request):
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_incharge = 'VhIncharge' in user_roles or request.user.is_staff

        if not is_incharge:
            return Response(
                {'detail': 'Permission denied. Only VhIncharge can generate booking reports.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ReportDaysSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        days = serializer.validated_data['days']

        bookings = get_bookings_for_last_n_days(days)
        records = []
        offline_count = 0

        for booking in bookings:
            booking_source = (booking.booking_source or 'online').lower()
            audit_flag = bool(booking.is_offline or booking_source in ['offline', 'telephonic', 'walkin'])
            if audit_flag:
                offline_count += 1

            records.append(
                {
                    'booking_id': booking.id,
                    'booking_date': booking.booking_date,
                    'booking_from': booking.booking_from,
                    'booking_to': booking.booking_to,
                    'status': booking.status,
                    'intender': booking.intender.get_full_name() or booking.intender.username,
                    'visitor_category': booking.visitor_category,
                    'number_of_rooms': booking.number_of_rooms,
                    'person_count': booking.person_count,
                    'source': booking.booking_source or 'online',
                    'is_offline': booking.is_offline,
                    'audit_flag': audit_flag,
                }
            )

        return Response(
            {
                'report_type': 'bookings',
                'days': days,
                'total_bookings': len(records),
                'offline_audit_count': offline_count,
                'records': records,
            },
            status=status.HTTP_200_OK,
        )


class InventoryReportsApiView(APIView):
    """UC-VH-012: Inventory reports by day window for VH In-Charge."""

    def get(self, request):
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_incharge = 'VhIncharge' in user_roles or request.user.is_staff

        if not is_incharge:
            return Response(
                {'detail': 'Permission denied. Only VhIncharge can generate inventory reports.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ReportDaysSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        days = serializer.validated_data['days']

        requests = get_replenishment_requests_for_last_n_days(days)
        inventory_items = Inventory.objects.all().order_by('item_name')

        request_records = [
            {
                'request_id': req.id,
                'item_name': req.inventory_item.item_name,
                'requested_quantity': req.requested_quantity,
                'approved_quantity': req.approved_quantity,
                'status': req.status,
                'urgency': req.urgency,
                'requested_by': req.requested_by.username,
                'approved_by': req.approved_by.username if req.approved_by else None,
                'created_at': req.created_at,
            }
            for req in requests
        ]

        snapshot = [
            {
                'item_id': item.id,
                'item_name': item.item_name,
                'quantity': item.quantity,
                'threshold_quantity': item.threshold_quantity,
                'is_critical': item.is_critical,
                'pending_replenishment': item.pending_replenishment,
                'unit': item.unit,
                'category': item.category,
            }
            for item in inventory_items
        ]

        return Response(
            {
                'report_type': 'inventory',
                'days': days,
                'total_requests': len(request_records),
                'critical_items_count': len([item for item in snapshot if item['is_critical']]),
                'pending_replenishment_count': len([item for item in snapshot if item['pending_replenishment']]),
                'request_records': request_records,
                'inventory_snapshot': snapshot,
            },
            status=status.HTTP_200_OK,
        )


class DetectNoShowsApiView(APIView):
    def post(self, request):
        # Security: only VhCaretaker/VhIncharge can run no-show detection
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = ('VhIncharge' in user_roles or 'VhCaretaker' in user_roles or request.user.is_staff)

        if not is_staff:
            return Response(
                {'detail': 'Permission denied. Only VhCaretaker/VhIncharge can detect no-shows.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        no_shows = detect_no_shows()
        if no_shows.exists():
            caretaker_user = get_vhcaretaker_user()
            if caretaker_user:
                visitors_hostel_notif(request.user, caretaker_user, 'booking_no_show_alert')
        return Response(
            {
                'count': no_shows.count(),
                'bookings': [
                    {
                        'id': booking.id,
                        'intender': booking.intender.username,
                        'booking_from': booking.booking_from,
                        'booking_to': booking.booking_to,
                        'status': booking.status,
                    }
                    for booking in no_shows
                ],
            },
            status=status.HTTP_200_OK,
        )


class DetectOverstaysApiView(APIView):
    """
    BR-VH-018: Enhanced Overstay Detection API
    
    Detects overstays when checkout time is exceeded and triggers alerts.
    Logic: IF current_time > approved_checkout THEN alert
    """
    
    def get(self, request):
        """Get current overstay information without triggering alerts"""
        # Security: only VhCaretaker/VhIncharge can view overstay data
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = ('VhIncharge' in user_roles or 'VhCaretaker' in user_roles or request.user.is_staff)

        if not is_staff:
            return Response(
                {'detail': 'Permission denied. Only VhCaretaker/VhIncharge can view overstay data.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        overstays = detect_overstays()
        overstay_details = get_overstay_details(overstays)
        
        return Response(
            {
                'success': True,
                'overstay_count': len(overstay_details),
                'critical_overstays': sum(1 for o in overstay_details if o['is_critical']),
                'overstays': overstay_details,
                'message': f'Found {len(overstay_details)} overstay(s)'
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """
        BR-VH-018: Trigger overstay detection and send alerts
        
        Generates alerts when checkout time is exceeded.
        Effects: Prevents unauthorized extended stays.
        """
        # Security: only VhCaretaker/VhIncharge can run overstay detection
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = ('VhIncharge' in user_roles or 'VhCaretaker' in user_roles or request.user.is_staff)

        if not is_staff:
            return Response(
                {'detail': 'Permission denied. Only VhCaretaker/VhIncharge can detect overstays.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # BR-VH-018: Enhanced overstay detection with time checking
        overstays = detect_overstays()
        overstay_details = get_overstay_details(overstays)
        
        alert_results = {'alerts_sent': 0, 'critical_alerts': 0}
        
        if overstay_details:
            # Trigger BR-VH-018 compliant alerts
            alert_results = trigger_overstay_alerts(overstay_details)
        
        return Response(
            {
                'success': True,
                'overstay_count': len(overstay_details),
                'alerts_sent': alert_results['alerts_sent'],
                'critical_alerts': alert_results['critical_alerts'],
                'overstays': overstay_details,
                'message': f'Detected {len(overstay_details)} overstay(s), sent {alert_results["alerts_sent"]} alert(s)'
            },
            status=status.HTTP_200_OK,
        )


class DetectDueCheckoutsApiView(APIView):
    """
    BR-VH-010: Due Checkout Detection API
    
    Detects checkouts due today and triggers alerts for better operational control.
    Logic: Alert staff when departure time is approaching or due.
    """
    
    def get(self, request):
        """Get current due checkout information without triggering alerts"""
        # Security: only VhCaretaker/VhIncharge can view due checkout data
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = ('VhIncharge' in user_roles or 'VhCaretaker' in user_roles or request.user.is_staff)

        if not is_staff:
            return Response(
                {'detail': 'Permission denied. Only VhCaretaker/VhIncharge can view due checkout data.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        due_checkouts = detect_due_checkouts()
        due_checkout_details = get_due_checkout_details(due_checkouts)
        
        return Response(
            {
                'success': True,
                'due_checkout_count': len(due_checkout_details),
                'urgent_checkouts': sum(1 for c in due_checkout_details if c['is_urgent']),
                'due_checkouts': due_checkout_details,
                'message': f'Found {len(due_checkout_details)} checkout(s) due today'
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """
        BR-VH-010: Trigger due checkout detection and send alerts
        
        Generates alerts when departure time is approaching.
        Effects: Improves operational control.
        """
        # Security: only VhCaretaker/VhIncharge can run due checkout detection
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = ('VhIncharge' in user_roles or 'VhCaretaker' in user_roles or request.user.is_staff)

        if not is_staff:
            return Response(
                {'detail': 'Permission denied. Only VhCaretaker/VhIncharge can detect due checkouts.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # BR-VH-010: Due checkout detection with time checking
        due_checkouts = detect_due_checkouts()
        due_checkout_details = get_due_checkout_details(due_checkouts)
        
        alert_results = {'alerts_sent': 0, 'urgent_checkouts': 0}
        
        if due_checkout_details:
            # Trigger BR-VH-010 compliant alerts
            alert_results = trigger_due_checkout_alerts(due_checkout_details)
        
        return Response(
            {
                'success': True,
                'due_checkout_count': len(due_checkout_details),
                'alerts_sent': alert_results['alerts_sent'],
                'urgent_checkouts': alert_results['urgent_checkouts'],
                'due_checkouts': due_checkout_details,
                'message': f'Detected {len(due_checkout_details)} due checkout(s), sent {alert_results["alerts_sent"]} alert(s)'
            },
            status=status.HTTP_200_OK,
        )


class RequestBookingApiView(APIView):
    def post(self, request):
        # Security: User can only request bookings for themselves
        # (Not allow client to specify intender to prevent impersonation)
        serializer = RequestBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # UC-VH-006: Handle offline bookings
        is_offline = serializer.validated_data.get('is_offline', False)
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_caretaker = 'VhCaretaker' in user_roles

        # Only caretakers can create offline bookings
        if is_offline and not is_caretaker:
            return Response(
                {'detail': 'Permission denied. Only VhCaretaker can create offline bookings.'},
                status=status.HTTP_403_FORBIDDEN
            )

        payload = {
            'intender': request.user.id,  # ← Use user ID, not User object
            'booking_id': serializer.validated_data.get('booking_id', ''),
            'category': serializer.validated_data['category'],
            'person_count': serializer.validated_data['number_of_people'],
            'purpose_of_visit': serializer.validated_data['purpose_of_visit'],
            'booking_from': serializer.validated_data['booking_from'],
            'booking_to': serializer.validated_data['booking_to'],
            'booking_from_time': serializer.validated_data.get('booking_from_time', ''),
            'booking_to_time': serializer.validated_data.get('booking_to_time', ''),
            'remarks_during_booking_request': serializer.validated_data.get('remarks_during_booking_request', ''),
            'bill_to_be_settled_by': serializer.validated_data['bill_settlement'],
            'number_of_rooms': serializer.validated_data['number_of_rooms'],
            'visitor_name': serializer.validated_data['name'],
            'visitor_phone': serializer.validated_data['phone'],
            'visitor_email': serializer.validated_data.get('email', ''),
            'visitor_address': serializer.validated_data.get('address', ''),
            'visitor_organization': serializer.validated_data.get('organization', ''),
            'visitor_nationality': serializer.validated_data.get('nationality', ''),
            # UC-VH-006: Offline booking fields
            'is_offline': is_offline,
            'booking_source': serializer.validated_data.get('booking_source', 'online'),
            'intender_name': serializer.validated_data.get('intender_name', ''),
            'intender_phone': serializer.validated_data.get('intender_phone', ''),
            'intender_email': serializer.validated_data.get('intender_email', ''),
            'intender_relation': serializer.validated_data.get('intender_relation', ''),
        }
        try:
            request_booking_service_from_data(payload, request.FILES)
        except VisitorHostelServiceError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        caretaker_user = get_vhcaretaker_user()
        if caretaker_user:
            visitors_hostel_notif(request.user, caretaker_user, 'booking_request')
        return Response({'detail': 'Booking requested.'}, status=status.HTTP_200_OK)


class BillGenerationApiView(APIView):
    def post(self, request):
        # Security: Only VhIncharge can generate bills
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_incharge = 'VhIncharge' in user_roles or request.user.is_staff
        
        if not is_incharge:
            return Response(
                {'detail': 'Permission denied. Only VhIncharge can generate bills.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BillGenerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        bill_generation_service_from_data(
            username=request.user.username,
            v_id=serializer.validated_data['visitor'],
            meal_bill=serializer.validated_data['mess_bill'],
            room_bill=serializer.validated_data['room_bill'],
            status=serializer.validated_data['status'],
        )
        return Response({'detail': 'Bill generated.'}, status=status.HTTP_200_OK)


class SettleBillApiView(APIView):
    """
    BR-VH-014 Compliant Bill Settlement API
    
    Enforces Immutable Billing constraint: Bills MUST NOT be modified after checkout.
    Logic: IF status=Checked-out THEN lock
    """
    def post(self, request):
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_incharge = 'VhIncharge' in user_roles or request.user.is_staff

        if not is_incharge:
            return Response(
                {'detail': 'Permission denied. Only VhIncharge can settle bills.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = SettleBillSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking = get_booking_by_id(serializer.validated_data['booking_id'])
        if booking.status not in ['Complete', 'Canceled']:
            return Response(
                {'detail': 'Bill settlement is allowed only for completed or canceled bookings.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # BR-VH-014: Immutable Billing - Don't allow modification of core amounts after checkout
        existing_bill = Bill.objects.filter(booking=booking).first()
        
        # For existing bills that are checked out, ignore billing amount fields
        meal_bill = None
        room_bill = None
        extra_charges = None
        
        if not (existing_bill and booking.check_out is not None):
            # Only allow billing amounts if bill doesn't exist or booking not checked out
            meal_bill = serializer.validated_data.get('meal_bill')
            room_bill = serializer.validated_data.get('room_bill')
            extra_charges = serializer.validated_data.get('extra_charges')

        settle_bill_service(
            booking_id=serializer.validated_data['booking_id'],
            acting_user=request.user,
            bill_settlement=serializer.validated_data.get('bill_settlement'),
            payment_status=serializer.validated_data.get('payment_status', True),
            meal_bill=meal_bill,
            room_bill=room_bill,
            extra_charges=extra_charges,
            payment_mode=serializer.validated_data.get('payment_mode'),
            transaction_id=serializer.validated_data.get('transaction_id'),
            payment_screenshot=serializer.validated_data.get('payment_screenshot'),
            offline_bill_id=serializer.validated_data.get('offline_bill_id'),
            offline_bill_photo=serializer.validated_data.get('offline_bill_photo'),
        )

        return Response({'detail': 'Bill settled successfully.'}, status=status.HTTP_200_OK)


class CompletedBookingsApiView(APIView):
    def get(self, request):
        # Security: Filter by user role
        # VhIncharge/VhCaretaker: See ALL completed bookings
        # Regular users: See only their own completed bookings
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = 'VhIncharge' in user_roles or 'VhCaretaker' in user_roles or request.user.is_staff
        
        if is_staff:
            # Staff: use selector for all completed/canceled bookings
            completed_bookings = get_completed_or_canceled_bookings_for_staff()
        else:
            # Regular user: only their own completed bookings
            completed_bookings = get_completed_bookings_for_user(request.user)
        
        data = [
            {
                'id': booking.id,
                'intender': booking.intender.username,
                'intender_name': booking.intender.get_full_name() or booking.intender.username,
                'booking_from': booking.booking_from,
                'booking_to': booking.booking_to,
                'status': booking.status,
                'guest_name': booking.visitor.first().visitor_name if booking.visitor.exists() else 'N/A',
                'visitor_email': booking.visitor.first().visitor_email if booking.visitor.exists() else 'N/A',
                'visitor_category': booking.visitor_category,
                'person_count': booking.person_count,
                'number_of_rooms': booking.number_of_rooms,
                'created_at': str(booking.booking_date),
                'bill_to_be_settled_by': booking.bill_to_be_settled_by,
                'meal_bill': (
                    int(booking.bill.meal_bill)
                    if hasattr(booking, 'bill') and booking.bill is not None
                    else 0
                ),
                'room_bill': (
                    int(booking.bill.room_bill)
                    if hasattr(booking, 'bill') and booking.bill is not None
                    else 0
                ),
                'extra_charges': (
                    int(getattr(booking.bill, 'extra_charges', 0) or 0)
                    if hasattr(booking, 'bill') and booking.bill is not None
                    else 0
                ),
                'cancellation_charges': (
                    int(booking.bill.room_bill)
                    if (
                        booking.status == 'Canceled'
                        and hasattr(booking, 'bill')
                        and booking.bill is not None
                    )
                    else 0
                ),
                'total_bill': (
                    int(booking.bill.meal_bill)
                    + int(booking.bill.room_bill)
                    + int(getattr(booking.bill, 'extra_charges', 0) or 0)
                    if hasattr(booking, 'bill') and booking.bill is not None
                    else 0
                ),
                'bill_status': (
                    'paid'
                    if hasattr(booking, 'bill') and booking.bill is not None and booking.bill.payment_status
                    else 'pending'
                ),
                'payment_mode': (
                    booking.bill.payment_mode
                    if hasattr(booking, 'bill') and booking.bill is not None
                    else None
                ),
                'transaction_id': (
                    booking.bill.transaction_id
                    if hasattr(booking, 'bill') and booking.bill is not None
                    else None
                ),
                'offline_bill_id': (
                    booking.bill.offline_bill_id
                    if hasattr(booking, 'bill') and booking.bill is not None
                    else None
                ),
                'payment_screenshot': (
                    booking.bill.payment_screenshot.url
                    if (
                        hasattr(booking, 'bill')
                        and booking.bill is not None
                        and booking.bill.payment_screenshot
                    )
                    else None
                ),
                'offline_bill_photo': (
                    booking.bill.offline_bill_photo.url
                    if (
                        hasattr(booking, 'bill')
                        and booking.bill is not None
                        and booking.bill.offline_bill_photo
                    )
                    else None
                ),
                'cancelled_on': (
                    str(booking.bill.bill_date)
                    if (
                        booking.status == 'Canceled'
                        and hasattr(booking, 'bill')
                        and booking.bill is not None
                        and booking.bill.bill_date is not None
                    )
                    else None
                ),
                'cancellation_reason': booking.remark if booking.status == 'Canceled' else '',
                # UC-VH-006: Include offline booking fields
                'is_offline': booking.is_offline,
                'booking_source': booking.booking_source,
            }
            for booking in completed_bookings
        ]
        return Response({'results': data})


class BookingDetailApiView(APIView):
    def get(self, request, booking_id):
        # Security: User can only view their own booking UNLESS staff
        try:
            # Using selector instead of direct query
            booking = get_booking_by_id(booking_id)
        except BookingDetail.DoesNotExist:
            return Response(
                {'detail': 'Booking not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check access permission
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = 'VhIncharge' in user_roles or 'VhCaretaker' in user_roles or request.user.is_staff
        is_owner = booking.intender == request.user
        
        if not (is_owner or is_staff):
            return Response(
                {'detail': 'Permission denied. You can only view your own bookings.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Build response with all booking details
        detail_data = {
            'id': booking.id,
            'intender': booking.intender.username,
            'intender_name': booking.intender.get_full_name() or booking.intender.username,
            'intender_email': booking.intender.email,
            'intender_phone': getattr(booking.intender, 'phone', 'N/A'),
            'booking_from': booking.booking_from,
            'booking_to': booking.booking_to,
            'status': booking.status,
            'visitor_category': booking.visitor_category,
            'person_count': booking.person_count,
            'number_of_rooms': booking.number_of_rooms,
            'purpose_of_visit': booking.purpose,
            'bill_to_be_settled_by': booking.bill_to_be_settled_by,
            'remarks': booking.remark,
            'created_at': str(booking.booking_date),
            'meal_bill': (
                int(booking.bill.meal_bill)
                if hasattr(booking, 'bill') and booking.bill is not None
                else 0
            ),
            'room_bill': (
                int(booking.bill.room_bill)
                if hasattr(booking, 'bill') and booking.bill is not None
                else 0
            ),
            'extra_charges': (
                int(getattr(booking.bill, 'extra_charges', 0) or 0)
                if hasattr(booking, 'bill') and booking.bill is not None
                else 0
            ),
            'total_bill': (
                int(booking.bill.meal_bill)
                + int(booking.bill.room_bill)
                + int(getattr(booking.bill, 'extra_charges', 0) or 0)
                if hasattr(booking, 'bill') and booking.bill is not None
                else 0
            ),
            'bill_status': (
                'paid'
                if hasattr(booking, 'bill') and booking.bill is not None and booking.bill.payment_status
                else 'pending'
            ),
            'payment_mode': (
                booking.bill.payment_mode
                if hasattr(booking, 'bill') and booking.bill is not None
                else None
            ),
            'transaction_id': (
                booking.bill.transaction_id
                if hasattr(booking, 'bill') and booking.bill is not None
                else None
            ),
            'offline_bill_id': (
                booking.bill.offline_bill_id
                if hasattr(booking, 'bill') and booking.bill is not None
                else None
            ),
            'payment_screenshot': (
                booking.bill.payment_screenshot.url
                if (
                    hasattr(booking, 'bill')
                    and booking.bill is not None
                    and booking.bill.payment_screenshot
                )
                else None
            ),
            'offline_bill_photo': (
                booking.bill.offline_bill_photo.url
                if (
                    hasattr(booking, 'bill')
                    and booking.bill is not None
                    and booking.bill.offline_bill_photo
                )
                else None
            ),
            'visitors': [
                {
                    'id': v.id,
                    'name': v.visitor_name,
                    'email': v.visitor_email,
                    'phone': v.visitor_phone,
                    'address': v.visitor_address,
                    'organization': v.visitor_organization,
                    'nationality': v.nationality,
                }
                for v in booking.visitor.all()
            ] if booking.visitor.exists() else [],
            'rooms': [
                {
                    'room_number': r.room_number,
                    'room_status': r.room_status,
                }
                for r in booking.rooms.all()
            ] if booking.rooms.exists() else [],
        }
        
        # UC-VH-010: Add meal booking history with error handling
        try:
            meal_records = get_meals_for_booking(booking.id)
            detail_data['meal_bookings'] = []
            total_meals_cost = 0
            
            for meal_record in meal_records:
                meal_cost = (
                    (meal_record.morning_tea * 10) +
                    (meal_record.breakfast * 50) +
                    (meal_record.lunch * 100) +
                    (meal_record.eve_tea * 10) +
                    (meal_record.dinner * 100)
                )
                total_meals_cost += meal_cost
                
                detail_data['meal_bookings'].append({
                    'id': meal_record.id,
                    'meal_date': meal_record.meal_date,
                    'visitor_name': meal_record.visitor.visitor_name,
                    'visitor_id': meal_record.visitor.id,
                    'meals': {
                        'morning_tea': meal_record.morning_tea,
                        'breakfast': meal_record.breakfast,
                        'lunch': meal_record.lunch,
                        'eve_tea': meal_record.eve_tea,
                        'dinner': meal_record.dinner,
                    },
                    'total_meals': (
                        meal_record.morning_tea + meal_record.breakfast + 
                        meal_record.lunch + meal_record.eve_tea + meal_record.dinner
                    ),
                    'meal_cost': meal_cost,
                })
            
            detail_data['total_meals_cost'] = total_meals_cost
            detail_data['has_meal_bookings'] = len(meal_records) > 0
            detail_data['estimated_meal_bill'] = total_meals_cost
        except Exception as e:
            # If meal fetching fails, set empty meal data
            detail_data['meal_bookings'] = []
            detail_data['total_meals_cost'] = 0
            detail_data['has_meal_bookings'] = False
            detail_data['estimated_meal_bill'] = 0

        try:
            checkout_date = timezone.localdate()
            detail_data['estimated_room_bill'] = calculate_room_bill_for_booking(
                booking,
                from_date=booking.check_in or booking.booking_from,
                to_date=booking.check_out or checkout_date,
            )
        except Exception:
            detail_data['estimated_room_bill'] = 0

        detail_data['estimated_total_bill'] = (
            int(detail_data.get('estimated_meal_bill', 0) or 0)
            + int(detail_data.get('estimated_room_bill', 0) or 0)
        )
        
        return Response(detail_data, status=status.HTTP_200_OK)


# ============================================================
# UC-VH-011: INVENTORY THRESHOLD & REPLENISHMENT API ENDPOINTS
# ============================================================

class InventoryThresholdCheckApiView(APIView):
    def get(self, request):
        """UC-VH-011, BR-VH-007: Check inventory thresholds and get critical items"""
        # Security: Only staff can check thresholds
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = 'VhIncharge' in user_roles or 'VhCaretaker' in user_roles or request.user.is_staff

        if not is_staff:
            return Response(
                {'detail': 'Permission denied. Only VhCaretaker/VhIncharge can check inventory thresholds.'},
                status=status.HTTP_403_FORBIDDEN
            )

        critical_items = check_inventory_thresholds()
        data = [
            {
                'id': item.id,
                'item_name': item.item_name,
                'quantity': item.quantity,
                'threshold_quantity': item.threshold_quantity,
                'unit': item.unit,
                'category': item.category,
                'is_critical': item.is_critical,
                'pending_replenishment': item.pending_replenishment,
                'last_threshold_alert': item.last_threshold_alert,
            }
            for item in critical_items
        ]
        return Response({'critical_items': data})

    def post(self, request):
        """Manually trigger threshold check"""
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = 'VhIncharge' in user_roles or 'VhCaretaker' in user_roles or request.user.is_staff

        if not is_staff:
            return Response(
                {'detail': 'Permission denied. Only VhCaretaker/VhIncharge can trigger threshold checks.'},
                status=status.HTTP_403_FORBIDDEN
            )

        critical_items = check_inventory_thresholds()
        return Response({
            'detail': f'Threshold check completed. {len(critical_items)} items are below threshold.',
            'critical_count': len(critical_items)
        })


class ReplenishmentRequestApiView(APIView):
    def post(self, request):
        """UC-VH-011: Create replenishment request (Caretaker only)"""
        # Security: Only caretakers can create replenishment requests
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_caretaker = 'VhCaretaker' in user_roles

        if not is_caretaker:
            return Response(
                {'detail': 'Permission denied. Only VhCaretaker can create replenishment requests.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            item_id = request.data.get('item_id')
            requested_quantity = request.data.get('requested_quantity')
            urgency = request.data.get('urgency', 'medium')
            justification = request.data.get('justification', '')

            if not all([item_id, requested_quantity]):
                return Response(
                    {'detail': 'item_id and requested_quantity are required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            replenishment_request = create_replenishment_request_service(
                item_id=item_id,
                requested_quantity=requested_quantity,
                urgency=urgency,
                justification=justification,
                requested_by_user=request.user
            )

            return Response({
                'detail': 'Replenishment request created successfully.',
                'request_id': replenishment_request.id
            })

        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': f'Error creating request: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        """Get replenishment requests based on user role"""
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_incharge = 'VhIncharge' in user_roles or request.user.is_staff
        is_caretaker = 'VhCaretaker' in user_roles

        if not (is_incharge or is_caretaker):
            return Response(
                {'detail': 'Permission denied. Only VhIncharge/VhCaretaker can view replenishment requests.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if is_incharge:
            # VhIncharge can see all pending requests for approval
            requests = get_pending_replenishment_requests()
        else:
            # Caretaker can see their own requests
            from applications.visitor_hostel.models import ReplenishmentRequest
            requests = ReplenishmentRequest.objects.filter(requested_by=request.user).order_by('-created_at')

        data = [
            {
                'id': req.id,
                'item_name': req.inventory_item.item_name,
                'item_id': req.inventory_item.id,
                'requested_quantity': req.requested_quantity,
                'current_quantity': req.current_quantity,
                'urgency': req.urgency,
                'justification': req.justification,
                'status': req.status,
                'approved_quantity': req.approved_quantity,
                'approval_remarks': req.approval_remarks,
                'requested_by': req.requested_by.username,
                'approved_by': req.approved_by.username if req.approved_by else None,
                'created_at': req.created_at,
                'reviewed_at': req.reviewed_at,
                'days_pending': req.days_pending,
                'unit': req.inventory_item.unit,
            }
            for req in requests
        ]
        return Response({'requests': data})


class ApproveReplenishmentApiView(APIView):
    def post(self, request):
        """UC-VH-011, BR-VH-016: Approve replenishment request (VhIncharge only)"""
        # Security: Only VhIncharge can approve
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_incharge = 'VhIncharge' in user_roles or request.user.is_staff

        if not is_incharge:
            return Response(
                {'detail': 'Permission denied. Only VhIncharge can approve replenishment requests.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            request_id = request.data.get('request_id')
            approved_quantity = request.data.get('approved_quantity')
            approval_remarks = request.data.get('approval_remarks', '')

            if not all([request_id, approved_quantity]):
                return Response(
                    {'detail': 'request_id and approved_quantity are required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            replenishment_request = approve_replenishment_request_service(
                request_id=request_id,
                approved_quantity=approved_quantity,
                approval_remarks=approval_remarks,
                approved_by_user=request.user
            )

            return Response({
                'detail': 'Replenishment request approved successfully.',
                'approved_quantity': replenishment_request.approved_quantity
            })

        except (ValueError, PermissionError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': f'Error approving request: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RejectReplenishmentApiView(APIView):
    def post(self, request):
        """UC-VH-011, BR-VH-016: Reject replenishment request (VhIncharge only)"""
        # Security: Only VhIncharge can reject
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_incharge = 'VhIncharge' in user_roles or request.user.is_staff

        if not is_incharge:
            return Response(
                {'detail': 'Permission denied. Only VhIncharge can reject replenishment requests.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            request_id = request.data.get('request_id')
            approval_remarks = request.data.get('approval_remarks', '')

            if not request_id:
                return Response(
                    {'detail': 'request_id is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            replenishment_request = reject_replenishment_request_service(
                request_id=request_id,
                approval_remarks=approval_remarks,
                approved_by_user=request.user
            )

            return Response({
                'detail': 'Replenishment request rejected.',
                'rejection_reason': replenishment_request.approval_remarks
            })

        except (ValueError, PermissionError) as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': f'Error rejecting request: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateInventoryQuantityApiView(APIView):
    def post(self, request):
        """UC-VH-011: Update inventory quantity with threshold checking"""
        # Security: Only VhIncharge can update quantities
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_incharge = 'VhIncharge' in user_roles or request.user.is_staff

        if not is_incharge:
            return Response(
                {'detail': 'Permission denied. Only VhIncharge can update inventory quantities.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            item_id = request.data.get('item_id')
            new_quantity = request.data.get('quantity')
            operation = request.data.get('operation', 'set')  # 'set', 'add', 'subtract'

            if not all([item_id, new_quantity is not None]):
                return Response(
                    {'detail': 'item_id and quantity are required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            inventory_item = update_inventory_quantity_service(
                item_id=item_id,
                new_quantity=new_quantity,
                user=request.user,
                operation=operation
            )

            return Response({
                'detail': 'Inventory quantity updated successfully.',
                'item_name': inventory_item.item_name,
                'new_quantity': inventory_item.quantity,
                'is_critical': inventory_item.is_critical,
                'below_threshold': inventory_item.is_below_threshold
            })

        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': f'Error updating quantity: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MarkReplenishmentReceivedApiView(APIView):
    def post(self, request):
        """UC-VH-011: Mark replenishment as received and update inventory"""
        # Security: Only staff can mark as received
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = 'VhIncharge' in user_roles or 'VhCaretaker' in user_roles or request.user.is_staff

        if not is_staff:
            return Response(
                {'detail': 'Permission denied. Only VhIncharge/VhCaretaker can mark replenishment as received.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            request_id = request.data.get('request_id')
            actual_cost = request.data.get('actual_cost')
            delivery_date = request.data.get('delivery_date')

            if not request_id:
                return Response(
                    {'detail': 'request_id is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            replenishment_request = mark_replenishment_received_service(
                request_id=request_id,
                actual_cost=actual_cost,
                delivery_date=delivery_date,
                user=request.user
            )

            return Response({
                'detail': 'Replenishment marked as received and inventory updated.',
                'item_name': replenishment_request.inventory_item.item_name,
                'new_quantity': replenishment_request.inventory_item.quantity
            })

        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': f'Error marking as received: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# BR-VH-010: CHECK-IN / CHECK-OUT ALERTS VIEWS
# ============================================================================

class DetectNoShowAlertsApiView(APIView):
    """BR-VH-010: Detect and create no-show alerts"""
    
    def post(self, request):
        """Manually trigger no-show alert detection"""
        # Security: Only staff can trigger alert detection
        from applications.visitor_hostel.services import detect_and_create_no_show_alerts
        
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = 'VhIncharge' in user_roles or 'VhCaretaker' in user_roles or request.user.is_staff
        
        if not is_staff:
            return Response(
                {'detail': 'Permission denied. Only staff can trigger alert detection.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            alerts = detect_and_create_no_show_alerts()
            return Response({
                'detail': f'{len(alerts)} no-show alert(s) created.',
                'alerts_count': len(alerts),
                'alert_ids': [alert.id for alert in alerts]
            })
        except Exception as e:
            return Response(
                {'detail': f'Error detecting no-show alerts: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DetectDueCheckoutAlertsApiView(APIView):
    """BR-VH-010: Detect and create due checkout alerts"""
    
    def post(self, request):
        """Manually trigger due checkout alert detection"""
        from applications.visitor_hostel.services import detect_and_create_due_checkout_alerts
        
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = 'VhIncharge' in user_roles or 'VhCaretaker' in user_roles or request.user.is_staff
        
        if not is_staff:
            return Response(
                {'detail': 'Permission denied. Only staff can trigger alert detection.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            alerts = detect_and_create_due_checkout_alerts()
            return Response({
                'detail': f'{len(alerts)} due checkout alert(s) created.',
                'alerts_count': len(alerts),
                'alert_ids': [alert.id for alert in alerts]
            })
        except Exception as e:
            return Response(
                {'detail': f'Error detecting due checkout alerts: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetPendingAlertsApiView(APIView):
    """BR-VH-010: Get all pending alerts"""
    
    def get(self, request):
        """Retrieve all pending alerts, optionally filtered by booking_id"""
        from applications.visitor_hostel.services import get_pending_alerts_for_booking, get_all_pending_alerts
        from applications.visitor_hostel.api.serializers import CheckInCheckOutAlertSerializer
        
        booking_id = request.query_params.get('booking_id')
        
        # Security: Users can see alerts for their bookings, staff can see all
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = 'VhIncharge' in user_roles or 'VhCaretaker' in user_roles or request.user.is_staff
        
        try:
            if booking_id:
                # Get alerts for specific booking
                alerts = get_pending_alerts_for_booking(int(booking_id))
                
                # Security: Check if user has access to this booking
                if not is_staff:
                    booking = BookingDetail.objects.get(id=int(booking_id))
                    if booking.intender != request.user:
                        return Response(
                            {'detail': 'Permission denied. You can only access your own booking alerts.'},
                            status=status.HTTP_403_FORBIDDEN
                        )
            else:
                # Get all pending alerts (staff only)
                if not is_staff:
                    return Response(
                        {'detail': 'Permission denied. Only staff can view all alerts.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                alerts = get_all_pending_alerts()
            
            serializer = CheckInCheckOutAlertSerializer(alerts, many=True)
            return Response({
                'count': len(alerts),
                'alerts': serializer.data
            })
        except BookingDetail.DoesNotExist:
            return Response(
                {'detail': 'Booking not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'detail': f'Error retrieving alerts: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AcknowledgeAlertApiView(APIView):
    """BR-VH-010: Acknowledge an alert"""
    
    def post(self, request):
        """Mark an alert as acknowledged"""
        from applications.visitor_hostel.services import acknowledge_alert_service
        from applications.visitor_hostel.api.serializers import AcknowledgeAlertSerializer, CheckInCheckOutAlertSerializer
        
        serializer = AcknowledgeAlertSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Security: Only staff can acknowledge alerts
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = 'VhIncharge' in user_roles or 'VhCaretaker' in user_roles or request.user.is_staff
        
        if not is_staff:
            return Response(
                {'detail': 'Permission denied. Only staff can acknowledge alerts.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            alert = acknowledge_alert_service(
                alert_id=serializer.validated_data['alert_id'],
                user=request.user,
                remarks=serializer.validated_data.get('remarks', '')
            )
            
            response_serializer = CheckInCheckOutAlertSerializer(alert)
            return Response({
                'detail': 'Alert acknowledged successfully.',
                'alert': response_serializer.data
            })
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'detail': f'Error acknowledging alert: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ResolveAlertApiView(APIView):
    """BR-VH-010: Resolve an alert"""
    
    def post(self, request):
        """Mark an alert as resolved"""
        from applications.visitor_hostel.services import resolve_alert_service
        from applications.visitor_hostel.api.serializers import ResolveAlertSerializer, CheckInCheckOutAlertSerializer
        
        serializer = ResolveAlertSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Security: Only staff can resolve alerts
        user_roles = request.user.holds_designations.values_list('designation__name', flat=True)
        is_staff = 'VhIncharge' in user_roles or 'VhCaretaker' in user_roles or request.user.is_staff
        
        if not is_staff:
            return Response(
                {'detail': 'Permission denied. Only staff can resolve alerts.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            alert = resolve_alert_service(alert_id=serializer.validated_data['alert_id'])
            
            response_serializer = CheckInCheckOutAlertSerializer(alert)
            return Response({
                'detail': 'Alert resolved successfully.',
                'alert': response_serializer.data
            })
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'detail': f'Error resolving alert: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


