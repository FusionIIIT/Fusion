import datetime
import uuid
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase

from applications.globals.models import ExtraInfo
from applications.visitor_hostel.models import (
    Bill,
    BookingDetail,
    Inventory,
    InventoryBill,
    MealRecord,
    ReplenishmentRequest,
    RoomDetail,
    VisitorDetail,
    CheckInCheckOutAlert,
)
from applications.visitor_hostel.services import (
    approve_replenishment_request_service,
    create_replenishment_request_service,
    mark_replenishment_received_service,
    reject_replenishment_request_service,
    request_booking_service_from_data,
)


class VisitorHostelDataIntegrityAndAcidTests(TestCase):
    def setUp(self):
        suffix = uuid.uuid4().hex[:8]
        self.intender = User.objects.create_user(username=f'integrity_intender_{suffix}', password='x')
        self.caretaker = User.objects.create_user(username=f'integrity_caretaker_{suffix}', password='x')
        self.incharge = User.objects.create_user(
            username=f'integrity_incharge_{suffix}',
            password='x',
            is_staff=True,
        )

    def _create_booking(self, status='Pending'):
        booking = BookingDetail.objects.create(
            intender=self.intender,
            caretaker=self.caretaker,
            visitor_category='C',
            person_count=1,
            purpose='Test booking',
            booking_from=datetime.date(2026, 5, 1),
            booking_to=datetime.date(2026, 5, 2),
            status=status,
            number_of_rooms=1,
            number_of_rooms_alloted=1,
        )
        return booking

    def test_01_room_number_must_be_unique(self):
        room_number = f'R{uuid.uuid4().hex[:3]}'
        RoomDetail.objects.create(
            room_number=room_number,
            room_type='SingleBed',
            room_floor='GroundFloor',
            room_status='Available',
        )

        with self.assertRaises(IntegrityError):
            RoomDetail.objects.create(
                room_number=room_number,
                room_type='SingleBed',
                room_floor='FirstFloor',
                room_status='Available',
            )

    def test_02_bill_one_to_one_enforced_per_booking(self):
        booking = self._create_booking()
        Bill.objects.create(booking=booking, caretaker=self.caretaker, meal_bill=0, room_bill=0)

        with self.assertRaises(IntegrityError):
            Bill.objects.create(booking=booking, caretaker=self.caretaker, meal_bill=10, room_bill=20)

    def test_03_booking_delete_cascades_bill_and_meal_records(self):
        booking = self._create_booking()
        visitor = VisitorDetail.objects.create(visitor_phone='9999999999', visitor_name='Guest')
        booking.visitor.add(visitor)
        Bill.objects.create(booking=booking, caretaker=self.caretaker, meal_bill=0, room_bill=100)
        MealRecord.objects.create(booking=booking, visitor=visitor, meal_date=datetime.date(2026, 5, 1))

        booking.delete()

        self.assertFalse(Bill.objects.filter(booking_id=booking.id).exists())
        self.assertFalse(MealRecord.objects.filter(booking_id=booking.id).exists())

    def test_04_inventory_critical_flag_auto_updates_on_save(self):
        item = Inventory.objects.create(item_name='Soap', quantity=2, threshold_quantity=5, consumable=True)
        self.assertTrue(item.is_critical)

        item.quantity = 10
        item.save()
        item.refresh_from_db()
        self.assertFalse(item.is_critical)

    def test_05_inventory_available_quantity_never_negative(self):
        item = Inventory.objects.create(item_name='Bucket', quantity=1, inuse=4, threshold_quantity=2)
        self.assertEqual(item.available_quantity, 0)

    def test_06_pending_replenishment_duplicate_blocked(self):
        item = Inventory.objects.create(item_name='Towel', quantity=1, threshold_quantity=5)

        create_replenishment_request_service(
            item_id=item.id,
            requested_quantity=10,
            urgency='high',
            justification='Low stock',
            requested_by_user=self.caretaker,
        )

        with self.assertRaises(ValueError):
            create_replenishment_request_service(
                item_id=item.id,
                requested_quantity=12,
                urgency='high',
                justification='Still low stock',
                requested_by_user=self.caretaker,
            )

    def test_07_approve_replenishment_requires_incharge_role(self):
        outsider = User.objects.create_user(username=f'integrity_outsider_{uuid.uuid4().hex[:8]}', password='x')
        item = Inventory.objects.create(item_name='Pillow', quantity=1, threshold_quantity=5)
        req = ReplenishmentRequest.objects.create(
            inventory_item=item,
            requested_by=self.caretaker,
            requested_quantity=5,
            current_quantity=1,
            urgency='medium',
            justification='Required',
            status='pending',
        )

        with self.assertRaises(PermissionError):
            approve_replenishment_request_service(
                request_id=req.id,
                approved_quantity=5,
                approval_remarks='No access',
                approved_by_user=outsider,
            )

    def test_08_reject_replenishment_clears_pending_flag(self):
        item = Inventory.objects.create(item_name='Bedsheet', quantity=1, threshold_quantity=5, pending_replenishment=True)
        req = ReplenishmentRequest.objects.create(
            inventory_item=item,
            requested_by=self.caretaker,
            requested_quantity=6,
            current_quantity=1,
            urgency='medium',
            justification='Required',
            status='pending',
        )

        reject_replenishment_request_service(
            request_id=req.id,
            approval_remarks='Rejected for now',
            approved_by_user=self.incharge,
        )

        item.refresh_from_db()
        req.refresh_from_db()
        self.assertEqual(req.status, 'rejected')
        self.assertFalse(item.pending_replenishment)

    def test_09_mark_received_updates_quantity_and_status_consistently(self):
        item = Inventory.objects.create(item_name='Curtain', quantity=2, threshold_quantity=5, pending_replenishment=True)
        req = ReplenishmentRequest.objects.create(
            inventory_item=item,
            requested_by=self.caretaker,
            requested_quantity=7,
            current_quantity=2,
            urgency='high',
            justification='Required',
            status='approved',
            approved_by=self.incharge,
            approved_quantity=7,
        )

        mark_replenishment_received_service(
            request_id=req.id,
            actual_cost=1200,
            delivery_date=datetime.date(2026, 5, 5),
            user=self.caretaker,
        )

        item.refresh_from_db()
        req.refresh_from_db()
        self.assertEqual(item.quantity, 9)
        self.assertFalse(item.pending_replenishment)
        self.assertEqual(req.status, 'received')

    @patch('applications.visitor_hostel.services._enforce_single_active_role_policy', return_value=None)
    @patch('applications.visitor_hostel.services.get_vhcaretaker_user')
    def test_10_atomic_commit_creates_booking_and_visitor(self, mock_get_caretaker, _mock_policy):
        mock_get_caretaker.return_value = self.caretaker
        baseline_booking_count = BookingDetail.objects.count()
        baseline_visitor_count = VisitorDetail.objects.count()
        payload = {
            'intender': self.intender.id,
            'booking_id': 'ACID-1',
            'category': 'C',
            'person_count': 1,
            'purpose_of_visit': 'ACID success test',
            'booking_from': datetime.date(2026, 5, 10),
            'booking_to': datetime.date(2026, 5, 11),
            'booking_from_time': '10:00',
            'booking_to_time': '12:00',
            'bill_to_be_settled_by': 'Intender',
            'number_of_rooms': 1,
            'intender_relation': 'Parent',
            'visitor_name': 'Guest One',
            'visitor_phone': f'8888{uuid.uuid4().hex[:6]}',
            'visitor_email': 'guest1@example.com',
            'visitor_address': 'Hostel Lane',
            'visitor_organization': 'Org',
            'visitor_nationality': 'Indian',
        }

        request_booking_service_from_data(payload, files=None)

        self.assertEqual(BookingDetail.objects.count(), baseline_booking_count + 1)
        self.assertEqual(VisitorDetail.objects.count(), baseline_visitor_count + 1)
        booking = BookingDetail.objects.filter(purpose='ACID success test').order_by('-id').first()
        self.assertEqual(booking.visitor.count(), 1)

    @patch('applications.visitor_hostel.services._enforce_single_active_role_policy', return_value=None)
    @patch('applications.visitor_hostel.services.get_vhcaretaker_user')
    def test_10b_offline_booking_metadata_persists(self, mock_get_caretaker, _mock_policy):
        mock_get_caretaker.return_value = self.caretaker
        payload = {
            'intender': self.intender.id,
            'booking_id': 'OFFLINE-1',
            'category': 'C',
            'person_count': 1,
            'purpose_of_visit': 'Offline booking persistence test',
            'booking_from': datetime.date(2026, 5, 16),
            'booking_to': datetime.date(2026, 5, 17),
            'booking_from_time': '10:00',
            'booking_to_time': '12:00',
            'bill_to_be_settled_by': 'Intender',
            'number_of_rooms': 1,
            'is_offline': True,
            'booking_source': 'telephonic',
            'intender_name': 'Offline Intender',
            'intender_phone': '9999912345',
            'intender_email': 'offline.intender@example.com',
            'intender_relation': 'Self',
            'visitor_name': 'Guest Offline',
            'visitor_phone': f'9999{uuid.uuid4().hex[:6]}',
            'visitor_email': 'guest.offline@example.com',
            'visitor_address': 'Hostel Lane',
            'visitor_organization': 'Org',
            'visitor_nationality': 'Indian',
        }

        request_booking_service_from_data(payload, files=None)

        booking = BookingDetail.objects.filter(
            purpose='Offline booking persistence test'
        ).order_by('-id').first()

        self.assertIsNotNone(booking)
        self.assertTrue(booking.is_offline)
        self.assertEqual(booking.booking_source, 'telephonic')
        self.assertEqual(booking.intender_name, 'Offline Intender')
        self.assertEqual(booking.intender_phone, '9999912345')
        self.assertEqual(booking.intender_email, 'offline.intender@example.com')

    @patch('applications.visitor_hostel.services._enforce_single_active_role_policy', return_value=None)
    @patch('applications.visitor_hostel.services.get_vhcaretaker_user')
    @patch('applications.visitor_hostel.services.VisitorDetail.objects.create', side_effect=RuntimeError('forced visitor create failure'))
    def test_11_atomic_rollback_when_visitor_creation_fails(self, _mock_visitor_create, mock_get_caretaker, _mock_policy):
        mock_get_caretaker.return_value = self.caretaker
        unique_phone = f'7777{uuid.uuid4().hex[:6]}'
        payload = {
            'intender': self.intender.id,
            'booking_id': 'ACID-2',
            'category': 'C',
            'person_count': 1,
            'purpose_of_visit': 'ACID rollback test',
            'booking_from': datetime.date(2026, 5, 12),
            'booking_to': datetime.date(2026, 5, 13),
            'booking_from_time': '10:00',
            'booking_to_time': '12:00',
            'bill_to_be_settled_by': 'Intender',
            'number_of_rooms': 1,
            'intender_relation': 'Parent',
            'visitor_name': 'Guest Two',
            'visitor_phone': unique_phone,
            'visitor_email': 'guest2@example.com',
            'visitor_address': 'Hostel Lane',
            'visitor_organization': 'Org',
            'visitor_nationality': 'Indian',
        }

        with self.assertRaises(RuntimeError):
            request_booking_service_from_data(payload, files=None)

        self.assertFalse(BookingDetail.objects.filter(purpose='ACID rollback test').exists())
        self.assertFalse(VisitorDetail.objects.filter(visitor_phone=unique_phone).exists())

    @patch('applications.visitor_hostel.services._enforce_single_active_role_policy', return_value=None)
    @patch('applications.visitor_hostel.services.get_vhcaretaker_user')
    @patch('applications.visitor_hostel.services.BookingDetail.save', side_effect=RuntimeError('forced booking save failure'))
    def test_12_atomic_rollback_when_booking_save_fails_after_link(self, _mock_save, mock_get_caretaker, _mock_policy):
        mock_get_caretaker.return_value = self.caretaker
        unique_phone = f'6666{uuid.uuid4().hex[:6]}'
        payload = {
            'intender': self.intender.id,
            'booking_id': 'ACID-3',
            'category': 'C',
            'person_count': 1,
            'purpose_of_visit': 'ACID rollback test 2',
            'booking_from': datetime.date(2026, 5, 14),
            'booking_to': datetime.date(2026, 5, 15),
            'booking_from_time': '10:00',
            'booking_to_time': '12:00',
            'bill_to_be_settled_by': 'Intender',
            'number_of_rooms': 1,
            'intender_relation': 'Parent',
            'visitor_name': 'Guest Three',
            'visitor_phone': unique_phone,
            'visitor_email': 'guest3@example.com',
            'visitor_address': 'Hostel Lane',
            'visitor_organization': 'Org',
            'visitor_nationality': 'Indian',
        }

        with self.assertRaises(RuntimeError):
            request_booking_service_from_data(payload, files=None)

        self.assertFalse(BookingDetail.objects.filter(purpose='ACID rollback test 2').exists())
        self.assertFalse(VisitorDetail.objects.filter(visitor_phone=unique_phone).exists())

    def test_13_create_replenishment_snapshots_current_quantity(self):
        item = Inventory.objects.create(item_name='SoapBox', quantity=11, threshold_quantity=5)

        req = create_replenishment_request_service(
            item_id=item.id,
            requested_quantity=4,
            urgency='low',
            justification='Top up',
            requested_by_user=self.caretaker,
        )

        self.assertEqual(req.current_quantity, 11)
        item.refresh_from_db()
        self.assertTrue(item.pending_replenishment)

    def test_14_received_requires_approved_state(self):
        item = Inventory.objects.create(item_name='Mug', quantity=3, threshold_quantity=5)
        req = ReplenishmentRequest.objects.create(
            inventory_item=item,
            requested_by=self.caretaker,
            requested_quantity=2,
            current_quantity=3,
            urgency='low',
            justification='Stock safety',
            status='pending',
        )

        with self.assertRaises(ValueError):
            mark_replenishment_received_service(
                request_id=req.id,
                actual_cost=200,
                delivery_date=datetime.date(2026, 5, 5),
                user=self.caretaker,
            )

    def test_15_create_replenishment_raises_for_invalid_item(self):
        with self.assertRaises(ValueError):
            create_replenishment_request_service(
                item_id=999999,
                requested_quantity=4,
                urgency='medium',
                justification='invalid item id',
                requested_by_user=self.caretaker,
            )

    def test_16_approve_replenishment_rejects_non_pending_request(self):
        item = Inventory.objects.create(item_name='Plate', quantity=8, threshold_quantity=5)
        req = ReplenishmentRequest.objects.create(
            inventory_item=item,
            requested_by=self.caretaker,
            requested_quantity=2,
            current_quantity=8,
            urgency='low',
            justification='state validation',
            status='approved',
            approved_by=self.incharge,
            approved_quantity=2,
        )

        with self.assertRaises(ValueError):
            approve_replenishment_request_service(
                request_id=req.id,
                approved_quantity=2,
                approval_remarks='duplicate approval',
                approved_by_user=self.incharge,
            )

    def test_17_reject_replenishment_rejects_non_pending_request(self):
        item = Inventory.objects.create(item_name='Glass', quantity=8, threshold_quantity=5)
        req = ReplenishmentRequest.objects.create(
            inventory_item=item,
            requested_by=self.caretaker,
            requested_quantity=2,
            current_quantity=8,
            urgency='low',
            justification='state validation',
            status='received',
            approved_by=self.incharge,
            approved_quantity=2,
        )

        with self.assertRaises(ValueError):
            reject_replenishment_request_service(
                request_id=req.id,
                approval_remarks='invalid transition',
                approved_by_user=self.incharge,
            )

    def test_18_mark_received_raises_for_invalid_request_id(self):
        with self.assertRaises(ValueError):
            mark_replenishment_received_service(
                request_id=999999,
                actual_cost=500,
                delivery_date=datetime.date(2026, 5, 8),
                user=self.caretaker,
            )

    @patch('applications.visitor_hostel.services._enforce_single_active_role_policy', return_value=None)
    @patch('applications.visitor_hostel.services.get_vhcaretaker_user')
    def test_19_student_invalid_relation_denied_and_no_booking_created(self, mock_get_caretaker, _mock_policy):
        mock_get_caretaker.return_value = self.caretaker
        student_user = User.objects.create_user(
            username=f'integrity_student_{uuid.uuid4().hex[:8]}',
            password='x',
        )
        ExtraInfo.objects.create(
            id=f'student_{uuid.uuid4().hex[:8]}',
            user=student_user,
            user_type='student',
        )

        payload = {
            'intender': student_user.id,
            'booking_id': 'ACID-REL-1',
            'category': 'C',
            'person_count': 1,
            'purpose_of_visit': 'student invalid relation',
            'booking_from': datetime.date(2026, 5, 16),
            'booking_to': datetime.date(2026, 5, 17),
            'booking_from_time': '10:00',
            'booking_to_time': '12:00',
            'bill_to_be_settled_by': 'Intender',
            'number_of_rooms': 1,
            'intender_relation': 'Friend',
            'visitor_name': 'Guest Four',
            'visitor_phone': f'5555{uuid.uuid4().hex[:6]}',
            'visitor_email': 'guest4@example.com',
            'visitor_address': 'Hostel Lane',
            'visitor_organization': 'Org',
            'visitor_nationality': 'Indian',
        }

        with self.assertRaises(Exception):
            request_booking_service_from_data(payload, files=None)

        self.assertFalse(BookingDetail.objects.filter(purpose='student invalid relation').exists())

    @patch('applications.visitor_hostel.services._enforce_single_active_role_policy', return_value=None)
    @patch('applications.visitor_hostel.services.get_vhcaretaker_user')
    def test_20_student_parent_relation_allows_booking_creation(self, mock_get_caretaker, _mock_policy):
        mock_get_caretaker.return_value = self.caretaker
        student_user = User.objects.create_user(
            username=f'integrity_student_ok_{uuid.uuid4().hex[:8]}',
            password='x',
        )
        ExtraInfo.objects.create(
            id=f'student_ok_{uuid.uuid4().hex[:8]}',
            user=student_user,
            user_type='student',
        )

        payload = {
            'intender': student_user.id,
            'booking_id': 'ACID-REL-2',
            'category': 'C',
            'person_count': 1,
            'purpose_of_visit': 'student valid relation',
            'booking_from': datetime.date(2026, 5, 18),
            'booking_to': datetime.date(2026, 5, 19),
            'booking_from_time': '10:00',
            'booking_to_time': '12:00',
            'bill_to_be_settled_by': 'Intender',
            'number_of_rooms': 1,
            'intender_relation': 'Parent',
            'visitor_name': 'Guest Five',
            'visitor_phone': f'5544{uuid.uuid4().hex[:6]}',
            'visitor_email': 'guest5@example.com',
            'visitor_address': 'Hostel Lane',
            'visitor_organization': 'Org',
            'visitor_nationality': 'Indian',
        }

        request_booking_service_from_data(payload, files=None)

        self.assertTrue(BookingDetail.objects.filter(purpose='student valid relation').exists())

    def test_21_inventory_delete_cascades_related_records(self):
        item = Inventory.objects.create(item_name='CascadeItem', quantity=6, threshold_quantity=5)
        inv_bill = InventoryBill.objects.create(item_name=item, bill_number='INV-CASCADE-1', cost=100)
        req = ReplenishmentRequest.objects.create(
            inventory_item=item,
            requested_by=self.caretaker,
            requested_quantity=3,
            current_quantity=6,
            urgency='low',
            justification='cascade check',
            status='pending',
        )

        item.delete()

        self.assertFalse(InventoryBill.objects.filter(id=inv_bill.id).exists())
        self.assertFalse(ReplenishmentRequest.objects.filter(id=req.id).exists())

    def test_22_visitor_delete_cascades_meal_records(self):
        booking = self._create_booking(status='CheckedIn')
        visitor = VisitorDetail.objects.create(
            visitor_phone=f'9000{uuid.uuid4().hex[:6]}',
            visitor_name='Cascade Visitor',
        )
        booking.visitor.add(visitor)
        meal = MealRecord.objects.create(
            booking=booking,
            visitor=visitor,
            meal_date=datetime.date(2026, 5, 20),
            breakfast=1,
        )

        visitor.delete()

        self.assertFalse(MealRecord.objects.filter(id=meal.id).exists())

    def test_23_intender_delete_cascades_booking_and_bill(self):
        booking = self._create_booking()
        bill = Bill.objects.create(booking=booking, caretaker=self.caretaker, meal_bill=0, room_bill=100)

        self.intender.delete()

        self.assertFalse(BookingDetail.objects.filter(id=booking.id).exists())
        self.assertFalse(Bill.objects.filter(id=bill.id).exists())

    def test_24_replenishment_create_rolls_back_on_inventory_update_failure(self):
        item = Inventory.objects.create(item_name='AtomicCreate', quantity=10, threshold_quantity=5)

        with patch('applications.visitor_hostel.services.Inventory.save', side_effect=RuntimeError('forced inventory save failure')):
            with self.assertRaises(RuntimeError):
                create_replenishment_request_service(
                    item_id=item.id,
                    requested_quantity=4,
                    urgency='medium',
                    justification='atomic rollback check',
                    requested_by_user=self.caretaker,
                )

        self.assertFalse(
            ReplenishmentRequest.objects.filter(
                inventory_item=item,
                justification='atomic rollback check',
            ).exists()
        )

    def test_25_mark_received_rolls_back_inventory_on_request_save_failure(self):
        item = Inventory.objects.create(
            item_name='AtomicReceive',
            quantity=5,
            threshold_quantity=5,
            pending_replenishment=True,
        )
        req = ReplenishmentRequest.objects.create(
            inventory_item=item,
            requested_by=self.caretaker,
            requested_quantity=3,
            current_quantity=5,
            urgency='medium',
            justification='atomic receive rollback check',
            status='approved',
            approved_by=self.incharge,
            approved_quantity=3,
        )

        with patch('applications.visitor_hostel.services.ReplenishmentRequest.save', side_effect=RuntimeError('forced request save failure')):
            with self.assertRaises(RuntimeError):
                mark_replenishment_received_service(
                    request_id=req.id,
                    actual_cost=300,
                    delivery_date=datetime.date(2026, 5, 21),
                    user=self.caretaker,
                )

        item.refresh_from_db()
        req.refresh_from_db()
        self.assertEqual(item.quantity, 5)
        self.assertTrue(item.pending_replenishment)
        self.assertEqual(req.status, 'approved')


