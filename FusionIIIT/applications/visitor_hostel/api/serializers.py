"""DRF serializers for visitor_hostel API.

Validation classes are introduced incrementally to preserve existing behavior.
"""

from rest_framework import serializers


class BookingIdSerializer(serializers.Serializer):
	booking_id = serializers.IntegerField(min_value=1)


class ConfirmBookingSerializer(serializers.Serializer):
	booking_id = serializers.IntegerField(min_value=1)
	category = serializers.CharField(max_length=2)
	rooms = serializers.ListField(child=serializers.CharField(max_length=20), allow_empty=True)


class CancelBookingSerializer(serializers.Serializer):
	booking_id = serializers.IntegerField(min_value=1)
	remark = serializers.CharField(allow_blank=True, required=False)
	charges = serializers.IntegerField(min_value=0, required=False)


class CancelBookingRequestSerializer(serializers.Serializer):
	booking_id = serializers.IntegerField(min_value=1)
	remark = serializers.CharField(allow_blank=True, required=False)


class CancelBookingReviewSerializer(serializers.Serializer):
	booking_id = serializers.IntegerField(min_value=1)
	remark = serializers.CharField(allow_blank=True, required=False)
	transaction_id = serializers.CharField(max_length=120, required=False, allow_blank=True)


class RejectBookingSerializer(serializers.Serializer):
	booking_id = serializers.IntegerField(min_value=1)
	remark = serializers.CharField(allow_blank=True, required=False)


class ForwardBookingSerializer(serializers.Serializer):
	booking_id = serializers.IntegerField(min_value=1)
	modified_category = serializers.CharField(max_length=2, required=False, allow_blank=True)
	rooms = serializers.ListField(child=serializers.CharField(max_length=20), allow_empty=True)
	remark = serializers.CharField(allow_blank=True, required=False)
	bill_settlement = serializers.CharField(max_length=30, required=False, allow_blank=True)


class CheckOutSerializer(serializers.Serializer):
	booking_id = serializers.IntegerField(min_value=1)
	meal_bill = serializers.IntegerField(min_value=0)
	room_bill = serializers.IntegerField(min_value=0, required=False, allow_null=True)
	extra_charges = serializers.IntegerField(min_value=0, required=False, default=0)
	payment_mode = serializers.ChoiceField(choices=['online', 'offline'])
	transaction_id = serializers.CharField(max_length=120, required=False, allow_blank=True)
	payment_screenshot = serializers.FileField(required=False, allow_null=True)
	offline_bill_id = serializers.CharField(max_length=120, required=False, allow_blank=True)
	offline_bill_photo = serializers.FileField(required=False, allow_null=True)
	bill_settlement = serializers.ChoiceField(
		choices=['Intender', 'Visitor', 'ProjectNo', 'Institute'],
		required=False,
	)

	def validate(self, attrs):
		payment_mode = attrs.get('payment_mode')
		if payment_mode == 'online':
			if not attrs.get('transaction_id'):
				raise serializers.ValidationError('transaction_id is required for online payment.')
			if not attrs.get('payment_screenshot'):
				raise serializers.ValidationError('payment_screenshot is required for online payment.')
		if payment_mode == 'offline':
			if not attrs.get('offline_bill_id'):
				raise serializers.ValidationError('offline_bill_id is required for offline payment.')
			if not attrs.get('offline_bill_photo'):
				raise serializers.ValidationError('offline_bill_photo is required for offline payment.')
		return attrs


class SettleBillSerializer(serializers.Serializer):
	booking_id = serializers.IntegerField(min_value=1)
	bill_settlement = serializers.ChoiceField(
		choices=['Intender', 'Visitor', 'ProjectNo', 'Institute'],
		required=False,
	)
	payment_status = serializers.BooleanField(required=False, default=True)
	meal_bill = serializers.IntegerField(min_value=0, required=False)
	room_bill = serializers.IntegerField(min_value=0, required=False)
	extra_charges = serializers.IntegerField(min_value=0, required=False)
	payment_mode = serializers.ChoiceField(choices=['online', 'offline'], required=False)
	transaction_id = serializers.CharField(max_length=120, required=False, allow_blank=True)
	payment_screenshot = serializers.FileField(required=False, allow_null=True)
	offline_bill_id = serializers.CharField(max_length=120, required=False, allow_blank=True)
	offline_bill_photo = serializers.FileField(required=False, allow_null=True)

	def validate_payment_status(self, value):
		"""Convert string boolean values from FormData to actual boolean"""
		if isinstance(value, str):
			return value.lower() in ('true', '1', 'yes')
		return value



class DateRangeSerializer(serializers.Serializer):
	start_date = serializers.DateField()
	end_date = serializers.DateField()
	category = serializers.CharField(max_length=1, required=False, allow_blank=True)

	def validate(self, attrs):
		if attrs['start_date'] > attrs['end_date']:
			raise serializers.ValidationError('start_date must be less than or equal to end_date.')
		return attrs


