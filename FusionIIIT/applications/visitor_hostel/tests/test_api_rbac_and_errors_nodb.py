from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from applications.visitor_hostel.api import views as vh_views
from applications.visitor_hostel.services import VisitorHostelServiceError


class _RoleHolder:
    def __init__(self, roles):
        self._roles = list(roles)

    def values_list(self, *_args, **_kwargs):
        return self._roles


def _user(username='user', roles=(), is_staff=False, is_active=True, user_id=1):
    return SimpleNamespace(
        id=user_id,
        username=username,
        is_staff=is_staff,
        is_active=is_active,
        is_authenticated=True,
        holds_designations=_RoleHolder(roles),
    )


def _booking(status='Pending', intender=None, booking_id=1):
    return SimpleNamespace(
        id=booking_id,
        status=status,
        intender=intender or _user('owner'),
        booking_from='2026-05-01',
        booking_to='2026-05-02',
    )


class VisitorHostelApiRbacAndErrorNoDbTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not hasattr(vh_views.ConfirmBookingApiView, '_get_client_ip'):
            setattr(vh_views.ConfirmBookingApiView, '_get_client_ip', lambda self, _request: '127.0.0.1')

    def setUp(self):
        self.factory = APIRequestFactory()
        self.regular = _user('regular', user_id=101)
        self.caretaker = _user('caretaker', roles=('VhCaretaker',), user_id=102)
        self.incharge = _user('incharge', roles=('VhIncharge',), user_id=103)

    def _call_post(self, view_cls, path, user, data=None):
        request = self.factory.post(path, data or {}, format='json')
        request.user = user
        return view_cls.as_view()(request)

    def _call_get(self, view_cls, path, user):
        request = self.factory.get(path)
        request.user = user
        return view_cls.as_view()(request)

    def test_01_health_ok(self):
        response = self._call_get(vh_views.VisitorHostelApiHealthView, '/visitorhostel/api/health/', self.regular)
        self.assertEqual(response.status_code, 200)

    @patch('applications.visitor_hostel.api.views.vh_logger.log_security_event')
    def test_02_confirm_denied_for_regular_user(self, _mock_log_security_event):
        response = self._call_post(vh_views.ConfirmBookingApiView, '/visitorhostel/api/bookings/confirm/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_03_cancel_denied_for_regular_user(self):
        response = self._call_post(vh_views.CancelBookingApiView, '/visitorhostel/api/bookings/cancel/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_04_cancel_approve_denied_for_regular_user(self):
        response = self._call_post(vh_views.ApproveCancelBookingRequestApiView, '/visitorhostel/api/bookings/cancel-approve/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_05_cancel_reject_denied_for_regular_user(self):
        response = self._call_post(vh_views.RejectCancelBookingRequestApiView, '/visitorhostel/api/bookings/cancel-reject/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_06_reject_booking_denied_for_regular_user(self):
        response = self._call_post(vh_views.RejectBookingApiView, '/visitorhostel/api/bookings/reject/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_07_forward_denied_for_regular_user(self):
        response = self._call_post(vh_views.ForwardBookingApiView, '/visitorhostel/api/bookings/forward/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_08_checkout_denied_for_regular_user(self):
        response = self._call_post(vh_views.CheckOutApiView, '/visitorhostel/api/bookings/checkout/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_09_checkin_denied_for_regular_user(self):
        response = self._call_post(vh_views.CheckInApiView, '/visitorhostel/api/bookings/checkin/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_10_record_meal_denied_for_regular_user(self):
        response = self._call_post(vh_views.RecordMealApiView, '/visitorhostel/api/meals/record/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_11_add_inventory_denied_for_regular_user(self):
        response = self._call_post(vh_views.AddInventoryApiView, '/visitorhostel/api/inventory/add/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_12_update_inventory_denied_for_caretaker(self):
        response = self._call_post(vh_views.UpdateInventoryApiView, '/visitorhostel/api/inventory/update/', self.caretaker)
        self.assertEqual(response.status_code, 403)

    def test_13_inventory_list_denied_for_regular_user(self):
        response = self._call_get(vh_views.InventoryListApiView, '/visitorhostel/api/inventory/list/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_14_edit_room_status_denied_for_regular_user(self):
        response = self._call_post(vh_views.EditRoomStatusApiView, '/visitorhostel/api/rooms/status/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_15_bill_report_denied_for_regular_user(self):
        response = self._call_get(vh_views.BillBetweenDatesApiView, '/visitorhostel/api/reports/bills/?start_date=2026-01-01&end_date=2026-01-02', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_16_booking_report_denied_for_regular_user(self):
        response = self._call_get(vh_views.BookingReportsApiView, '/visitorhostel/api/reports/bookings/?days=7', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_17_inventory_report_denied_for_regular_user(self):
        response = self._call_get(vh_views.InventoryReportsApiView, '/visitorhostel/api/reports/inventory/?days=7', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_18_detect_no_shows_denied_for_regular_user(self):
        response = self._call_post(vh_views.DetectNoShowsApiView, '/visitorhostel/api/bookings/detect-no-shows/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_19_detect_overstays_get_denied_for_regular_user(self):
        response = self._call_get(vh_views.DetectOverstaysApiView, '/visitorhostel/api/bookings/detect-overstays/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_20_detect_overstays_post_denied_for_regular_user(self):
        response = self._call_post(vh_views.DetectOverstaysApiView, '/visitorhostel/api/bookings/detect-overstays/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_21_due_checkouts_get_denied_for_regular_user(self):
        response = self._call_get(vh_views.DetectDueCheckoutsApiView, '/visitorhostel/api/bookings/detect-due-checkouts/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_22_due_checkouts_post_denied_for_regular_user(self):
        response = self._call_post(vh_views.DetectDueCheckoutsApiView, '/visitorhostel/api/bookings/detect-due-checkouts/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_23_bill_generation_denied_for_regular_user(self):
        response = self._call_post(vh_views.BillGenerationApiView, '/visitorhostel/api/bills/generate/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_24_settle_bill_denied_for_regular_user(self):
        response = self._call_post(vh_views.SettleBillApiView, '/visitorhostel/api/bookings/settle-bill/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_25_threshold_get_denied_for_regular_user(self):
        response = self._call_get(vh_views.InventoryThresholdCheckApiView, '/visitorhostel/api/inventory/threshold-check/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_26_threshold_post_denied_for_regular_user(self):
        response = self._call_post(vh_views.InventoryThresholdCheckApiView, '/visitorhostel/api/inventory/threshold-check/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_27_replenishment_create_denied_for_regular_user(self):
        response = self._call_post(vh_views.ReplenishmentRequestApiView, '/visitorhostel/api/inventory/replenishment-request/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_28_replenishment_list_denied_for_regular_user(self):
        response = self._call_get(vh_views.ReplenishmentRequestApiView, '/visitorhostel/api/inventory/replenishment-request/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_29_approve_replenishment_denied_for_regular_user(self):
        response = self._call_post(vh_views.ApproveReplenishmentApiView, '/visitorhostel/api/inventory/approve-replenishment/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_30_reject_replenishment_denied_for_regular_user(self):
        response = self._call_post(vh_views.RejectReplenishmentApiView, '/visitorhostel/api/inventory/reject-replenishment/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_31_update_quantity_denied_for_regular_user(self):
        response = self._call_post(vh_views.UpdateInventoryQuantityApiView, '/visitorhostel/api/inventory/update-quantity/', self.regular)
        self.assertEqual(response.status_code, 403)

    def test_32_mark_received_denied_for_regular_user(self):
        response = self._call_post(vh_views.MarkReplenishmentReceivedApiView, '/visitorhostel/api/inventory/mark-received/', self.regular)
        self.assertEqual(response.status_code, 403)

    @patch('applications.visitor_hostel.api.views.has_overlapping_bookings', return_value=False)
    @patch('applications.visitor_hostel.api.views.confirm_booking_service', side_effect=VisitorHostelServiceError('business violation'))
    @patch('applications.visitor_hostel.api.views.ConfirmBookingSerializer')
    @patch('applications.visitor_hostel.api.views.get_booking_by_id')
    def test_33_confirm_handles_business_rule_error(self, mock_get_booking, mock_serializer, _mock_confirm, _mock_overlap):
        serializer = MagicMock()
        serializer.validated_data = {'booking_id': 10, 'category': 'C', 'rooms': []}
        mock_serializer.return_value = serializer
        mock_get_booking.return_value = _booking(status='Forward', intender=self.regular, booking_id=10)

        response = self._call_post(vh_views.ConfirmBookingApiView, '/visitorhostel/api/bookings/confirm/', self.incharge)
        self.assertEqual(response.status_code, 400)

    @patch('applications.visitor_hostel.api.views.has_overlapping_bookings', return_value=False)
    @patch('applications.visitor_hostel.api.views.confirm_booking_service', side_effect=Exception('unexpected'))
    @patch('applications.visitor_hostel.api.views.ConfirmBookingSerializer')
    @patch('applications.visitor_hostel.api.views.get_booking_by_id')
    def test_34_confirm_handles_unexpected_error(self, mock_get_booking, mock_serializer, _mock_confirm, _mock_overlap):
        serializer = MagicMock()
        serializer.validated_data = {'booking_id': 11, 'category': 'C', 'rooms': []}
        mock_serializer.return_value = serializer
        mock_get_booking.return_value = _booking(status='Forward', intender=self.regular, booking_id=11)

        response = self._call_post(vh_views.ConfirmBookingApiView, '/visitorhostel/api/bookings/confirm/', self.incharge)
        self.assertEqual(response.status_code, 500)

    @patch('applications.visitor_hostel.api.views.SettleBillSerializer')
    @patch('applications.visitor_hostel.api.views.get_booking_by_id')
    def test_35_settle_bill_rejects_non_complete_status(self, mock_get_booking, mock_serializer):
        serializer = MagicMock()
        serializer.validated_data = {'booking_id': 99, 'payment_status': True}
        mock_serializer.return_value = serializer
        mock_get_booking.return_value = _booking(status='Pending', intender=self.regular, booking_id=99)

        response = self._call_post(vh_views.SettleBillApiView, '/visitorhostel/api/bookings/settle-bill/', self.incharge)
        self.assertEqual(response.status_code, 400)

    @patch('applications.visitor_hostel.api.views.RequestBookingSerializer')
    def test_36_offline_booking_denied_for_non_caretaker(self, mock_serializer):
        serializer = MagicMock()
        serializer.validated_data = {
            'booking_id': 'BK-1',
            'category': 'C',
            'number_of_people': 1,
            'purpose_of_visit': 'Test',
            'booking_from': '2026-05-02',
            'booking_to': '2026-05-03',
            'bill_settlement': 'Intender',
            'number_of_rooms': 1,
            'name': 'Visitor',
            'phone': '9999999999',
            'is_offline': True,
        }
        mock_serializer.return_value = serializer

        response = self._call_post(vh_views.RequestBookingApiView, '/visitorhostel/api/bookings/request/', self.regular)
        self.assertEqual(response.status_code, 403)

    @patch('applications.visitor_hostel.api.views.CancelBookingRequestSerializer')
    @patch('applications.visitor_hostel.models.BookingDetail.objects.get')
    def test_37_cancel_request_denied_for_non_owner(self, mock_get_booking, mock_serializer):
        serializer = MagicMock()
        serializer.validated_data = {'booking_id': 5, 'remark': 'cancel'}
        mock_serializer.return_value = serializer
        mock_get_booking.return_value = _booking(status='Pending', intender=self.other_owner(), booking_id=5)

        response = self._call_post(vh_views.CancelBookingRequestApiView, '/visitorhostel/api/bookings/cancel-request/', self.regular)
        self.assertEqual(response.status_code, 403)

    @patch('applications.visitor_hostel.api.views.visitors_hostel_notif')
    @patch('applications.visitor_hostel.api.views.check_in_service')
    @patch('applications.visitor_hostel.api.views.get_booking_by_id')
    @patch('applications.visitor_hostel.api.views.CheckInSerializer')
    def test_38_checkin_success_notifies_owner(self, mock_serializer, mock_get_booking, mock_check_in, mock_notif):
        serializer = MagicMock()
        serializer.validated_data = {
            'booking_id': 11,
            'name': 'Guest',
            'phone': '9999999999',
            'email': 'guest@example.com',
            'address': 'Hostel Lane',
        }
        mock_serializer.return_value = serializer
        booking = _booking(status='Confirmed', intender=self.regular, booking_id=11)
        mock_get_booking.return_value = booking

        response = self._call_post(vh_views.CheckInApiView, '/visitorhostel/api/bookings/checkin/', self.caretaker, serializer.validated_data)

        self.assertEqual(response.status_code, 200)
        mock_check_in.assert_called_once()
        mock_notif.assert_called_once_with(self.caretaker, self.regular, 'booking_checkin_done')

    @patch('applications.visitor_hostel.api.views.visitors_hostel_notif')
    @patch('applications.visitor_hostel.api.views.check_out_service')
    @patch('applications.visitor_hostel.api.views.get_booking_by_id')
    @patch('applications.visitor_hostel.api.views.CheckOutSerializer')
    def test_39_checkout_success_notifies_owner(self, mock_serializer, mock_get_booking, mock_check_out, mock_notif):
        serializer = MagicMock()
        serializer.validated_data = {
            'booking_id': 12,
            'meal_bill': 100,
            'room_bill': 500,
            'extra_charges': 25,
            'payment_mode': 'online',
            'transaction_id': 'txn-123',
            'payment_screenshot': None,
            'offline_bill_id': '',
            'offline_bill_photo': None,
            'bill_settlement': 'Intender',
        }
        mock_serializer.return_value = serializer
        booking = _booking(status='CheckedIn', intender=self.regular, booking_id=12)
        mock_get_booking.return_value = booking

        response = self._call_post(vh_views.CheckOutApiView, '/visitorhostel/api/bookings/checkout/', self.caretaker, serializer.validated_data)

        self.assertEqual(response.status_code, 200)
        mock_check_out.assert_called_once()
        mock_notif.assert_called_once_with(self.caretaker, self.regular, 'booking_checkout_done')

    def other_owner(self):
        return _user('other_owner', user_id=104)
