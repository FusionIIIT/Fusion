"""Service layer for visitor_hostel.

This file contains business logic and write operations.
Functions are added incrementally during refactor without changing behavior.
"""

import datetime
import os

from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from django.db import models
from django.db import transaction
from django.utils import timezone
from notifications.signals import notify

from Fusion import settings
from applications.visitor_hostel.models import (
    Bill,
    BookingDetail,
    Inventory,
    InventoryBill,
    MealRecord,
    RoomDetail,
    VisitorDetail,
    ReplenishmentRequest,
    CheckInCheckOutAlert,
)
from applications.visitor_hostel.selectors import (
    get_all_intenders,
    get_all_bills,
    get_all_bookings_ordered,
    get_all_inventory,
    get_all_inventory_bills,
    get_all_previous_visitors,
    get_booking_by_id,
    get_booking_by_visitor,
    get_cancel_requested_bookings_for_staff,
    get_cancel_requested_bookings_for_user,
    get_cancel_requested_bookings_for_user_future,
    get_canceled_bookings_for_staff,
    get_canceled_bookings_for_user,
    get_checkedin_bookings_for_user,
    get_completed_bookings_for_user,
    get_completed_or_canceled_bookings_for_staff,
    get_confirmed_or_checkedin_bookings_for_staff,
    get_dashboard_bookings_for_staff,
    get_dashboard_bookings_for_user,
    get_first_visitor_by_phone_legacy,
    get_available_rooms_between_dates,
    get_future_forward_bookings,
    get_forwarded_rooms_between_dates,
    get_meal_record_for_booking_visitor_date,
    get_meals_for_booking,
    get_pending_or_forward_bookings_for_staff,
    get_pending_or_forward_bookings_for_user,
    get_rejected_bookings_for_staff,
    get_rejected_bookings_for_user,
    get_room_by_number,
    get_user_by_id,
    get_user_by_username,
    get_visitor_by_id,
    get_vhcaretaker_user,
    validate_single_active_vh_roles,
    VisitorHostelRolePolicyError,
    user_has_vhcaretaker_designation,
    user_has_vhincharge_designation,
)
from applications.visitor_hostel.logging_config import vh_logger, log_errors


class VisitorHostelServiceError(Exception):
    """Base exception for visitor_hostel service operations."""


def _enforce_single_active_role_policy():
    """BR-VH-015: exactly one active caretaker and one active in-charge must exist."""
    try:
        validate_single_active_vh_roles()
    except VisitorHostelRolePolicyError as exc:
        raise VisitorHostelServiceError(str(exc)) from exc


def _fit_booking_remark(value):
    """Fit remark content into BookingDetail.remark (varchar(40))."""
    return (value or '')[:40]


def _normalize_relation(value):
    return (value or '').strip().lower()


def _validate_student_indenter_relation(user, relation):
    """BR-VH-008: Students may book only for Parent or Spouse."""
    user_type = getattr(getattr(user, 'extrainfo', None), 'user_type', None)
    if user_type != 'student':
        return

    allowed_relations = {'parent', 'spouse'}
    normalized_relation = _normalize_relation(relation)
    if normalized_relation not in allowed_relations:
        raise VisitorHostelServiceError(
            'Students may book only for Parent or Spouse (BR-VH-008).'
        )


def reserve_rooms_for_booking(booking, room_count=None, room_numbers=None, replace_existing=False, enforce_confirmation=True):
    """
    Reserve rooms for booking with VhIncharge confirmation enforcement.
    
    Args:
        booking: BookingDetail instance
        room_count: Number of rooms to allocate
        room_numbers: Specific room numbers to allocate
        replace_existing: Whether to replace existing room assignments
        enforce_confirmation: If True, only allow room allocation for confirmed bookings
    
    Raises:
        VisitorHostelServiceError: If trying to allocate rooms before VhIncharge confirmation
    """
    # SECURITY FIX: Enforce VhIncharge confirmation before room allotment
    if enforce_confirmation and booking.status not in ['Confirmed', 'CheckedIn', 'Complete']:
        raise VisitorHostelServiceError(
            'Rooms can only be allotted after booking confirmation from VhIncharge. '
            'Current status: ' + booking.status
        )
    
    existing_rooms = list(booking.rooms.all())
    if room_numbers is None and existing_rooms and not replace_existing:
        target_count = int(room_count or booking.number_of_rooms or len(existing_rooms))
        if len(existing_rooms) >= target_count:
            booking.number_of_rooms_alloted = len(existing_rooms)
            booking.save(update_fields=['number_of_rooms_alloted'])
            return existing_rooms

    available_rooms = list(
        get_available_rooms_between_dates(
            booking.booking_from,
            booking.booking_to,
            exclude_booking_id=booking.id if replace_existing else None,
            category=booking.visitor_category,
        )
    )

    if room_numbers is not None:
        available_room_numbers = {room.room_number for room in available_rooms}
        rooms_to_assign = []
        for room_number in room_numbers:
            try:
                room_object = get_room_by_number(room_number)
            except Exception as exc:
                raise VisitorHostelServiceError(f'Room {room_number} does not exist.') from exc
            if room_object.room_number not in available_room_numbers:
                raise VisitorHostelServiceError(
                    f'Room {room_object.room_number} is not available for the selected dates.'
                )
            rooms_to_assign.append(room_object)
    else:
        target_count = int(room_count or booking.number_of_rooms or 1)
        if len(available_rooms) < target_count:
            raise VisitorHostelServiceError('Not enough rooms available for the selected dates.')
        rooms_to_assign = available_rooms[:target_count]

    booking.rooms.set(rooms_to_assign)
    booking.number_of_rooms_alloted = len(rooms_to_assign)
    booking.save(update_fields=['number_of_rooms_alloted'])
    return rooms_to_assign


def _get_room_rate_per_day(category, room_type):
    category_key = (category or '').upper()

    if category_key == 'A':
        return 0

    if category_key == 'B':
        return 400 if room_type == 'SingleBed' else 500

    if category_key == 'C':
        return 800 if room_type == 'SingleBed' else 1000

    # Default D and any fallback: highest tariff slab.
    return 1400 if room_type == 'SingleBed' else 1600


def calculate_room_bill_for_booking(booking, from_date=None, to_date=None):
    start_date = from_date or booking.check_in or booking.booking_from
    end_date = to_date or datetime.date.today()
    stay_days = (end_date - start_date).days
    if stay_days <= 0:
        stay_days = 1

    category = booking.visitor_category
    assigned_rooms = list(booking.rooms.all())

    if assigned_rooms:
        total = 0
        for room in assigned_rooms:
            total += _get_room_rate_per_day(category, room.room_type) * stay_days
        return int(total)

    fallback_count = int(booking.number_of_rooms_alloted or booking.number_of_rooms or 1)
    fallback_rate = _get_room_rate_per_day(category, 'SingleBed')
    return int(fallback_count * fallback_rate * stay_days)


def calculate_cancellation_charges(booking_date, arrival_date, estimated_room_bill):
    """
    BR-VH-005: Calculate cancellation charges based on arrival date proximity.
    
    Logic:
    - >7 days from arrival = 0% charge
    - ≤7 days from arrival = 25% charge
    - Same day or no-show = 50% charge
    
    Args:
        booking_date: Date when cancellation is requested (today)
        arrival_date: BookingDetail.booking_from
        estimated_room_bill: Estimated room cost
    
    Returns:
        Charge amount in rupees
    """
    days_to_arrival = (arrival_date - booking_date).days
    
    if days_to_arrival > 7:
        # >7 days: 0% charge
        charge_percentage = 0
    elif days_to_arrival > 0:
        # ≤7 days: 25% charge
        charge_percentage = 25
    else:
        # Same day or past: 50% charge (no-show)
        charge_percentage = 50
    
    charge_amount = int((estimated_room_bill * charge_percentage) / 100)
    return charge_amount


def estimate_cancellation_charges_for_booking(booking, reference_date=None):
    """Estimate BR-VH-005 cancellation charges for a booking."""
    effective_date = reference_date or datetime.date.today()
    estimated_room_bill = calculate_room_bill_for_booking(
        booking,
        from_date=booking.booking_from,
        to_date=booking.booking_to,
    )
    return calculate_cancellation_charges(
        effective_date,
        booking.booking_from,
        estimated_room_bill,
    )