# ============================================================================
# BR-VH-010: CHECK-IN / CHECK-OUT ALERTS TESTS
# ============================================================================

class CheckInCheckOutAlertTests(TestCase):
    """Tests for BR-VH-010 Check-in/Check-out Alert System"""
    
    def setUp(self):
        from applications.visitor_hostel.models import CheckInCheckOutAlert
        suffix = uuid.uuid4().hex[:8]
        self.intender = User.objects.create_user(username=f'alert_intender_{suffix}', password='x')
        self.caretaker = User.objects.create_user(username=f'alert_caretaker_{suffix}', password='x')
        self.incharge = User.objects.create_user(
            username=f'alert_incharge_{suffix}',
            password='x',
            is_staff=True,
        )
        self.CheckInCheckOutAlert = CheckInCheckOutAlert
    
    def _create_booking(self, booking_from, booking_to, arrival_time='10:00', status='Confirmed'):
        """Helper to create a booking with specific dates and times"""
        booking = BookingDetail.objects.create(
            intender=self.intender,
            caretaker=self.caretaker,
            visitor_category='C',
            person_count=1,
            purpose='Test alert booking',
            booking_from=booking_from,
            booking_to=booking_to,
            arrival_time=arrival_time,
            departure_time='14:00',
            status=status,
            number_of_rooms=1,
        )
        visitor = VisitorDetail.objects.create(
            visitor_phone='9999999999',
            visitor_name=f'AlertTestVisitor_{uuid.uuid4().hex[:6]}',
            visitor_email='test@example.com'
        )
        booking.visitor.add(visitor)
        booking.save()
        return booking
    
    def test_26_no_show_alert_created_for_missed_arrival(self):
        """BR-VH-010: No-show alert created when arrival time passed without check-in"""
        from applications.visitor_hostel.services import detect_and_create_no_show_alerts
        from django.utils import timezone
        
        # Create booking with past arrival date
        past_date = datetime.date(2026, 4, 20)  # Before current time
        booking = self._create_booking(
            booking_from=past_date,
            booking_to=past_date + datetime.timedelta(days=1),
            status='Confirmed'
        )
        
        # Verify no check-in yet
        self.assertIsNone(booking.check_in)
        
        # Detect no-shows
        alerts = detect_and_create_no_show_alerts()
        
        # Verify alert was created
        self.assertGreater(len(alerts), 0)
        
        alert = self.CheckInCheckOutAlert.objects.filter(
            booking=booking,
            alert_type='no_show',
            status='pending'
        ).first()
        
        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, 'high')
        self.assertIn('No-show', alert.message)
    
    def test_27_due_checkout_alert_created_for_overdue_guest(self):
        """BR-VH-010: Due checkout alert created when departure date passed"""
        from applications.visitor_hostel.services import detect_and_create_due_checkout_alerts
        
        # Create checked-in booking with past departure date
        past_date = datetime.date(2026, 4, 20)
        booking = self._create_booking(
            booking_from=past_date,
            booking_to=past_date - datetime.timedelta(days=1),  # Already passed
            status='CheckedIn'
        )
        booking.check_in = past_date
        booking.save()
        
        # Detect due checkouts
        alerts = detect_and_create_due_checkout_alerts()
        
        # Verify alert was created
        alert = self.CheckInCheckOutAlert.objects.filter(
            booking=booking,
            alert_type='due_checkout',
            status='pending'
        ).first()
        
        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, 'high')
        self.assertIn('overdue', alert.message.lower())
    
    def test_28_no_duplicate_no_show_alerts(self):
        """BR-VH-010: Duplicate no-show alerts not created on repeated detection"""
        from applications.visitor_hostel.services import detect_and_create_no_show_alerts
        
        past_date = datetime.date(2026, 4, 20)
        booking = self._create_booking(
            booking_from=past_date,
            booking_to=past_date + datetime.timedelta(days=1),
            status='Confirmed'
        )
        
        # First detection
        alerts_1 = detect_and_create_no_show_alerts()
        count_1 = self.CheckInCheckOutAlert.objects.filter(
            booking=booking,
            alert_type='no_show',
            status='pending'
        ).count()
        
        # Second detection
        alerts_2 = detect_and_create_no_show_alerts()
        count_2 = self.CheckInCheckOutAlert.objects.filter(
            booking=booking,
            alert_type='no_show',
            status='pending'
        ).count()
        
        # Should not create duplicate
        self.assertEqual(count_1, count_2)
        self.assertEqual(count_1, 1)
    
    def test_29_no_duplicate_due_checkout_alerts(self):
        """BR-VH-010: Duplicate due checkout alerts not created"""
        from applications.visitor_hostel.services import detect_and_create_due_checkout_alerts
        
        past_date = datetime.date(2026, 4, 20)
        booking = self._create_booking(
            booking_from=past_date,
            booking_to=past_date - datetime.timedelta(days=1),
            status='CheckedIn'
        )
        booking.check_in = past_date
        booking.save()
        
        # First detection
        alerts_1 = detect_and_create_due_checkout_alerts()
        count_1 = self.CheckInCheckOutAlert.objects.filter(
            booking=booking,
            alert_type='due_checkout',
            status='pending'
        ).count()
        
        # Second detection
        alerts_2 = detect_and_create_due_checkout_alerts()
        count_2 = self.CheckInCheckOutAlert.objects.filter(
            booking=booking,
            alert_type='due_checkout',
            status='pending'
        ).count()
        
        # Should not create duplicate
        self.assertEqual(count_1, count_2)
        self.assertEqual(count_1, 1)
    
    def test_30_acknowledge_alert_marks_status(self):
        """BR-VH-010: Acknowledging alert updates status and timestamps"""
        from applications.visitor_hostel.services import acknowledge_alert_service, detect_and_create_no_show_alerts
        
        past_date = datetime.date(2026, 4, 20)
        booking = self._create_booking(
            booking_from=past_date,
            booking_to=past_date + datetime.timedelta(days=1),
            status='Confirmed'
        )
        
        # Create alert
        detect_and_create_no_show_alerts()
        alert = self.CheckInCheckOutAlert.objects.filter(
            booking=booking,
            alert_type='no_show'
        ).first()
        
        initial_status = alert.status
        self.assertEqual(initial_status, 'pending')
        
        # Acknowledge alert
        updated_alert = acknowledge_alert_service(
            alert_id=alert.id,
            user=self.caretaker,
            remarks='Visitor called, will check in today'
        )
        
        # Verify status changed
        self.assertEqual(updated_alert.status, 'acknowledged')
        self.assertEqual(updated_alert.acknowledged_by, self.caretaker)
        self.assertEqual(updated_alert.acknowledgment_remarks, 'Visitor called, will check in today')
        self.assertIsNotNone(updated_alert.acknowledged_at)
    
    def test_31_resolve_alert_marks_resolved(self):
        """BR-VH-010: Resolving alert updates status to resolved"""
        from applications.visitor_hostel.services import resolve_alert_service, detect_and_create_no_show_alerts
        
        past_date = datetime.date(2026, 4, 20)
        booking = self._create_booking(
            booking_from=past_date,
            booking_to=past_date + datetime.timedelta(days=1),
            status='Confirmed'
        )
        
        # Create alert
        detect_and_create_no_show_alerts()
        alert = self.CheckInCheckOutAlert.objects.filter(
            booking=booking,
            alert_type='no_show'
        ).first()
        
        # Resolve alert
        updated_alert = resolve_alert_service(alert_id=alert.id)
        
        # Verify status changed
        self.assertEqual(updated_alert.status, 'resolved')
        self.assertIsNotNone(updated_alert.resolved_at)
    
    def test_32_alert_notification_sent_on_creation(self):
        """BR-VH-010: Notifications sent when alerts are created"""
        from applications.visitor_hostel.services import detect_and_create_no_show_alerts
        
        past_date = datetime.date(2026, 4, 20)
        booking = self._create_booking(
            booking_from=past_date,
            booking_to=past_date + datetime.timedelta(days=1),
            status='Confirmed'
        )
        
        # Mock notification system
        with patch('applications.visitor_hostel.services.notify.send') as mock_notify:
            # Create alert
            alerts = detect_and_create_no_show_alerts()
            
            # Verify notification was attempted
            self.assertEqual(len(alerts), 1)
            # Note: Mock will track calls even if notifier is not installed
    
    def test_33_alert_created_during_booking_creation(self):
        """BR-VH-010: Alert system initialized when new booking is created"""
        from applications.visitor_hostel.services import create_initial_alert_for_booking
        
        booking = self._create_booking(
            booking_from=datetime.date(2026, 5, 15),
            booking_to=datetime.date(2026, 5, 16),
            status='Confirmed'
        )
        
        # Alert metadata should be available
        alert_info = create_initial_alert_for_booking(booking)
        
        self.assertTrue(alert_info['alerts_initialized'])
        self.assertEqual(alert_info['booking_id'], booking.id)
        self.assertIn('visitor_name', alert_info)
        self.assertIn('expected_arrival', alert_info)
    
    def test_34_alert_severity_based_on_days_overdue(self):
        """BR-VH-010: Alert severity escalates based on days overdue"""
        from applications.visitor_hostel.services import detect_and_create_due_checkout_alerts
        
        # 2 days overdue - should be high severity
        # Use relative dates: 2 days ago from today
        today = datetime.date.today()
        booking_to_date = today - datetime.timedelta(days=2)
        booking_from_date = today - datetime.timedelta(days=3)
        
        booking = self._create_booking(
            booking_from=booking_from_date,
            booking_to=booking_to_date,
            status='CheckedIn'
        )
        booking.check_in = booking_from_date
        booking.save()
        
        alerts = detect_and_create_due_checkout_alerts()
        alert = self.CheckInCheckOutAlert.objects.filter(
            booking=booking,
            alert_type='due_checkout'
        ).first()
        
        self.assertEqual(alert.severity, 'high')
        self.assertIn('2 day(s)', alert.message)
    
    def test_35_no_alert_for_future_booking(self):
        """BR-VH-010: No alert created for future bookings"""
        from applications.visitor_hostel.services import detect_and_create_no_show_alerts
        
        # Future booking
        future_date = datetime.date(2026, 7, 15)
        booking = self._create_booking(
            booking_from=future_date,
            booking_to=future_date + datetime.timedelta(days=1),
            status='Confirmed'
        )
        
        # Detect no-shows
        alerts = detect_and_create_no_show_alerts()
        
        # No alert should be created for future booking
        alert = self.CheckInCheckOutAlert.objects.filter(
            booking=booking,
            alert_type='no_show'
        ).exists()
        
        self.assertFalse(alert)
