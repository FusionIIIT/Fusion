# Quick fix: ActiveBookingsApiView without meal indicators
# Use this if the meal indicators are causing issues

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
                # UC-VH-006: Include offline booking fields
                'is_offline': booking.is_offline,
                'booking_source': booking.booking_source,
                # UC-VH-010: Meal booking status (fallback values)
                'has_meal_bookings': False,
                'total_meals_booked': 0,
                'meal_booking_count': 0,
            }
            for booking in active_bookings
        ]
        return Response({'results': data})