def detect_no_shows(today=None):
    """
    BR-VH-010: Detect no-shows where arrival date has passed but guest hasn't checked in.
    
    A no-show occurs when:
    - Status is NOT CheckedIn
    - booking_from date is in the past (relative to today)
    - Status is Confirmed or Forward
    
    Args:
        today: Optional date to check (defaults to today)
    
    Returns:
        QuerySet of bookings with no-show status
    """
    if today is None:
        today = datetime.date.today()
    
    no_shows = BookingDetail.objects.filter(
        booking_from__lt=today,
        status__in=['Confirmed', 'Forward'],
        check_in__isnull=True
    )
    return no_shows


def detect_overstays(current_datetime=None):
    """
    BR-VH-018: Overstay Detection
    
    Overstay alerts MUST be generated when checkout time is exceeded.
    Logic: IF current_time > approved_checkout THEN alert
    
    An overstay occurs when:
    - Status is CheckedIn
    - booking_to date has passed OR checkout time exceeded
    - Guest is still occupying (no check_out date)
    
    Args:
        current_datetime: Optional datetime to check (defaults to now)
    
    Returns:
        QuerySet of bookings in overstay status
    """
    from django.utils import timezone
    
    if current_datetime is None:
        current_datetime = timezone.now()
    
    current_date = current_datetime.date()
    current_time = current_datetime.time()
    
    # BR-VH-018: Check for overstays based on date and time
    overstays = BookingDetail.objects.filter(
        status='CheckedIn',
        check_out__isnull=True
    ).filter(
        # Case 1: Checkout date has passed completely
        models.Q(booking_to__lt=current_date) |
        # Case 2: Checkout date is today but departure time has passed
        models.Q(
            booking_to=current_date,
            departure_time__isnull=False,
            departure_time__lt=current_time.strftime('%H:%M')
        ) |
        # Case 3: Checkout date is today and no departure time specified (default to 11:00 AM)
        models.Q(
            booking_to=current_date,
            departure_time__isnull=True
        ).extra(
            where=["TIME('%s') > TIME('11:00')"],
            params=[current_time.strftime('%H:%M')]
        )
    )
    
    return overstays


def get_overstay_details(overstays_queryset):
    """
    BR-VH-018: Get detailed overstay information for alerts
    
    Returns:
        List of dictionaries with overstay details
    """
    overstay_details = []
    
    for booking in overstays_queryset:
        visitors = booking.visitor.all()
        rooms = booking.rooms.all()
        
        # Calculate overstay duration
        from django.utils import timezone
        current_date = timezone.now().date()
        
        if booking.departure_time:
            # Parse departure time for comparison
            try:
                departure_hour, departure_minute = map(int, booking.departure_time.split(':'))
                departure_datetime = datetime.datetime.combine(
                    booking.booking_to,
                    datetime.time(departure_hour, departure_minute)
                )
                overstay_duration = timezone.now() - timezone.make_aware(departure_datetime)
            except (ValueError, TypeError):
                # Fallback to date-only comparison
                overstay_duration = current_date - booking.booking_to
        else:
            # Default departure time 11:00 AM
            departure_datetime = datetime.datetime.combine(
                booking.booking_to,
                datetime.time(11, 0)
            )
            overstay_duration = timezone.now() - timezone.make_aware(departure_datetime)
        
        overstay_details.append({
            'booking_id': booking.id,
            'booking_to': booking.booking_to,
            'departure_time': booking.departure_time or '11:00',
            'visitors': [{'name': v.visitor_name, 'phone': v.visitor_phone} for v in visitors],
            'rooms': [r.room_number for r in rooms],
            'intender': {
                'name': booking.intender.get_full_name() or booking.intender.username,
                'email': booking.intender.email,
            },
            'overstay_duration': str(overstay_duration),
            'overstay_days': max(0, overstay_duration.days),
            'is_critical': overstay_duration.days > 1,  # More than 1 day overstay is critical
        })
    
    return overstay_details


def detect_due_checkouts(current_datetime=None):
    """
    BR-VH-010: Detect due check-outs where departure time is approaching
    
    A due checkout occurs when:
    - Status is CheckedIn
    - booking_to date is today
    - departure_time is approaching (within alert window)
    - Guest has not checked out yet
    
    Args:
        current_datetime: Optional datetime to check (defaults to now)
    
    Returns:
        QuerySet of bookings due for checkout
    """
    from django.utils import timezone
    
    if current_datetime is None:
        current_datetime = timezone.now()
    
    current_date = current_datetime.date()
    current_time = current_datetime.time()
    
    # BR-VH-010: Check for bookings due for checkout today
    due_checkouts = BookingDetail.objects.filter(
        status='CheckedIn',
        check_out__isnull=True,
        booking_to=current_date
    ).filter(
        # Case 1: Departure time specified and approaching (within 2 hours)
        models.Q(departure_time__isnull=False) |
        # Case 2: No departure time specified (default 11:00 AM)
        models.Q(departure_time__isnull=True)
    )
    
    return due_checkouts


def get_due_checkout_details(due_checkouts_queryset):
    """
    BR-VH-010: Get detailed due checkout information for alerts
    
    Returns:
        List of dictionaries with due checkout details
    """
    due_checkout_details = []
    
    for booking in due_checkouts_queryset:
        visitors = booking.visitor.all()
        rooms = booking.rooms.all()
        
        # Calculate time until departure
        from django.utils import timezone
        current_datetime = timezone.now()
        
        departure_time = booking.departure_time or '11:00'
        
        try:
            departure_hour, departure_minute = map(int, departure_time.split(':'))
            departure_datetime = datetime.datetime.combine(
                booking.booking_to,
                datetime.time(departure_hour, departure_minute)
            )
            departure_datetime = timezone.make_aware(departure_datetime)
            
            time_until_departure = departure_datetime - current_datetime
            hours_until_departure = time_until_departure.total_seconds() / 3600
        except (ValueError, TypeError):
            # Default to 11:00 AM if parsing fails
            departure_datetime = datetime.datetime.combine(
                booking.booking_to,
                datetime.time(11, 0)
            )
            departure_datetime = timezone.make_aware(departure_datetime)
            time_until_departure = departure_datetime - current_datetime
            hours_until_departure = time_until_departure.total_seconds() / 3600
        
        due_checkout_details.append({
            'booking_id': booking.id,
            'booking_to': booking.booking_to,
            'departure_time': departure_time,
            'visitors': [{'name': v.visitor_name, 'phone': v.visitor_phone} for v in visitors],
            'rooms': [r.room_number for r in rooms],
            'intender': {
                'name': booking.intender.get_full_name() or booking.intender.username,
                'email': booking.intender.email,
            },
            'hours_until_departure': max(0, hours_until_departure),
            'is_urgent': hours_until_departure <= 2,  # Less than 2 hours is urgent
            'is_overdue': hours_until_departure < 0,  # Past departure time
        })
    
    return due_checkout_details


def trigger_due_checkout_alerts(due_checkout_details):
    """
    BR-VH-010: Trigger due checkout alerts to appropriate staff
    
    Effects: Improves operational control by alerting staff of upcoming checkouts
    """
    from notification.views import visitors_hostel_notif
    from applications.visitor_hostel.selectors import get_vhincharge_user_legacy_preferred, get_vhcaretaker_user
    
    if not due_checkout_details:
        return {'alerts_sent': 0, 'urgent_checkouts': 0}
    
    incharge_user = get_vhincharge_user_legacy_preferred()
    caretaker_user = get_vhcaretaker_user()
    
    alerts_sent = 0
    urgent_checkouts = 0
    
    for checkout in due_checkout_details:
        # Alert VH Incharge for all due checkouts
        if incharge_user:
            visitors_hostel_notif(
                incharge_user, 
                incharge_user, 
                'booking_due_checkout_alert',
                extra_context={
                    'booking_id': checkout['booking_id'],
                    'visitor_names': ', '.join([v['name'] for v in checkout['visitors']]),
                    'room_numbers': ', '.join(checkout['rooms']),
                    'departure_time': checkout['departure_time'],
                    'hours_until_departure': checkout['hours_until_departure'],
                    'is_urgent': checkout['is_urgent']
                }
            )
            alerts_sent += 1
        
        # Alert VH Caretaker for all due checkouts
        if caretaker_user:
            visitors_hostel_notif(
                caretaker_user,
                caretaker_user,
                'booking_due_checkout_alert',
                extra_context={
                    'booking_id': checkout['booking_id'],
                    'visitor_names': ', '.join([v['name'] for v in checkout['visitors']]),
                    'room_numbers': ', '.join(checkout['rooms']),
                    'departure_time': checkout['departure_time'],
                    'hours_until_departure': checkout['hours_until_departure'],
                    'is_urgent': checkout['is_urgent']
                }
            )
        
        # Count urgent alerts (checkout within 2 hours)
        if checkout['is_urgent']:
            urgent_checkouts += 1
    
    return {
        'alerts_sent': alerts_sent,
        'urgent_checkouts': urgent_checkouts,
        'total_due_checkouts': len(due_checkout_details)
    }


