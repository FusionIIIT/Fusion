"""Selector layer for visitor_hostel.

This file contains read/query operations.
Functions are added incrementally during refactor without changing behavior.
"""

import datetime

from django.db.models import Q

from applications.globals.models import HoldsDesignation
from applications.visitor_hostel.models import (
	Bill,
	BookingDetail,
	Inventory,
	InventoryBill,
	MealRecord,
	ReplenishmentRequest,
	RoomDetail,
	VisitorDetail,
)
from django.contrib.auth.models import User


class VisitorHostelRolePolicyError(Exception):
	"""Raised when BR-VH-015 single active role policy is violated."""


def validate_single_active_vh_roles():
	"""BR-VH-015: Exactly one active caretaker and one active in-charge must exist."""
	caretaker_working_ids = list(
		HoldsDesignation.objects.select_related('working', 'designation')
		.filter(designation__name='VhCaretaker')
		.values_list('working_id', flat=True)
		.distinct()
	)
	incharge_working_ids = list(
		HoldsDesignation.objects.select_related('working', 'designation')
		.filter(designation__name='VhIncharge')
		.values_list('working_id', flat=True)
		.distinct()
	)

	errors = []
	if len(caretaker_working_ids) != 1:
		errors.append(
			f"expected exactly 1 active VhCaretaker, found {len(caretaker_working_ids)}"
		)
	if len(incharge_working_ids) != 1:
		errors.append(
			f"expected exactly 1 active VhIncharge, found {len(incharge_working_ids)}"
		)

	if errors:
		raise VisitorHostelRolePolicyError('BR-VH-015 violation: ' + '; '.join(errors))

	return {
		'caretaker_user': User.objects.get(id=caretaker_working_ids[0]),
		'incharge_user': User.objects.get(id=incharge_working_ids[0]),
	}


def get_bills_in_range(date1, date2):
	bookings = BookingDetail.objects.select_related('intender', 'caretaker').filter(
		Q(booking_from__lte=date1, booking_to__gte=date1)
		| Q(booking_from__gte=date1, booking_to__lte=date2)
		| Q(booking_from__lte=date2, booking_to__gte=date2)
		| Q(booking_from__lte=date1, booking_to__gte=date1)
		| Q(booking_from__gte=date1, booking_to__lte=date2)
		| Q(booking_from__lte=date2, booking_to__gte=date2)
	)

	bookings_bw_dates = []
	booking_ids = []
	for booking_id in bookings:
		booking_ids.append(booking_id.id)

	for b_id in booking_ids:
		if Bill.objects.select_related('caretaker').filter(booking__pk=b_id).exists():
			bill_id = Bill.objects.select_related('caretaker').get(booking__pk=b_id)
			bookings_bw_dates.append(bill_id)

	return bookings_bw_dates


def get_bookings_for_last_n_days(days):
	start_date = datetime.date.today() - datetime.timedelta(days=int(days) - 1)
	return BookingDetail.objects.select_related('intender', 'caretaker').filter(
		booking_date__gte=start_date
	).order_by('-booking_date', '-id')


def get_replenishment_requests_for_last_n_days(days):
	start_date = datetime.date.today() - datetime.timedelta(days=int(days) - 1)
	return ReplenishmentRequest.objects.select_related(
		'inventory_item',
		'requested_by',
		'approved_by',
	).filter(created_at__date__gte=start_date).order_by('-created_at', '-id')


def get_available_rooms_between_dates(date1, date2, exclude_booking_id=None, category=None):
	"""
	OPTIMIZED VERSION: Eliminates N+1 queries with prefetch_related and set operations
	Performance improvement: O(n²) -> O(n) complexity
	"""
	# Use prefetch_related to fetch rooms in a single query
	bookings = BookingDetail.objects.prefetch_related('rooms').filter(
		Q(booking_from__lte=date1, booking_to__gte=date1, status="Confirmed")
		| Q(booking_from__gte=date1, booking_to__lte=date2, status="Confirmed")
		| Q(booking_from__lte=date2, booking_to__gte=date2, status="Confirmed")
		| Q(booking_from__lte=date1, booking_to__gte=date1, status="Forward")
		| Q(booking_from__gte=date1, booking_to__lte=date2, status="Forward")
		| Q(booking_from__lte=date2, booking_to__gte=date2, status="Forward")
		| Q(booking_from__lte=date1, booking_to__gte=date1, status="Pending")
		| Q(booking_from__gte=date1, booking_to__lte=date2, status="Pending")
		| Q(booking_from__lte=date2, booking_to__gte=date2, status="Pending")
		| Q(booking_from__lte=date1, booking_to__gte=date1, status="CheckedIn")
		| Q(booking_from__gte=date1, booking_to__lte=date2, status="CheckedIn")
		| Q(booking_from__lte=date2, booking_to__gte=date2, status="CheckedIn")
	)
	if exclude_booking_id is not None:
		bookings = bookings.exclude(id=exclude_booking_id)

	if category:
		bookings = bookings.filter(rooms__room_number__startswith=category).distinct()

	# OPTIMIZATION: Use set operations instead of nested loops
	booked_room_ids = set()
	for booking in bookings:
		booked_room_ids.update(room.id for room in booking.rooms.all())

	# OPTIMIZATION: Use exclude() instead of manual filtering
	all_rooms_query = RoomDetail.objects.all()
	if category:
		all_rooms_query = all_rooms_query.filter(room_number__startswith=category)
	
	available_rooms = all_rooms_query.exclude(id__in=booked_room_ids)
	return list(available_rooms)


