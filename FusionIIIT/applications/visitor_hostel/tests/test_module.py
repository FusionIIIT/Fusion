from django.test import TestCase
from unittest.mock import MagicMock, patch

from applications.visitor_hostel.models import Inventory
from applications.visitor_hostel.services import (
    check_out_service,
    confirm_booking_service,
    record_meal_service,
    update_inventory_service,
)


class VisitorHostelModuleSmokeTest(TestCase):
    def test_smoke(self):
        self.assertTrue(True)


class VisitorHostelServiceUnitTest(TestCase):
    @patch('applications.visitor_hostel.services.get_room_by_number')
    @patch('applications.visitor_hostel.services.get_booking_by_id')
    def test_confirm_booking_service_uses_selectors_and_notifies(self, mock_get_booking, mock_get_room):
        booking = MagicMock()
        booking.intender = MagicMock()
        booking.rooms = MagicMock()
        mock_get_booking.return_value = booking
        mock_get_room.side_effect = [MagicMock(), MagicMock()]
        notify_fn = MagicMock()
        acting_user = MagicMock()

        confirm_booking_service(booking_id=11, category='B', rooms=['101', '102'], acting_user=acting_user, notify_fn=notify_fn)

        mock_get_booking.assert_called_once_with(11)
        self.assertEqual(mock_get_room.call_count, 2)
        self.assertEqual(booking.rooms.add.call_count, 2)
        booking.save.assert_called_once()
        notify_fn.assert_called_once_with(acting_user, booking.intender, 'booking_confirmation')

    @patch('applications.visitor_hostel.services.get_meal_record_for_booking_visitor_date')
    @patch('applications.visitor_hostel.services.get_visitor_by_id')
    @patch('applications.visitor_hostel.services.get_booking_by_id')
    def test_record_meal_service_updates_existing_meal(self, mock_get_booking, mock_get_visitor, mock_get_meal):
        mock_get_booking.return_value = MagicMock()
        mock_get_visitor.return_value = MagicMock()
        meal = MagicMock()
        meal.morning_tea = 1
        meal.eve_tea = 2
        meal.breakfast = 3
        meal.lunch = 4
        meal.dinner = 5
        mock_get_meal.return_value = meal

        record_meal_service(
            booking_id=1,
            visitor_id=2,
            meal_date='2026-03-23',
            m_tea='1',
            breakfast='1',
            lunch='1',
            eve_tea='1',
            dinner='1',
        )

        self.assertEqual(meal.morning_tea, 2)
        self.assertEqual(meal.eve_tea, 3)
        self.assertEqual(meal.breakfast, 4)
        self.assertEqual(meal.lunch, 5)
        self.assertEqual(meal.dinner, 6)
        meal.save.assert_called_once()

    def test_update_inventory_service_clears_critical_when_quantity_reaches_threshold(self):
        item = Inventory.objects.create(item_name='Soap', quantity=3, threshold_quantity=5)
        self.assertTrue(item.is_critical)

        updated_item = update_inventory_service(item.id, quantity=5)

        updated_item.refresh_from_db()
        self.assertEqual(updated_item.quantity, 5)
        self.assertFalse(updated_item.is_critical)
        self.assertFalse(updated_item.pending_replenishment)

    def test_update_inventory_service_sets_critical_when_quantity_drops_below_threshold(self):
        item = Inventory.objects.create(item_name='Towel', quantity=8, threshold_quantity=5)
        self.assertFalse(item.is_critical)

        updated_item = update_inventory_service(item.id, quantity=4)

        updated_item.refresh_from_db()
        self.assertEqual(updated_item.quantity, 4)
        self.assertTrue(updated_item.is_critical)

    @patch('applications.visitor_hostel.services.Bill.objects.create')
    @patch('applications.visitor_hostel.services.BookingDetail.objects.filter')
    @patch('applications.visitor_hostel.services.calculate_room_bill_for_booking')
    @patch('applications.visitor_hostel.services.get_booking_by_id')
    def test_check_out_service_auto_calculates_room_bill_when_missing(
        self,
        mock_get_booking,
        mock_calculate_room_bill,
        mock_filter,
        mock_bill_create,
    ):
        booking = MagicMock()
        booking.check_in = '2026-04-18'
        booking.booking_from = '2026-04-18'
        booking.booking_to = '2026-04-21'
        booking.bill_to_be_settled_by = 'Intender'
        mock_get_booking.return_value = booking
        mock_filter.return_value.update.return_value = 1
        mock_calculate_room_bill.return_value = 2400

        check_out_service(
            booking_id=12,
            meal_bill=300,
            room_bill=None,
            extra_charges=50,
            payment_mode='online',
            transaction_id='txn-123',
            payment_screenshot=None,
            offline_bill_id='',
            offline_bill_photo=None,
            bill_settlement='Visitor',
            acting_user=MagicMock(),
        )

        mock_calculate_room_bill.assert_called_once()
        mock_bill_create.assert_called_once()
        kwargs = mock_bill_create.call_args.kwargs
        self.assertEqual(kwargs['meal_bill'], 300)
        self.assertEqual(kwargs['room_bill'], 2400)
        self.assertEqual(kwargs['extra_charges'], 50)
        self.assertEqual(kwargs['payment_mode'], 'online')
        self.assertEqual(kwargs['transaction_id'], 'txn-123')