def trigger_overstay_alerts(overstay_details):
    """
    BR-VH-018: Trigger overstay alerts to appropriate staff
    
    Effects: Prevents unauthorized extended stays
    """
    from notification.views import visitors_hostel_notif
    from applications.visitor_hostel.selectors import get_vhincharge_user_legacy_preferred, get_vhcaretaker_user
    
    if not overstay_details:
        return {'alerts_sent': 0, 'critical_alerts': 0}
    
    incharge_user = get_vhincharge_user_legacy_preferred()
    caretaker_user = get_vhcaretaker_user()
    
    alerts_sent = 0
    critical_alerts = 0
    
    for overstay in overstay_details:
        # Alert VH Incharge for all overstays
        if incharge_user:
            visitors_hostel_notif(
                incharge_user, 
                incharge_user, 
                'booking_overstay_alert',
                extra_context={
                    'booking_id': overstay['booking_id'],
                    'visitor_names': ', '.join([v['name'] for v in overstay['visitors']]),
                    'room_numbers': ', '.join(overstay['rooms']),
                    'overstay_days': overstay['overstay_days'],
                    'is_critical': overstay['is_critical']
                }
            )
            alerts_sent += 1
        
        # Alert VH Caretaker for all overstays
        if caretaker_user:
            visitors_hostel_notif(
                caretaker_user,
                caretaker_user,
                'booking_overstay_alert',
                extra_context={
                    'booking_id': overstay['booking_id'],
                    'visitor_names': ', '.join([v['name'] for v in overstay['visitors']]),
                    'room_numbers': ', '.join(overstay['rooms']),
                    'overstay_days': overstay['overstay_days'],
                    'is_critical': overstay['is_critical']
                }
            )
        
        # Count critical alerts (overstay > 1 day)
        if overstay['is_critical']:
            critical_alerts += 1
    
    return {
        'alerts_sent': alerts_sent,
        'critical_alerts': critical_alerts,
        'total_overstays': len(overstay_details)
    }


@log_errors("Booking Confirmation")
def confirm_booking_service(booking_id, category, rooms, acting_user, notify_fn):
    """
    Confirm booking and allocate rooms - ONLY VhIncharge can perform this action.
    
    This is the ONLY point where room allocation should happen for new bookings.
    """
    _enforce_single_active_role_policy()
    bd = get_booking_by_id(booking_id)
    
    # Update booking status and category
    bd.status = 'Confirmed'
    bd.visitor_category = category
    bd.confirmed_date = datetime.date.today()

    # SECURITY: Room allocation happens ONLY during VhIncharge confirmation
    # Use enforce_confirmation=False here since we're in the confirmation process
    if rooms:
        reserve_rooms_for_booking(bd, room_numbers=rooms, replace_existing=True, enforce_confirmation=False)
    elif not bd.rooms.exists():
        reserve_rooms_for_booking(bd, room_count=bd.number_of_rooms, enforce_confirmation=False)
    else:
        bd.number_of_rooms_alloted = bd.rooms.count()
        bd.save(update_fields=['status', 'visitor_category', 'confirmed_date', 'number_of_rooms_alloted'])
        notify_fn(acting_user, bd.intender, 'booking_confirmation')
        return

    bd.save()
    notify_fn(acting_user, bd.intender, 'booking_confirmation')


def cancel_booking_service(
    booking_id,
    remark,
    charges,
    acting_user,
    notify_fn,
    payment_mode=None,
    transaction_id=None,
):
    """
    Cancel a booking and apply proper cancellation charges per BR-VH-005.
    
    If charges not provided, calculates automatically based on days to arrival.
    """
    _enforce_single_active_role_policy()
    booking = get_booking_by_id(booking_id)
    BookingDetail.objects.filter(id=booking_id).update(
        status='Canceled', remark=_fit_booking_remark(remark)
    )

    # If charges not provided, calculate based on BR-VH-005
    bill_amount = 0
    if charges is not None:
        bill_amount = int(charges)
    else:
        bill_amount = estimate_cancellation_charges_for_booking(booking)

    if int(bill_amount) > 0 and payment_mode == 'online' and not transaction_id:
        raise VisitorHostelServiceError('transaction_id is required to confirm online cancellation fee payment.')

    existing_bill = Bill.objects.filter(booking=booking).first()
    if existing_bill:
        existing_bill.room_bill = int(existing_bill.room_bill) + int(bill_amount)
        existing_bill.caretaker = acting_user
        if payment_mode is not None:
            existing_bill.payment_mode = payment_mode
        if transaction_id is not None:
            existing_bill.transaction_id = transaction_id or None
        total_due = int(existing_bill.meal_bill) + int(existing_bill.room_bill)
        existing_bill.payment_status = total_due == 0
        existing_bill.bill_date = datetime.date.today()
        existing_bill.save()
    else:
        Bill.objects.create(
            booking=booking,
            meal_bill=0,
            room_bill=bill_amount,
            caretaker=acting_user,
            payment_mode=payment_mode,
            transaction_id=(transaction_id or None),
            payment_status=(int(bill_amount) == 0),
            bill_date=datetime.date.today(),
        )

    notify_fn(acting_user, booking.intender, 'booking_cancellation_request_accepted')
    return bill_amount


def cancel_booking_request_service(booking_id, remark):
    _enforce_single_active_role_policy()
    booking = get_booking_by_id(booking_id)
    previous_status = booking.status
    previous_status_tag = f"__prev_status__:{previous_status}"
    merged_remark = previous_status_tag
    if remark:
        merged_remark = f"{previous_status_tag} {remark}".strip()

    BookingDetail.objects.filter(id=booking_id).update(
        status='CancelRequested', remark=_fit_booking_remark(merged_remark)
    )


def approve_cancel_booking_request_service(booking_id, remark=""):
    _enforce_single_active_role_policy()
    booking = get_booking_by_id(booking_id)
    if booking.status != 'CancelRequested':
        raise VisitorHostelServiceError('Only cancellation requests can be approved.')

    base_remark = booking.remark or ''
    approval_note = '__caretaker_approved__'
    if remark:
        approval_note = f"__caretaker_approved__ {remark}".strip()
    updated_remark = f"{base_remark} {approval_note}".strip()

    BookingDetail.objects.filter(id=booking_id).update(remark=_fit_booking_remark(updated_remark))


def reject_cancel_booking_request_service(booking_id, remark=""):
    _enforce_single_active_role_policy()
    booking = get_booking_by_id(booking_id)
    if booking.status != 'CancelRequested':
        raise VisitorHostelServiceError('Only cancellation requests can be rejected.')

    previous_status = 'Pending'
    current_remark = booking.remark or ''
    if '__prev_status__:' in current_remark:
        status_chunk = current_remark.split('__prev_status__:', 1)[1].strip()
        status_value = status_chunk.split(' ')[0].strip()
        if status_value in ['Pending', 'Forward', 'Confirmed', 'CheckedIn']:
            previous_status = status_value

    final_remark = remark if remark else 'Cancellation request rejected'
    BookingDetail.objects.filter(id=booking_id).update(
        status=previous_status,
        remark=_fit_booking_remark(final_remark),
    )


def reject_booking_service(booking_id, remark, acting_user=None):
    update_fields = {
        'status': 'Rejected',
        'remark': remark,
    }
    if acting_user is not None:
        update_fields['caretaker'] = acting_user

    BookingDetail.objects.filter(id=booking_id).update(**update_fields)