class ReportDaysSerializer(serializers.Serializer):
	days = serializers.IntegerField(min_value=1, max_value=365)


class CheckInSerializer(serializers.Serializer):
	booking_id = serializers.IntegerField(min_value=1)
	name = serializers.CharField(max_length=100)
	phone = serializers.CharField(max_length=20)
	email = serializers.CharField(max_length=100, allow_blank=True, required=False)
	address = serializers.CharField(allow_blank=True, required=False)


class UpdateBookingSerializer(serializers.Serializer):
	booking_id = serializers.IntegerField(min_value=1)
	number_of_people = serializers.IntegerField(min_value=1, required=False)
	purpose_of_visit = serializers.CharField(allow_blank=True)
	booking_from = serializers.DateField()
	booking_to = serializers.DateField()
	number_of_rooms = serializers.IntegerField(min_value=1)


class UpdateVisitorInfoSerializer(serializers.Serializer):
	booking_id = serializers.IntegerField(min_value=1)
	visitor_name = serializers.CharField(max_length=40, required=False, allow_blank=True)
	visitor_email = serializers.CharField(max_length=40, required=False, allow_blank=True)
	visitor_phone = serializers.CharField(max_length=15, required=False, allow_blank=True)
	visitor_organization = serializers.CharField(max_length=100, required=False, allow_blank=True)
	visitor_address = serializers.CharField(required=False, allow_blank=True)
	nationality = serializers.CharField(max_length=20, required=False, allow_blank=True)


class RecordMealSerializer(serializers.Serializer):
	visitor_id = serializers.IntegerField(min_value=1)
	booking_id = serializers.IntegerField(min_value=1)
	m_tea = serializers.IntegerField(min_value=0, required=False, default=0)
	breakfast = serializers.IntegerField(min_value=0, required=False, default=0)
	lunch = serializers.IntegerField(min_value=0, required=False, default=0)
	eve_tea = serializers.IntegerField(min_value=0, required=False, default=0)
	dinner = serializers.IntegerField(min_value=0, required=False, default=0)
	meal_type = serializers.CharField(max_length=20, required=False, help_text="Meal type: breakfast, lunch, or dinner (for deadline validation)")

	def validate(self, attrs):
		"""BR-VH-011: Validate meal booking deadlines.
		
		Deadlines:
		- Breakfast/morning_tea: ≤ 09:00
		- Lunch: ≤ 09:00
		- Dinner/evening_tea: ≤ 14:00
		"""
		import datetime
		meal_type = attrs.get('meal_type', '').lower()
		current_time = datetime.datetime.now().time()
		
		if meal_type == 'lunch':
			deadline = datetime.time(9, 0)  # 09:00
			if current_time > deadline:
				raise serializers.ValidationError(f'Lunch booking deadline is 09:00. Current time: {current_time.strftime("%H:%M")}')
		elif meal_type == 'dinner':
			deadline = datetime.time(14, 0)  # 14:00
			if current_time > deadline:
				raise serializers.ValidationError(f'Dinner booking deadline is 14:00. Current time: {current_time.strftime("%H:%M")}')
		elif meal_type == 'breakfast':
			deadline = datetime.time(9, 0)  # 09:00
			if current_time > deadline:
				raise serializers.ValidationError(f'Breakfast booking deadline is 09:00. Current time: {current_time.strftime("%H:%M")}')
		
		return attrs


class AddInventorySerializer(serializers.Serializer):
	item_name = serializers.CharField(max_length=100)
	bill_number = serializers.CharField(max_length=100)
	quantity = serializers.IntegerField(min_value=0)
	cost = serializers.IntegerField(min_value=0)
	consumable = serializers.BooleanField()
	
	# UC-VH-011: Enhanced inventory fields for threshold management (BR-VH-007)
	threshold_quantity = serializers.IntegerField(min_value=1, default=5, help_text="Minimum quantity before alert (BR-VH-007)")
	unit = serializers.CharField(max_length=20, default='pieces', help_text="Unit of measurement")
	category = serializers.CharField(max_length=50, allow_blank=True, required=False, help_text="Item category")
	remark = serializers.CharField(allow_blank=True, required=False, help_text="Additional notes")
	
	# VhIncharge requirement: Bill photo for inventory replenishment
	bill_photo = serializers.ImageField(required=True, help_text="Bill photo is mandatory for inventory replenishment")
	
	def validate_bill_photo(self, value):
		"""Validate bill photo file."""
		if not value:
			raise serializers.ValidationError("Bill photo is required for inventory replenishment")
		
		# Check file size (max 5MB)
		if value.size > 5 * 1024 * 1024:
			raise serializers.ValidationError("Bill photo must be less than 5MB")
		
		# Check file type
		allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
		if value.content_type not in allowed_types:
			raise serializers.ValidationError("Please upload a valid image file (JPEG, PNG, or GIF)")
		
		return value