def get_forwarded_rooms_between_dates(date1, date2):
	"""
	OPTIMIZED VERSION: Eliminates N+1 queries and unnecessary first query
	"""
	# OPTIMIZATION: Remove unused first query and use prefetch_related
	forwarded_bookings = BookingDetail.objects.prefetch_related('rooms').filter(
		Q(booking_from__lte=date1, booking_to__gte=date1, status="Forward")
		| Q(booking_from__gte=date1, booking_to__lte=date2, status="Forward")
		| Q(booking_from__lte=date2, booking_to__gte=date2, status="Forward")
	)

	# OPTIMIZATION: Use list comprehension instead of nested loops
	forwarded_booking_rooms = [
		room for booking in forwarded_bookings 
		for room in booking.rooms.all()
	]

	return forwarded_booking_rooms


def get_vhcaretaker_user():
	caretakers = HoldsDesignation.objects.select_related('working', 'designation').filter(
		designation__name='VhCaretaker'
	).order_by('-held_at')
	if caretakers.exists():
		return caretakers[0].working
	return None


def user_has_vhcaretaker_designation(user):
	return user.holds_designations.filter(designation__name='VhCaretaker').exists()


def user_has_vhincharge_designation(user):
	return user.holds_designations.filter(designation__name='VhIncharge').exists()


def get_vhincharge_user_legacy_preferred():
	"""Return current active in-charge (working user), preserving old API name."""
	incharges = HoldsDesignation.objects.select_related('working', 'designation').filter(
		designation__name='VhIncharge'
	).order_by('-held_at')
	if incharges.exists():
		return incharges[0].working
	return None


def get_pending_bookings_queryset():
	return BookingDetail.objects.select_related('intender', 'caretaker').filter(status='Pending').order_by('booking_from')


def get_active_bookings_queryset():
	return BookingDetail.objects.select_related('intender', 'caretaker').filter(
		Q(status='Confirmed') | Q(status='CheckedIn')
	).order_by('booking_from')


def get_inactive_bookings_queryset():
	return BookingDetail.objects.select_related('intender', 'caretaker').filter(
		Q(status="Cancelled") | Q(status="Rejected") | Q(status="Complete")
	)


def get_all_intenders():
	return User.objects.all()


def get_user_by_id(user_id):
	return User.objects.get(id=user_id)


def get_user_by_username(username):
	return User.objects.get(username=username)


def get_booking_by_id(booking_id):
	return BookingDetail.objects.select_related('intender', 'caretaker').get(id=booking_id)


def get_booking_by_visitor(visitor):
	return BookingDetail.objects.get(visitor=visitor)


def get_room_by_number(room_number):
	return RoomDetail.objects.get(room_number=room_number)


def get_visitor_by_id(visitor_id):
	return VisitorDetail.objects.get(id=visitor_id)


def get_first_visitor_by_phone_legacy(visitor_phone):
	visitor = VisitorDetail.objects.filter(visitor_phone=visitor_phone).first()
	return visitor


def has_overlapping_bookings(booking_from, booking_to, statuses=None, intender=None, exclude_booking_id=None):
	if statuses is None:
		statuses = ["Confirmed", "CheckedIn"]

	queryset = BookingDetail.objects.filter(
		booking_from__lte=booking_to,
		booking_to__gte=booking_from,
		status__in=statuses,
	)

	if intender is not None:
		queryset = queryset.filter(intender=intender)

	if exclude_booking_id is not None:
		queryset = queryset.exclude(id=exclude_booking_id)

	return queryset.exists()


def get_meal_record_for_booking_visitor_date(booking, visitor, meal_date):
	return MealRecord.objects.select_related('booking__intender', 'booking__caretaker', 'visitor').get(
		visitor=visitor,
		booking=booking,
		meal_date=meal_date,
	)