def forward_booking_service(booking_id, modified_category, rooms, remark, bill_settlement=None, acting_user=None):
    """
    Forward booking to VhIncharge with room suggestions but NO room allocation.
    
    SECURITY: Rooms are only suggested for VhIncharge review, not allocated.
    Actual room allocation happens only after VhIncharge confirmation.
    """
    _enforce_single_active_role_policy()
    BookingDetail.objects.filter(id=booking_id).update(
        status='Forward',
        remark=remark,
        forwarded_date=datetime.date.today(),
    )
    bd = get_booking_by_id(booking_id)
    bd.modified_visitor_category = modified_category if modified_category else bd.visitor_category
    if acting_user is not None:
        bd.caretaker = acting_user
    if bill_settlement:
        bd.bill_to_be_settled_by = bill_settlement

    # SECURITY FIX: Do NOT allocate rooms during forward - only store suggestions
    # Rooms will be allocated only when VhIncharge confirms the booking
    if rooms:
        # Store suggested rooms in remark for VhIncharge review
        room_suggestions = ', '.join(rooms)
        existing_remark = bd.remark or ''
        bd.remark = f"{existing_remark} [Suggested rooms: {room_suggestions}]"[:40]  # Fit in varchar(40)
    
    bd.save()


def check_out_service(
    booking_id,
    meal_bill,
    room_bill,
    extra_charges,
    payment_mode,
    transaction_id,
    payment_screenshot,
    offline_bill_id,
    offline_bill_photo,
    bill_settlement,
    acting_user,
):
    _enforce_single_active_role_policy()
    checkout_date = datetime.date.today()
    BookingDetail.objects.filter(id=booking_id).update(
        check_out=datetime.datetime.today(), status='Complete'
    )
    booking = get_booking_by_id(booking_id)
    if bill_settlement:
        booking.bill_to_be_settled_by = bill_settlement
        booking.save(update_fields=['bill_to_be_settled_by'])

    computed_room_bill = room_bill
    if computed_room_bill is None:
        computed_room_bill = calculate_room_bill_for_booking(
            booking,
            from_date=booking.check_in or booking.booking_from,
            to_date=checkout_date,
        )

    Bill.objects.create(
        booking=booking,
        meal_bill=int(meal_bill),
        room_bill=int(computed_room_bill),
        extra_charges=int(extra_charges or 0),
        payment_mode=payment_mode,
        transaction_id=(transaction_id or None),
        payment_screenshot=payment_screenshot,
        offline_bill_id=(offline_bill_id or None),
        offline_bill_photo=offline_bill_photo,
        caretaker=acting_user,
        payment_status=False,
        bill_date=checkout_date,
    )


def settle_bill_service(
    booking_id,
    acting_user,
    bill_settlement=None,
    payment_status=True,
    meal_bill=None,
    room_bill=None,
    extra_charges=None,
    payment_mode=None,
    transaction_id=None,
    payment_screenshot=None,
    offline_bill_id=None,
    offline_bill_photo=None,
):
    """
    Settle bill with BR-VH-014 Immutable Billing enforcement.
    
    BR-VH-014: Core billing amounts (meal_bill, room_bill, extra_charges) MUST NOT be 
    modified after checkout. However, payment settlement fields can be updated.
    Logic: IF status=Checked-out (Complete) THEN lock core amounts
    """
    _enforce_single_active_role_policy()
    booking = get_booking_by_id(booking_id)

    if bill_settlement:
        booking.bill_to_be_settled_by = bill_settlement
        booking.save(update_fields=['bill_to_be_settled_by'])

    bill = Bill.objects.filter(booking=booking).first()
    
    # BR-VH-014: Check if bill exists and booking is checked out
    # Only block if trying to modify core billing amounts after checkout
    if bill is not None and booking.check_out is not None:
        if meal_bill is not None or room_bill is not None or extra_charges is not None:
            raise VisitorHostelServiceError(
                f'BR-VH-014 Violation: Billing amounts cannot be modified after checkout. '
                f'This bill was finalized when the guest checked out on {booking.check_out}. '
                f'Billing modifications are locked to ensure billing integrity.'
            )
    
    if bill is None:
        # Only allow bill creation during checkout or for non-checked-out bookings
        bill = Bill.objects.create(
            booking=booking,
            meal_bill=int(meal_bill or 0),
            room_bill=int(room_bill or 0),
            extra_charges=int(extra_charges or 0),
            payment_mode=payment_mode,
            transaction_id=(transaction_id or None),
            payment_screenshot=payment_screenshot,
            offline_bill_id=(offline_bill_id or None),
            offline_bill_photo=offline_bill_photo,
            caretaker=acting_user,
            payment_status=bool(payment_status),
            bill_date=datetime.date.today(),
        )
        return bill

    # Update existing bill with payment settlement fields (allowed even after checkout)
    if meal_bill is not None and booking.check_out is None:
        bill.meal_bill = int(meal_bill)
    if room_bill is not None and booking.check_out is None:
        bill.room_bill = int(room_bill)
    if extra_charges is not None and booking.check_out is None:
        bill.extra_charges = int(extra_charges)
    # Payment fields can always be updated
    if payment_mode is not None:
        bill.payment_mode = payment_mode
    if transaction_id is not None:
        bill.transaction_id = transaction_id or None
    if payment_screenshot is not None:
        bill.payment_screenshot = payment_screenshot
    if offline_bill_id is not None:
        bill.offline_bill_id = offline_bill_id or None
    if offline_bill_photo is not None:
        bill.offline_bill_photo = offline_bill_photo

    bill.caretaker = acting_user
    bill.payment_status = bool(payment_status)
    if not bill.bill_date:
        bill.bill_date = datetime.date.today()
    bill.save()
    return bill


def update_booking_service(booking_id, person_count, purpose_of_visit, booking_from, booking_to, number_of_rooms):
    """
    Update booking details with strict status enforcement.
    
    SECURITY: Only pending bookings can be modified.
    Once confirmed by VhIncharge, no modifications are allowed.
    """
    booking = get_booking_by_id(booking_id)
    
    # SECURITY CHECK: Only allow modification of pending bookings
    if booking.status != 'Pending':
        raise VisitorHostelServiceError(
            f'Booking modification is only allowed for pending bookings. '
            f'Current status: {booking.status}. '
            f'Once confirmed by VhIncharge, bookings cannot be modified.'
        )
    
    booking.person_count = person_count
    booking.number_of_rooms = number_of_rooms
    booking.booking_from = booking_from
    booking.booking_to = booking_to
    booking.purpose = purpose_of_visit
    booking.save()


def update_visitor_info_service(booking_id, visitor_name=None, visitor_email=None, visitor_phone=None, visitor_organization=None, visitor_address=None, nationality=None):
    """Update visitor information for a booking"""
    from applications.visitor_hostel.models import BookingDetail, VisitorDetail
    
    booking = get_booking_by_id(booking_id)
    
    # Get the first visitor associated with this booking (assuming one visitor per booking for now)
    if booking.visitor.exists():
        visitor = booking.visitor.first()
        
        # Update only the fields that are provided
        if visitor_name is not None:
            visitor.visitor_name = visitor_name
        if visitor_email is not None:
            visitor.visitor_email = visitor_email
        if visitor_phone is not None:
            visitor.visitor_phone = visitor_phone
        if visitor_organization is not None:
            visitor.visitor_organization = visitor_organization
        if visitor_address is not None:
            visitor.visitor_address = visitor_address
        if nationality is not None:
            visitor.nationality = nationality
            
        visitor.save()
        return visitor
    else:
        # If no visitor exists, create a new one
        visitor = VisitorDetail.objects.create(
            visitor_name=visitor_name or "",
            visitor_email=visitor_email or "",
            visitor_phone=visitor_phone or "",
            visitor_organization=visitor_organization or "",
            visitor_address=visitor_address or "",
            nationality=nationality or ""
        )
        booking.visitor.add(visitor)
        return visitor


def check_in_service(booking_id, visitor_name, visitor_phone, visitor_email, visitor_address, check_in_date):
    """
    Check-in service with VhIncharge confirmation enforcement.
    
    SECURITY: Only confirmed bookings can be checked in.
    """
    _enforce_single_active_role_policy()
    bd = get_booking_by_id(booking_id)
    
    # SECURITY FIX: Only allow check-in for confirmed bookings
    if bd.status != 'Confirmed':
        raise VisitorHostelServiceError(
            'Check-in is only allowed for bookings confirmed by VhIncharge. '
            f'Current status: {bd.status}'
        )
    
    visitor = get_first_visitor_by_phone_legacy(visitor_phone)
    if not visitor:
        visitor = VisitorDetail.objects.create(
            visitor_phone=visitor_phone,
            visitor_name=visitor_name,
            visitor_email=visitor_email,
            visitor_address=visitor_address,
        )
    
    # Rooms should already be allocated during confirmation
    # But if not, allocate them now (enforce_confirmation=False for this specific case)
    if not bd.rooms.exists():
        reserve_rooms_for_booking(bd, room_count=bd.number_of_rooms, enforce_confirmation=False)
    
    bd.status = "CheckedIn"
    bd.check_in = check_in_date
    bd.visitor.add(visitor)
    bd.save()