class UpdateInventorySerializer(serializers.Serializer):
	id = serializers.IntegerField(min_value=1)
	quantity = serializers.IntegerField()
	bill_number = serializers.CharField(max_length=100, help_text="Bill number for stock update")
	cost = serializers.IntegerField(min_value=0, help_text="Cost of additional stock")
	
	# VhIncharge requirement: Bill photo for stock updates/replenishment
	bill_photo = serializers.ImageField(required=True, help_text="Bill photo is mandatory for inventory stock updates")
	
	def validate_bill_photo(self, value):
		"""Validate bill photo file for stock updates."""
		if not value:
			raise serializers.ValidationError("Bill photo is required for inventory stock updates")
		
		# Check file size (max 5MB)
		if value.size > 5 * 1024 * 1024:
			raise serializers.ValidationError("Bill photo must be less than 5MB")
		
		# Check file type
		allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
		if value.content_type not in allowed_types:
			raise serializers.ValidationError("Please upload a valid image file (JPEG, PNG, or GIF)")
		
		return value


class EditRoomStatusSerializer(serializers.Serializer):
	room_number = serializers.CharField(max_length=20)
	room_status = serializers.CharField(max_length=30)


class RequestBookingSerializer(serializers.Serializer):
	intender = serializers.IntegerField(min_value=1, required=False, allow_null=True)
	booking_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
	category = serializers.CharField(max_length=1)
	number_of_people = serializers.IntegerField(min_value=1)
	purpose_of_visit = serializers.CharField(allow_blank=True)
	booking_from = serializers.DateField()
	booking_to = serializers.DateField()
	booking_from_time = serializers.CharField(max_length=40, allow_blank=True, required=False)
	booking_to_time = serializers.CharField(max_length=40, allow_blank=True, required=False)
	remarks_during_booking_request = serializers.CharField(allow_blank=True, required=False)
	bill_settlement = serializers.CharField(max_length=30)
	number_of_rooms = serializers.IntegerField(min_value=1)
	name = serializers.CharField(max_length=100)
	phone = serializers.CharField(max_length=20)
	email = serializers.CharField(max_length=100, allow_blank=True, required=False)
	address = serializers.CharField(allow_blank=True, required=False)
	organization = serializers.CharField(max_length=100, allow_blank=True, required=False)
	nationality = serializers.CharField(max_length=50, allow_blank=True, required=False)
	# UC-VH-006: Offline booking fields
	is_offline = serializers.BooleanField(default=False, required=False)
	booking_source = serializers.CharField(max_length=10, required=False, allow_blank=True)
	intender_name = serializers.CharField(max_length=100, allow_blank=True, required=False)
	intender_phone = serializers.CharField(max_length=15, allow_blank=True, required=False)
	intender_email = serializers.CharField(max_length=100, allow_blank=True, required=False)
	intender_relation = serializers.CharField(max_length=50, allow_blank=True, required=False)


class BillGenerationSerializer(serializers.Serializer):
	visitor = serializers.CharField(max_length=30)
	mess_bill = serializers.IntegerField(min_value=0)
	room_bill = serializers.IntegerField(min_value=0)
	status = serializers.CharField(max_length=10)


# ============================================================================
# BR-VH-010: CHECK-IN / CHECK-OUT ALERTS SERIALIZERS
# ============================================================================

class CheckInCheckOutAlertSerializer(serializers.Serializer):
	"""Serializer for CheckInCheckOutAlert model"""
	id = serializers.IntegerField(read_only=True)
	booking = serializers.IntegerField()
	alert_type = serializers.ChoiceField(choices=['no_show', 'due_checkout'])
	status = serializers.ChoiceField(choices=['pending', 'acknowledged', 'resolved'])
	message = serializers.CharField()
	severity = serializers.ChoiceField(choices=['low', 'medium', 'high'])
	created_at = serializers.DateTimeField(read_only=True)
	acknowledged_at = serializers.DateTimeField(read_only=True, allow_null=True)
	resolved_at = serializers.DateTimeField(read_only=True, allow_null=True)
	acknowledged_by = serializers.IntegerField(allow_null=True, required=False)
	acknowledgment_remarks = serializers.CharField(allow_blank=True, required=False)


class AcknowledgeAlertSerializer(serializers.Serializer):
	"""Serializer for acknowledging an alert"""
	alert_id = serializers.IntegerField(min_value=1)
	remarks = serializers.CharField(allow_blank=True, required=False)


class ResolveAlertSerializer(serializers.Serializer):
	"""Serializer for resolving an alert"""
	alert_id = serializers.IntegerField(min_value=1)


class AlertListFilterSerializer(serializers.Serializer):
	"""Serializer for filtering alerts"""
	booking_id = serializers.IntegerField(required=False, allow_null=True)
	alert_type = serializers.ChoiceField(choices=['no_show', 'due_checkout'], required=False, allow_null=True)
	status = serializers.ChoiceField(choices=['pending', 'acknowledged', 'resolved'], required=False, allow_null=True)
	severity = serializers.ChoiceField(choices=['low', 'medium', 'high'], required=False, allow_null=True)