def get_meals_for_booking(booking_id):
	return MealRecord.objects.select_related('booking__intender', 'booking__caretaker', 'visitor').filter(
		booking_id=booking_id
	)


def get_all_bookings_ordered():
	return BookingDetail.objects.select_related('intender', 'caretaker').all().order_by('booking_from')


def get_pending_or_forward_bookings_for_user(user):
	return BookingDetail.objects.select_related('intender', 'caretaker').filter(
		Q(status="Pending") | Q(status="Forward"),
		booking_to__gte=datetime.datetime.today(),
		intender=user,
	).order_by('booking_from')


def get_checkedin_bookings_for_user(user):
	return BookingDetail.objects.select_related('intender', 'caretaker').filter(
		status="CheckedIn",
		booking_to__gte=datetime.datetime.today(),
		intender=user,
	).order_by('booking_from')


def get_dashboard_bookings_for_user(user):
	return BookingDetail.objects.select_related('intender', 'caretaker').filter(
		Q(status="Pending") | Q(status="Forward") | Q(status="Confirmed") | Q(status='Rejected'),
		booking_to__gte=datetime.datetime.today(),
		intender=user,
	).order_by('booking_from')


def get_completed_bookings_for_user(user):
	return BookingDetail.objects.select_related('intender', 'caretaker').filter(
		Q(status="Complete") | Q(status="Canceled"),
		intender=user,
	).order_by('booking_from').reverse()


def get_canceled_bookings_for_user(user):
	return BookingDetail.objects.select_related('intender', 'caretaker').filter(
		status="Canceled",
		intender=user,
	).order_by('booking_from')


def get_rejected_bookings_for_user(user):
	return BookingDetail.objects.select_related('intender', 'caretaker').filter(
		status='Rejected',
		intender=user,
	).order_by('booking_from')


def get_cancel_requested_bookings_for_user(user):
	return BookingDetail.objects.select_related('intender', 'caretaker').filter(
		status='CancelRequested',
		intender=user,
	).order_by('booking_from')


def get_pending_or_forward_bookings_for_staff():
	return BookingDetail.objects.select_related('intender', 'caretaker').filter(
		Q(status="Pending") | Q(status="Forward"),
		booking_to__gte=datetime.datetime.today(),
	).order_by('booking_from')


def get_confirmed_or_checkedin_bookings_for_staff():
	"""
	OPTIMIZED VERSION: Added prefetch_related for rooms and visitors to prevent N+1 queries
	"""
	return BookingDetail.objects.filter(
		Q(status="Confirmed") | Q(status="CheckedIn"),
		booking_to__gte=datetime.datetime.today(),
	).select_related('intender', 'caretaker').prefetch_related('rooms', 'visitor').order_by('booking_from')


def get_cancel_requested_bookings_for_staff():
	return BookingDetail.objects.select_related('intender', 'caretaker').filter(
		status="CancelRequested",
		booking_to__gte=datetime.datetime.today(),
	).order_by('booking_from')


def get_dashboard_bookings_for_staff():
	return BookingDetail.objects.select_related('intender', 'caretaker').filter(
		Q(status="Pending") | Q(status="Forward") | Q(status="Confirmed"),
		booking_to__gte=datetime.datetime.today(),
	).order_by('booking_from')


def get_completed_or_canceled_bookings_for_staff():
	return BookingDetail.objects.select_related('intender', 'caretaker').filter(
		Q(status="Canceled") | Q(status="Complete"),
	).select_related().order_by('booking_from').reverse()


def get_canceled_bookings_for_staff():
	return BookingDetail.objects.filter(status="Canceled").select_related('intender', 'caretaker').order_by('booking_from')


def get_rejected_bookings_for_staff():
	return BookingDetail.objects.select_related('intender', 'caretaker').filter(status='Rejected').order_by('booking_from')


def get_cancel_requested_bookings_for_user_future(user):
	return BookingDetail.objects.select_related('intender', 'caretaker').filter(
		status='CancelRequested',
		booking_to__gte=datetime.datetime.today(),
		intender=user,
	).order_by('booking_from')


def get_all_inventory():
	return Inventory.objects.all()


def get_all_inventory_bills():
	return InventoryBill.objects.select_related('item_name').all()


def get_all_bills():
	return Bill.objects.select_related()


def get_all_previous_visitors():
	return VisitorDetail.objects.all()


def get_future_forward_bookings():
	return BookingDetail.objects.select_related('intender', 'caretaker').filter(
		Q(status="Forward"), booking_to__gte=datetime.datetime.today()
	).order_by('booking_from')