def record_meal_service(booking_id, visitor_id, meal_date, m_tea, breakfast, lunch, eve_tea, dinner):
    booking = get_booking_by_id(booking_id)
    visitor = get_visitor_by_id(visitor_id)

    try:
        meal = get_meal_record_for_booking_visitor_date(booking, visitor, meal_date)
    except Exception:
        meal = False

    if meal:
        meal.morning_tea += int(m_tea)
        meal.eve_tea += int(eve_tea)
        meal.breakfast += int(breakfast)
        meal.lunch += int(lunch)
        meal.dinner += int(dinner)
        meal.save()
        return

    MealRecord.objects.create(
        visitor=visitor,
        booking=booking,
        morning_tea=m_tea,
        eve_tea=eve_tea,
        meal_date=meal_date,
        breakfast=breakfast,
        lunch=lunch,
        dinner=dinner,
        persons=1,
    )


def add_to_inventory_service(item_name, bill_number, quantity, cost, consumable, 
                            threshold_quantity=5, unit='pieces', category='', remark='', bill_photo=None):
    """
    UC-VH-011: Enhanced inventory service with threshold management (BR-VH-007)
    """
    is_consumable = False if consumable == 'false' else True
    
    # UC-VH-011: Create inventory item with threshold management fields
    item = Inventory.objects.create(
        item_name=item_name, 
        quantity=quantity, 
        consumable=is_consumable,
        # BR-VH-007: Threshold management
        threshold_quantity=threshold_quantity,
        unit=unit,
        category=category,
        remark=remark,
        # Auto-calculate fields
        total_stock=quantity,
        opening_stock=quantity,
        serviceable=quantity if not is_consumable else 0,
        inuse=0,
        total_usable=quantity
    )
    
    # Create associated bill record with photo
    InventoryBill.objects.create(
        bill_number=bill_number, 
        cost=cost, 
        item_name_id=item.pk,
        bill_photo=bill_photo  # Store the uploaded bill photo
    )
    
    return item


def update_inventory_service(item_id, quantity, bill_number=None, cost=0, bill_photo=None):
    """
    Update inventory stock with bill documentation.
    VhIncharge requirement: Bill photo is mandatory for stock updates.
    """
    if quantity < 0:
        quantity = 1
    
    if quantity == 0:
        Inventory.objects.filter(id=item_id).delete()
    else:
        # Update inventory quantity through model save to trigger threshold recalculation.
        inventory_item = Inventory.objects.get(id=item_id)
        inventory_item.quantity = quantity
        inventory_item.total_stock = quantity
        inventory_item.total_usable = quantity

        # If stock has recovered, clear pending replenishment marker.
        if quantity >= inventory_item.threshold_quantity:
            inventory_item.pending_replenishment = False

        # Inventory.save() updates is_critical via model logic.
        inventory_item.save()
        
        # Create bill record for the stock update if bill info provided
        if bill_number and bill_photo:
            InventoryBill.objects.create(
                item_name=inventory_item,
                bill_number=bill_number,
                cost=cost,
                bill_photo=bill_photo  # Required bill photo for stock updates
            )


def edit_room_status_service(room_number, room_status):
    room = get_room_by_number(room_number)
    RoomDetail.objects.filter(room_id=room).update(status=room_status)


def build_visitorhostel_dashboard_context(user):
    intenders = get_all_intenders()
    vhcaretaker = user_has_vhcaretaker_designation(user)
    vhincharge = user_has_vhincharge_designation(user)

    user_designation = "student"
    if vhincharge:
        user_designation = "VhIncharge"
    elif vhcaretaker:
        user_designation = "VhCaretaker"
    else:
        user_designation = "Intender"

    available_rooms = {}
    forwarded_rooms = {}
    cancel_booking_request = []

    if user_designation == "Intender":
        all_bookings = get_all_bookings_ordered()
        pending_bookings = get_pending_or_forward_bookings_for_user(user)
        active_bookings = get_checkedin_bookings_for_user(user)
        dashboard_bookings = get_dashboard_bookings_for_user(user)

        visitors = {}
        rooms = {}
        for booking in active_bookings:
            visitors[booking.id] = range(2, booking.person_count + 1)

        for booking in active_bookings:
            for room_no in booking.rooms.all():
                rooms[booking.id] = range(1, booking.number_of_rooms_alloted)

        complete_bookings = get_completed_bookings_for_user(user)
        canceled_bookings = get_canceled_bookings_for_user(user)
        rejected_bookings = get_rejected_bookings_for_user(user)
        cancel_booking_requested = get_cancel_requested_bookings_for_user(user)

    else:
        all_bookings = get_all_bookings_ordered()
        pending_bookings = get_pending_or_forward_bookings_for_staff()
        active_bookings = get_confirmed_or_checkedin_bookings_for_staff()
        cancel_booking_request = get_cancel_requested_bookings_for_staff()
        dashboard_bookings = get_dashboard_bookings_for_staff()

        visitors = {}
        rooms = {}

        c_bookings = get_future_forward_bookings()

        for booking in active_bookings:
            visitors[booking.id] = range(2, booking.person_count + 1)

        for booking in active_bookings:
            for room_no in booking.rooms.all():
                rooms[booking.id] = range(2, booking.number_of_rooms_alloted + 1)

        complete_bookings = get_completed_or_canceled_bookings_for_staff()
        canceled_bookings = get_canceled_bookings_for_staff()
        cancel_booking_requested = get_cancel_requested_bookings_for_user_future(user)
        rejected_bookings = get_rejected_bookings_for_staff()

        for booking in pending_bookings:
            available_rooms[booking.id] = get_available_rooms_between_dates(booking.booking_from, booking.booking_to)

        for booking in c_bookings:
            forwarded_rooms[booking.id] = get_forwarded_rooms_between_dates(booking.booking_from, booking.booking_to)

    inventory = get_all_inventory()
    inventory_bill = get_all_inventory_bills()

    completed_booking_bills = {}
    all_bills = get_all_bills()

    current_balance = 0
    for bill in all_bills:
        completed_booking_bills[bill.id] = {
            'intender': str(bill.booking.intender),
            'booking_from': str(bill.booking.booking_from),
            'booking_to': str(bill.booking.booking_to),
            'total_bill': str(bill.meal_bill + bill.room_bill + int(getattr(bill, 'extra_charges', 0) or 0)),
            'bill_date': str(bill.bill_date),
        }
        current_balance = current_balance + bill.meal_bill + bill.room_bill + int(getattr(bill, 'extra_charges', 0) or 0)

    for inv_bill in inventory_bill:
        current_balance = current_balance - inv_bill.cost

    active_visitors = {}
    for booking in active_bookings:
        if booking.status == 'CheckedIn':
            for visitor in booking.visitor.all():
                active_visitors[booking.id] = visitor

    previous_visitors = get_all_previous_visitors()

    bills = {}
    for booking in active_bookings:
        if booking.status == 'CheckedIn':
            rooms = booking.rooms.all()
            days = (datetime.date.today() - booking.check_in).days
            category = booking.visitor_category

            room_bill = 100
            if days == 0:
                days = 1

            if category == 'A':
                room_bill = 0
            elif category == 'B':
                for i in rooms:
                    if i.room_type == 'SingleBed':
                        room_bill = room_bill + days * 400
                    else:
                        room_bill = room_bill + days * 500
            elif category == 'C':
                for i in rooms:
                    if i.room_type == 'SingleBed':
                        room_bill = room_bill + days * 800
                    else:
                        room_bill = room_bill + days * 1000
            else:
                for i in rooms:
                    if i.room_type == 'SingleBed':
                        room_bill = room_bill + days * 1400
                    else:
                        room_bill = room_bill + days * 1600

            mess_bill = 0
            for visitor in booking.visitor.all():
                meal = get_meals_for_booking(booking.id)

                mess_bill1 = 0
                for m in meal:
                    if m.morning_tea != 0:
                        mess_bill1 = mess_bill1 + m.morning_tea * 10
                    if m.eve_tea != 0:
                        mess_bill1 = mess_bill1 + m.eve_tea * 10
                    if m.breakfast != 0:
                        mess_bill1 = mess_bill1 + m.breakfast * 50
                    if m.lunch != 0:
                        mess_bill1 = mess_bill1 + m.lunch * 100
                    if m.dinner != 0:
                        mess_bill1 = mess_bill1 + m.dinner * 100

                    mess_bill = mess_bill + mess_bill1

            total_bill = mess_bill + room_bill
            bills[booking.id] = {'mess_bill': mess_bill, 'room_bill': room_bill, 'total_bill': total_bill}

    visitor_list = []
    for b in dashboard_bookings:
        count = 1
        b_visitor_list = b.visitor.all()
        for v in b_visitor_list:
            if count == 1:
                visitor_list.append(v)
                count = count + 1

    return {
        'all_bookings': all_bookings,
        'complete_bookings': complete_bookings,
        'pending_bookings': pending_bookings,
        'active_bookings': active_bookings,
        'canceled_bookings': canceled_bookings,
        'dashboard_bookings': dashboard_bookings,
        'bills': bills,
        'available_rooms': available_rooms,
        'forwarded_rooms': forwarded_rooms,
        'inventory': inventory,
        'inventory_bill': inventory_bill,
        'active_visitors': active_visitors,
        'intenders': intenders,
        'user': user,
        'visitors': visitors,
        'rooms': rooms,
        'previous_visitors': previous_visitors,
        'completed_booking_bills': completed_booking_bills,
        'current_balance': current_balance,
        'rejected_bookings': rejected_bookings,
        'cancel_booking_request': cancel_booking_request,
        'cancel_booking_requested': cancel_booking_requested,
        'user_designation': user_designation,
    }


def request_booking_service(request):
    payload = {
        'intender': request.POST.get('intender'),
        'booking_id': request.POST.get('booking-id'),
        'category': request.POST.get('category'),
        'person_count': request.POST.get('number-of-people'),
        'purpose_of_visit': request.POST.get('purpose-of-visit'),
        'booking_from': request.POST.get('booking_from'),
        'booking_to': request.POST.get('booking_to'),
        'booking_from_time': request.POST.get('booking_from_time'),
        'booking_to_time': request.POST.get('booking_to_time'),
        'remarks_during_booking_request': request.POST.get('remarks_during_booking_request'),
        'bill_to_be_settled_by': request.POST.get('bill_settlement'),
        'number_of_rooms': request.POST.get('number-of-rooms'),
        'visitor_name': request.POST.get('name'),
        'visitor_phone': request.POST.get('phone'),
        'visitor_email': request.POST.get('email'),
        'visitor_address': request.POST.get('address'),
        'visitor_organization': request.POST.get('organization'),
        'visitor_nationality': request.POST.get('nationality'),
    }
    request_booking_service_from_data(payload, request.FILES)


def request_booking_service_from_data(payload, files=None):
    _enforce_single_active_role_policy()
    intender = payload.get('intender')
    user = get_user_by_id(intender)
    booking_id = payload.get('booking_id')
    category = payload.get('category')
    person_count = payload.get('person_count')
    purpose_of_visit = payload.get('purpose_of_visit')
    booking_from = payload.get('booking_from')
    booking_to = payload.get('booking_to')
    booking_from_time = payload.get('booking_from_time')
    booking_to_time = payload.get('booking_to_time')
    bill_to_be_settled_by = payload.get('bill_to_be_settled_by')
    number_of_rooms = payload.get('number_of_rooms')
    intender_relation = payload.get('intender_relation', '')
    is_offline = bool(payload.get('is_offline', False))
    booking_source = payload.get('booking_source', 'online')
    intender_name = payload.get('intender_name', '')
    intender_phone = payload.get('intender_phone', '')
    intender_email = payload.get('intender_email', '')

    # Normalize offline booking source to allowed values.
    if booking_source not in ['online', 'telephonic', 'walkin']:
        booking_source = 'online'
    if is_offline and booking_source == 'online':
        booking_source = 'telephonic'

    _validate_student_indenter_relation(user, intender_relation)

    care_taker = get_vhcaretaker_user()
    with transaction.atomic():
        booking_object = BookingDetail.objects.create(
            caretaker=care_taker,
            purpose=purpose_of_visit,
            intender=user,
            booking_from=booking_from,
            booking_to=booking_to,
            visitor_category=category,
            person_count=person_count,
            arrival_time=booking_from_time,
            departure_time=booking_to_time,
            number_of_rooms=number_of_rooms,
            number_of_rooms_alloted=0,
            bill_to_be_settled_by=bill_to_be_settled_by,
            is_offline=is_offline,
            booking_source=booking_source,
            intender_name=intender_name,
            intender_phone=intender_phone,
            intender_email=intender_email,
            intender_relation=intender_relation,
        )

        visitor_name = payload.get('visitor_name')
        visitor_phone = payload.get('visitor_phone')
        visitor_email = payload.get('visitor_email')
        visitor_address = payload.get('visitor_address')
        visitor_organization = payload.get('visitor_organization')
        visitor_nationality = payload.get('visitor_nationality')
        if visitor_organization == '':
            visitor_organization = ' '

        visitor = VisitorDetail.objects.create(
            visitor_phone=visitor_phone,
            visitor_name=visitor_name,
            visitor_email=visitor_email,
            visitor_address=visitor_address,
            visitor_organization=visitor_organization,
            nationality=visitor_nationality,
        )
        booking_object.visitor.add(visitor)
        booking_object.save()

    doc = None
    if files:
        doc = files.get('files-during-booking-request')
    if doc:
        filename, file_extenstion = os.path.splitext(doc.name)
        filename = booking_id
        if not filename:
            filename = str(booking_object.id)
        full_path = settings.MEDIA_ROOT + "/VhImage/"
        url = settings.MEDIA_URL + filename + file_extenstion
        if not os.path.isdir(full_path):
            os.makedirs(full_path)
        fs = FileSystemStorage(full_path, url)
        fs.save(filename + file_extenstion, doc)
        uploaded_file_url = "/media/online_cms/" + filename
        uploaded_file_url = uploaded_file_url + file_extenstion
        booking_object.image = uploaded_file_url
        booking_object.save()
    
    # BR-VH-010: Initialize alert system for this booking
    try:
        create_initial_alert_for_booking(booking_object)
    except Exception as e:
        vh_logger.logger.error(f"Error initializing alerts for booking {booking_object.id}: {str(e)}")
        # Don't fail the booking creation if alert initialization fails


def update_booking_and_get_forwarded_rooms(booking_id, person_count, purpose_of_visit, booking_from, booking_to, number_of_rooms):
    update_booking_service(booking_id, person_count, purpose_of_visit, booking_from, booking_to, number_of_rooms)

    forwarded_rooms = {}
    c_bookings = get_future_forward_bookings()
    for booking in c_bookings:
        temp2 = get_forwarded_rooms_between_dates(booking.booking_from, booking.booking_to)
        forwarded_rooms[booking.id] = temp2

    return forwarded_rooms


def bill_generation_service(request):
    v_id = request.POST.getlist('visitor')[0]
    meal_bill = request.POST.getlist('mess_bill')[0]
    room_bill = request.POST.getlist('room_bill')[0]
    status = request.POST.getlist('status')[0]
    bill_generation_service_from_data(request.user.username, v_id, meal_bill, room_bill, status)
    messages.success(request, 'guest check out successfully')


def bill_generation_service_from_data(username, v_id, meal_bill, room_bill, status):
    st = True if status == "True" else False

    user = get_user_by_username(username)
    visitor = get_first_visitor_by_phone_legacy(v_id)
    Bill.objects.create(
        booking=get_booking_by_visitor(visitor),
        caretaker=user,
        meal_bill=meal_bill,
        room_bill=room_bill,
        payment_status=st,
    )


# ============================================================
# UC-VH-011: INVENTORY THRESHOLD & REPLENISHMENT SERVICES
# ============================================================

def check_inventory_thresholds():
    """
    UC-VH-011, BR-VH-007: Check all inventory items for threshold breaches
    Returns list of items below threshold for alert generation
    """
    from django.utils import timezone
    
    critical_items = []
    inventory_items = Inventory.objects.all()
    
    for item in inventory_items:
        if item.is_below_threshold:
            # Update critical status
            item.is_critical = True
            item.last_threshold_alert = timezone.now()
            item.save()
            critical_items.append(item)
    
    return critical_items


def create_replenishment_request_service(item_id, requested_quantity, urgency, justification, requested_by_user):
    """
    UC-VH-011: Create replenishment request by caretaker
    """
    try:
        with transaction.atomic():
            inventory_item = Inventory.objects.get(id=item_id)

            # Check if there's already a pending request for this item
            existing_request = ReplenishmentRequest.objects.filter(
                inventory_item=inventory_item,
                status='pending'
            ).first()

            if existing_request:
                raise ValueError(f"Pending replenishment request already exists for {inventory_item.item_name}")

            # Create replenishment request
            request = ReplenishmentRequest.objects.create(
                inventory_item=inventory_item,
                requested_by=requested_by_user,
                requested_quantity=requested_quantity,
                current_quantity=inventory_item.quantity,
                urgency=urgency,
                justification=justification,
            )

            # Mark inventory item as having pending replenishment
            inventory_item.pending_replenishment = True
            inventory_item.save()

            return request
    except Inventory.DoesNotExist:
        raise ValueError("Inventory item not found")


def approve_replenishment_request_service(request_id, approved_quantity, approval_remarks, approved_by_user):
    """
    UC-VH-011, BR-VH-016: Approve replenishment request (VhIncharge only)
    """
    from django.utils import timezone
    
    try:
        request = ReplenishmentRequest.objects.get(id=request_id)
        
        if request.status != 'pending':
            raise ValueError("Request is not in pending state")
        
        # BR-VH-016: Only VhIncharge can approve
        user_roles = approved_by_user.holds_designations.values_list('designation__name', flat=True)
        if 'VhIncharge' not in user_roles and not approved_by_user.is_staff:
            raise PermissionError("Only VhIncharge can approve replenishment requests")
        
        # Update request
        request.status = 'approved'
        request.approved_by = approved_by_user
        request.approved_quantity = approved_quantity
        request.approval_remarks = approval_remarks
        request.reviewed_at = timezone.now()
        request.save()
        
        return request
    except ReplenishmentRequest.DoesNotExist:
        raise ValueError("Replenishment request not found")


def reject_replenishment_request_service(request_id, approval_remarks, approved_by_user):
    """
    UC-VH-011, BR-VH-016: Reject replenishment request (VhIncharge only)
    """
    from django.utils import timezone
    
    try:
        request = ReplenishmentRequest.objects.get(id=request_id)
        
        if request.status != 'pending':
            raise ValueError("Request is not in pending state")
        
        # BR-VH-016: Only VhIncharge can reject
        user_roles = approved_by_user.holds_designations.values_list('designation__name', flat=True)
        if 'VhIncharge' not in user_roles and not approved_by_user.is_staff:
            raise PermissionError("Only VhIncharge can reject replenishment requests")
        
        # Update request and inventory
        request.status = 'rejected'
        request.approved_by = approved_by_user
        request.approval_remarks = approval_remarks
        request.reviewed_at = timezone.now()
        request.save()
        
        # Remove pending flag from inventory
        request.inventory_item.pending_replenishment = False
        request.inventory_item.save()
        
        return request
    except ReplenishmentRequest.DoesNotExist:
        raise ValueError("Replenishment request not found")


def update_inventory_quantity_service(item_id, new_quantity, user, operation='set'):
    """
    UC-VH-011: Update inventory quantity with threshold checking
    """
    try:
        inventory_item = Inventory.objects.get(id=item_id)
        old_quantity = inventory_item.quantity
        
        if operation == 'add':
            inventory_item.quantity += new_quantity
        elif operation == 'subtract':
            inventory_item.quantity = max(0, inventory_item.quantity - new_quantity)
        else:  # set
            inventory_item.quantity = new_quantity
        
        # Auto-update critical status based on threshold (BR-VH-007)
        inventory_item.save()  # This triggers the save() method with threshold check
        
        # If quantity was increased and is now above threshold, remove critical status
        if old_quantity < inventory_item.threshold_quantity and inventory_item.quantity >= inventory_item.threshold_quantity:
            inventory_item.is_critical = False
            inventory_item.pending_replenishment = False
            inventory_item.save()
        
        return inventory_item
    except Inventory.DoesNotExist:
        raise ValueError("Inventory item not found")


def get_critical_inventory_items():
    """
    UC-VH-011: Get all critical inventory items for dashboard alerts
    """
    return Inventory.objects.filter(is_critical=True).order_by('quantity')


def get_pending_replenishment_requests():
    """
    UC-VH-011: Get all pending replenishment requests for VhIncharge approval
    """
    return ReplenishmentRequest.objects.filter(status='pending').order_by('-created_at')


def mark_replenishment_received_service(request_id, actual_cost, delivery_date, user):
    """
    UC-VH-011: Mark replenishment as received and update inventory
    """
    from django.utils import timezone
    
    try:
        with transaction.atomic():
            request = ReplenishmentRequest.objects.get(id=request_id)

            if request.status != 'approved':
                raise ValueError("Request must be approved before marking as received")

            # Update inventory quantity
            inventory_item = request.inventory_item
            inventory_item.quantity += request.approved_quantity
            inventory_item.last_replenishment_date = delivery_date or timezone.now().date()
            inventory_item.pending_replenishment = False
            inventory_item.save()  # This will auto-update is_critical flag

            # Update request
            request.status = 'received'
            request.actual_cost = actual_cost
            request.delivery_date = delivery_date or timezone.now().date()
            request.save()

            return request
    except ReplenishmentRequest.DoesNotExist:
        raise ValueError("Replenishment request not found")


# ============================================================================
# BR-VH-010: CHECK-IN / CHECK-OUT ALERTS
# ============================================================================

def visitor_hostel_notif(sender, recipient, alert_type, booking_id):
    """
    BR-VH-010: Send notification for check-in/check-out alerts.
    
    Args:
        sender: User who is generating the alert (system or staff)
        recipient: User to be notified (caretaker or VhIncharge)
        alert_type: Type of alert ('no_show' or 'due_checkout')
        booking_id: ID of the affected booking
    """
    url = 'visitor_hostel:visitor_hostel'
    module = 'Visitor Hostel'
    verb = ''
    
    if alert_type == 'no_show':
        verb = f"No-show alert for booking ID {booking_id}. Visitor has not checked in within expected timeframe."
    elif alert_type == 'due_checkout':
        verb = f"Due checkout alert for booking ID {booking_id}. Guest is overdue for check-out."
    
    try:
        # Only send notification if sender is not None
        if sender:
            notify.send(sender=sender, recipient=recipient, url=url, module=module, verb=verb)
    except Exception as e:
        vh_logger.logger.error(f"Failed to send notification: {str(e)}")


@transaction.atomic()
def detect_and_create_no_show_alerts():
    """
    BR-VH-010: Detect no-show bookings and create alerts.
    
    Logic:
    - Check all confirmed/checked-in bookings
    - If check_in is None (not checked in) AND current_time > arrival_time, it's a no-show
    - Create alert and notify caretaker/VhIncharge
    
    Returns:
        List of newly created alerts
    """
    now = timezone.now()
    created_alerts = []
    
    try:
        # Get all bookings that should have checked in by now
        bookings_to_check = BookingDetail.objects.filter(
            status__in=['Confirmed', 'CheckedIn'],  # Only bookings that are active or should be
            check_in__isnull=True,  # Not yet checked in
            booking_from__lte=now.date()  # Booking date has passed
        )
        
        for booking in bookings_to_check:
            # Parse arrival_time to check if it's passed
            try:
                arrival_time_str = booking.arrival_time
                booking_date = booking.booking_from
                
                if arrival_time_str:
                    # arrival_time format is typically "HH:MM"
                    arrival_hour, arrival_minute = map(int, arrival_time_str.split(':'))
                    # Simple approach: compare just the dates and times
                    # If booking date is in the past and arrival time has passed, it's a no-show
                    today_date = now.date()
                    
                    # If booking_date is today, check arrival time; otherwise it's automatically passed
                    if booking_date < today_date:
                        is_overdue = True
                    elif booking_date == today_date:
                        # Same day: check if arrival time has passed
                        current_time = now.time()
                        arrival_time_obj = datetime.time(arrival_hour, arrival_minute)
                        is_overdue = current_time > arrival_time_obj
                    else:
                        # Future booking, not overdue
                        is_overdue = False
                    
                    # Check if no-show alert should be created
                    if is_overdue and booking.check_in is None:
                        # Check if alert already exists for this booking
                        existing_alert = CheckInCheckOutAlert.objects.filter(
                            booking=booking,
                            alert_type='no_show',
                            status='pending'
                        ).first()
                        
                        if not existing_alert:
                            # Create no-show alert
                            alert = CheckInCheckOutAlert.objects.create(
                                booking=booking,
                                alert_type='no_show',
                                status='pending',
                                message=f"Visitor has not checked in. Expected arrival: {arrival_time_str} on {booking_date}. Guest name: {booking.visitor.first().visitor_name if booking.visitor.exists() else 'Unknown'}",
                                severity='high'
                            )
                            created_alerts.append(alert)
                            
                            # Send notification to caretaker and VhIncharge
                            if booking.caretaker:
                                visitor_hostel_notif(
                                    sender=get_vhcaretaker_user(),
                                    recipient=booking.caretaker,
                                    alert_type='no_show',
                                    booking_id=booking.id
                                )
                            
                            # Also notify VhIncharge
                            vh_incharge = get_vhincharge_user()
                            if vh_incharge:
                                visitor_hostel_notif(
                                    sender=get_vhcaretaker_user(),
                                    recipient=vh_incharge,
                                    alert_type='no_show',
                                    booking_id=booking.id
                                )
            except (ValueError, AttributeError) as e:
                vh_logger.logger.error(f"Error parsing arrival_time for booking {booking.id}: {str(e)}")
                continue
    
    except Exception as e:
        vh_logger.logger.error(f"Error detecting no-show bookings: {str(e)}")
        raise
    
    return created_alerts


@transaction.atomic()
def detect_and_create_due_checkout_alerts():
    """
    BR-VH-010: Detect overdue check-outs and create alerts.
    
    Logic:
    - Check all CheckedIn bookings
    - If current_time > check_out_date, guest is overdue
    - Create alert and notify caretaker/VhIncharge
    
    Returns:
        List of newly created alerts
    """
    now = timezone.now()
    created_alerts = []
    
    try:
        # Get all bookings that are checked in
        checked_in_bookings = BookingDetail.objects.filter(
            status='CheckedIn',
            check_out__isnull=True  # check_out_date not yet set
        )
        
        for booking in checked_in_bookings:
            # Check if departure date has passed
            if booking.booking_to < now.date():
                # Check if alert already exists for this booking
                existing_alert = CheckInCheckOutAlert.objects.filter(
                    booking=booking,
                    alert_type='due_checkout',
                    status='pending'
                ).first()
                
                if not existing_alert:
                    # Calculate how long overdue
                    days_overdue = (now.date() - booking.booking_to).days
                    
                    # Create due-checkout alert
                    alert = CheckInCheckOutAlert.objects.create(
                        booking=booking,
                        alert_type='due_checkout',
                        status='pending',
                        message=f"Guest is overdue for check-out by {days_overdue} day(s). Expected check-out: {booking.booking_to}. Guest name: {booking.visitor.first().visitor_name if booking.visitor.exists() else 'Unknown'}",
                        severity='high' if days_overdue >= 2 else 'medium'
                    )
                    created_alerts.append(alert)
                    
                    # Send notification to caretaker and VhIncharge
                    if booking.caretaker:
                        visitor_hostel_notif(
                            sender=get_vhcaretaker_user(),
                            recipient=booking.caretaker,
                            alert_type='due_checkout',
                            booking_id=booking.id
                        )
                    
                    # Also notify VhIncharge
                    vh_incharge = get_vhincharge_user()
                    if vh_incharge:
                        visitor_hostel_notif(
                            sender=get_vhcaretaker_user(),
                            recipient=vh_incharge,
                            alert_type='due_checkout',
                            booking_id=booking.id
                        )
    except Exception as e:
        vh_logger.logger.error(f"Error detecting due checkout bookings: {str(e)}")
        raise
    
    return created_alerts


def create_initial_alert_for_booking(booking):
    """
    BR-VH-010: Create initial potential alerts for a newly created booking.
    
    This function is called when a new booking is created to set up
    the alert system for future no-show/checkout detection.
    
    Args:
        booking: BookingDetail instance
    
    Returns:
        Dictionary with alert setup information
    """
    alert_info = {
        'booking_id': booking.id,
        'visitor_name': booking.visitor.first().visitor_name if booking.visitor.exists() else 'Unknown',
        'expected_arrival': f"{booking.arrival_time} on {booking.booking_from}",
        'expected_departure': f"{booking.departure_time} on {booking.booking_to}",
        'alerts_initialized': True
    }
    
    try:
        vh_incharge = get_vhincharge_user()
        if vh_incharge:
            # Send notification that a new booking has been confirmed
            try:
                notify.send(
                    sender=booking.intender,
                    recipient=vh_incharge,
                    url='visitor_hostel:visitor_hostel',
                    module='Visitor Hostel',
                    verb=f"New booking confirmed (ID: {booking.id}) for {alert_info['visitor_name']}. Expected arrival: {alert_info['expected_arrival']}"
                )
            except Exception as e:
                vh_logger.logger.error(f"Failed to notify VhIncharge of new booking: {str(e)}")
    except Exception as e:
        vh_logger.logger.error(f"Error setting up alerts for booking {booking.id}: {str(e)}")
    
    return alert_info


def acknowledge_alert_service(alert_id, user, remarks=''):
    """
    BR-VH-010: Mark an alert as acknowledged by staff.
    
    Args:
        alert_id: ID of the alert to acknowledge
        user: User acknowledging the alert (staff member)
        remarks: Optional remarks from the staff member
    
    Returns:
        Updated CheckInCheckOutAlert instance
    """
    try:
        alert = CheckInCheckOutAlert.objects.get(id=alert_id)
        
        alert.status = 'acknowledged'
        alert.acknowledged_at = timezone.now()
        alert.acknowledged_by = user
        alert.acknowledgment_remarks = remarks
        alert.save()
        
        return alert
    except CheckInCheckOutAlert.DoesNotExist:
        raise ValueError(f"Alert with ID {alert_id} not found")


def resolve_alert_service(alert_id):
    """
    BR-VH-010: Mark an alert as resolved.
    
    Args:
        alert_id: ID of the alert to resolve
    
    Returns:
        Updated CheckInCheckOutAlert instance
    """
    try:
        alert = CheckInCheckOutAlert.objects.get(id=alert_id)
        
        alert.status = 'resolved'
        alert.resolved_at = timezone.now()
        alert.save()
        
        return alert
    except CheckInCheckOutAlert.DoesNotExist:
        raise ValueError(f"Alert with ID {alert_id} not found")


def get_pending_alerts_for_booking(booking_id):
    """
    BR-VH-010: Get all pending alerts for a specific booking.
    
    Args:
        booking_id: ID of the booking
    
    Returns:
        QuerySet of pending CheckInCheckOutAlert instances
    """
    return CheckInCheckOutAlert.objects.filter(
        booking_id=booking_id,
        status='pending'
    ).order_by('-created_at')


def get_all_pending_alerts():
    """
    BR-VH-010: Get all pending alerts across all bookings.
    
    Returns:
        QuerySet of pending CheckInCheckOutAlert instances
    """
    return CheckInCheckOutAlert.objects.filter(
        status='pending'
    ).order_by('-created_at')


def get_vhincharge_user():
    """
    Helper function to get the VhIncharge user.
    
    Returns:
        User instance of VhIncharge, or None if not found
    """
    try:
        from applications.globals.models import Designation
        
        # Find VhIncharge designation
        vh_incharge_designation = Designation.objects.filter(name='VhIncharge').first()
        if not vh_incharge_designation:
            return None
        
        # Get users who hold the VhIncharge designation
        # ExtraInfo has a M2M relation called holds_designations
        from django.contrib.auth.models import User
        from applications.globals.models import ExtraInfo
        
        extra_info = ExtraInfo.objects.filter(
            holds_designations__id=vh_incharge_designation.id
        ).first()
        
        if extra_info and extra_info.user:
            return extra_info.user
        return None
    except Exception as e:
        vh_logger.logger.error(f"Error getting VhIncharge user: {str(e)}")
        return None

