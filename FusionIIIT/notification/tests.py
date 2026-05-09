from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from notification.views import (
    leave_module_notif,
    placement_cell_notif,
    academics_module_notif,
    office_module_notif,
    central_mess_notif,
    placement_cellNotif,
    visitors_hostel_notif,
    healthcare_center_notif,
    file_tracking_notif,
    scholarship_portal_notif,
    complaint_system_notif,
    office_dean_PnD_notif,
    office_module_DeanS_notif,
    gymkhana_voting,
    gymkhana_session,
)


class NotificationTestCase(TestCase):
    """Base test case for notification functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sender = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.recipient = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )


class LeaveModuleNotifTest(NotificationTestCase):
    """Test cases for leave_module_notif function"""
    
    @patch('notification.views.notify.send')
    def test_leave_applied_notification(self, mock_notify):
        """Test notification when leave is applied"""
        leave_module_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='leave_applied'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertEqual(call_kwargs['sender'], self.sender)
        self.assertEqual(call_kwargs['recipient'], self.recipient)
        self.assertEqual(call_kwargs['module'], 'Leave Module')
        self.assertEqual(call_kwargs['url'], 'leave:leave')
        self.assertIn('successfully submitted', call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_request_accepted_notification(self, mock_notify):
        """Test notification when request is accepted"""
        leave_module_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='request_accepted'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('accepted', call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_request_declined_notification(self, mock_notify):
        """Test notification when request is declined"""
        leave_module_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='request_declined'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('declined', call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_leave_accepted_notification(self, mock_notify):
        """Test notification when leave is accepted"""
        leave_module_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='leave_accepted'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('accepted', call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_leave_forwarded_notification(self, mock_notify):
        """Test notification when leave is forwarded"""
        leave_module_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='leave_forwarded'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('forwarded', call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_leave_rejected_notification(self, mock_notify):
        """Test notification when leave is rejected"""
        leave_module_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='leave_rejected'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('rejected', call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_offline_leave_notification(self, mock_notify):
        """Test notification for offline leave update"""
        leave_module_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='offline_leave'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('offline', call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_replacement_request_notification(self, mock_notify):
        """Test notification for replacement request"""
        leave_module_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='replacement_request'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('replacement', call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_leave_request_notification(self, mock_notify):
        """Test notification for leave request"""
        leave_module_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='leave_request'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('leave request', call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_leave_withdrawn_notification(self, mock_notify):
        """Test notification when leave is withdrawn"""
        test_date = '2024-01-15'
        leave_module_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='leave_withdrawn',
            date=test_date
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('withdrawn', call_kwargs['verb'])
        self.assertIn(test_date, call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_replacement_cancel_notification(self, mock_notify):
        """Test notification when replacement is cancelled"""
        test_date = '2024-01-15'
        leave_module_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='replacement_cancel',
            date=test_date
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('cancelled', call_kwargs['verb'])
        self.assertIn(test_date, call_kwargs['verb'])


class PlacementCellNotifTest(NotificationTestCase):
    """Test cases for placement_cell_notif and placement_cellNotif functions"""
    
    @patch('notification.views.notify.send')
    def test_placement_cell_notification(self, mock_notify):
        """Test basic placement cell notification"""
        placement_cell_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='test_type'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertEqual(call_kwargs['sender'], self.sender)
        self.assertEqual(call_kwargs['recipient'], self.recipient)
        self.assertEqual(call_kwargs['module'], 'Placement Cell')
        self.assertEqual(call_kwargs['url'], 'placement:placement')
    
    @patch('notification.views.notify.send')
    def test_placement_cellNotif_notification(self, mock_notify):
        """Test placement_cellNotif function"""
        placement_cellNotif(
            sender=self.sender,
            recipient=self.recipient,
            type='test_type'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertEqual(call_kwargs['module'], 'Placement Cell')


class AcademicsModuleNotifTest(NotificationTestCase):
    """Test cases for academics_module_notif function"""
    
    @patch('notification.views.notify.send')
    def test_academics_notification(self, mock_notify):
        """Test academics module notification"""
        test_message = 'Grade has been uploaded'
        academics_module_notif(
            sender=self.sender,
            recipient=self.recipient,
            type=test_message
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertEqual(call_kwargs['sender'], self.sender)
        self.assertEqual(call_kwargs['recipient'], self.recipient)
        self.assertEqual(call_kwargs['module'], "Academic's Module")
        self.assertEqual(call_kwargs['verb'], test_message)


class OfficeModuleNotifTest(NotificationTestCase):
    """Test cases for office_module_notif function"""
    
    @patch('notification.views.notify.send')
    def test_office_module_notification(self, mock_notify):
        """Test office module notification"""
        office_module_notif(
            sender=self.sender,
            recipient=self.recipient
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertEqual(call_kwargs['sender'], self.sender)
        self.assertEqual(call_kwargs['recipient'], self.recipient)
        self.assertEqual(call_kwargs['url'], 'office_module:officeOfRegistrar')
        self.assertEqual(call_kwargs['verb'], 'New file received')


class CentralMessNotifTest(NotificationTestCase):
    """Test cases for central_mess_notif function"""
    
    @patch('notification.views.notify.send')
    def test_feedback_submitted_notification(self, mock_notify):
        """Test notification when feedback is submitted"""
        central_mess_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='feedback_submitted'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertEqual(call_kwargs['module'], 'Central Mess')
        self.assertIn('submitted', call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_menu_change_accepted_notification(self, mock_notify):
        """Test notification when menu change is accepted"""
        central_mess_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='menu_change_accepted'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('approved', call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_leave_request_notification(self, mock_notify):
        """Test mess leave request notification"""
        test_message = 'Leave request approved'
        central_mess_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='leave_request',
            message=test_message
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertEqual(call_kwargs['verb'], test_message)
    
    @patch('notification.views.notify.send')
    def test_special_request_notification(self, mock_notify):
        """Test special food request notification"""
        message = 'approved'
        central_mess_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='special_request',
            message=message
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('special food request', call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_added_committee_notification(self, mock_notify):
        """Test notification when added to mess committee"""
        central_mess_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='added_committee'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('committee', call_kwargs['verb'])


class VisitorsHostelNotifTest(NotificationTestCase):
    """Test cases for visitors_hostel_notif function"""
    
    @patch('notification.views.notify.send')
    def test_booking_confirmation_notification(self, mock_notify):
        """Test booking confirmation notification"""
        visitors_hostel_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='booking_confirmation'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertEqual(call_kwargs['module'], "Visitor's Hostel")
        self.assertIn('confirmed', call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_booking_rejection_notification(self, mock_notify):
        """Test booking rejection notification"""
        visitors_hostel_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='booking_rejected'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('rejected', call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_booking_forwarded_notification(self, mock_notify):
        """Test booking forwarded notification"""
        visitors_hostel_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='booking_forwarded'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('Forwarded', call_kwargs['verb'])


class HealthcareCenterNotifTest(NotificationTestCase):
    """Test cases for healthcare_center_notif function"""
    
    @patch('notification.views.notify.send')
    def test_appointment_booking_notification(self, mock_notify):
        """Test appointment booking notification"""
        healthcare_center_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='appoint',
            message=None
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertEqual(call_kwargs['module'], 'Healthcare Center')
        self.assertIn('booked', call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_ambulance_request_notification(self, mock_notify):
        """Test ambulance request notification"""
        healthcare_center_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='amb_request',
            message=None
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('Ambulance', call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_prescription_notification(self, mock_notify):
        """Test prescription notification"""
        healthcare_center_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='presc',
            message=None
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('medicine', call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_medical_relief_approved_notification(self, mock_notify):
        """Test medical relief approved notification"""
        healthcare_center_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='rel_approved',
            message=None
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('approved', call_kwargs['verb'])


class FileTrackingNotifTest(NotificationTestCase):
    """Test cases for file_tracking_notif function"""
    
    @patch('notification.views.notify.send')
    def test_file_tracking_notification(self, mock_notify):
        """Test file tracking notification"""
        test_title = 'New document received'
        file_tracking_notif(
            sender=self.sender,
            recipient=self.recipient,
            title=test_title
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertEqual(call_kwargs['module'], 'File Tracking')
        self.assertEqual(call_kwargs['url'], 'filetracking:inward')
        self.assertEqual(call_kwargs['verb'], test_title)


class ScholarshipPortalNotifTest(NotificationTestCase):
    """Test cases for scholarship_portal_notif function"""
    
    @patch('notification.views.notify.send')
    def test_award_invitation_notification(self, mock_notify):
        """Test award invitation notification"""
        scholarship_portal_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='award_merit_scholarship'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertEqual(call_kwargs['module'], 'Scholarship Portal')
        self.assertIn('Invitation', call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_mcm_accepted_notification(self, mock_notify):
        """Test MCM form accepted notification"""
        scholarship_portal_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='Accept_MCM'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('accepted', call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_gold_medal_accepted_notification(self, mock_notify):
        """Test Gold Medal form accepted notification"""
        scholarship_portal_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='Accept_Gold'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('Gold Medal', call_kwargs['verb'])
        self.assertIn('accepted', call_kwargs['verb'])


class ComplaintSystemNotifTest(NotificationTestCase):
    """Test cases for complaint_system_notif function"""
    
    @patch('notification.views.notify.send')
    def test_student_complaint_notification(self, mock_notify):
        """Test student complaint notification"""
        test_message = 'Complaint received'
        complaint_system_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='new_complaint',
            complaint_id='COMP001',
            student=1,
            message=test_message
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertEqual(call_kwargs['module'], 'Complaint System')
        self.assertEqual(call_kwargs['verb'], test_message)
        self.assertEqual(call_kwargs['description'], 'COMP001')
    
    @patch('notification.views.notify.send')
    def test_staff_complaint_notification(self, mock_notify):
        """Test staff complaint notification"""
        test_message = 'Complaint received'
        complaint_system_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='new_complaint',
            complaint_id='COMP002',
            student=0,
            message=test_message
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertEqual(call_kwargs['module'], 'Complaint System')


class OfficeDeanPnDNotifTest(NotificationTestCase):
    """Test cases for office_dean_PnD_notif function"""
    
    @patch('notification.views.notify.send')
    def test_requisition_filed_notification(self, mock_notify):
        """Test requisition filed notification"""
        office_dean_PnD_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='requisition_filed'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertEqual(call_kwargs['module'], 'Office of Dean PnD Module')
        self.assertIn('successfully submitted', call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_assignment_created_notification(self, mock_notify):
        """Test assignment created notification"""
        office_dean_PnD_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='assignment_created'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('created', call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_assignment_approved_notification(self, mock_notify):
        """Test assignment approved notification"""
        office_dean_PnD_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='assignment_approved'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('approved', call_kwargs['verb'])


class OfficeModuleDeanSNotifTest(NotificationTestCase):
    """Test cases for office_module_DeanS_notif function"""
    
    @patch('notification.views.notify.send')
    def test_hostel_allotment_notification(self, mock_notify):
        """Test hostel allotment notification"""
        office_module_DeanS_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='hostel_alloted'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertEqual(call_kwargs['module'], 'Office Module')
        self.assertIn('alloted', call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_budget_approved_notification(self, mock_notify):
        """Test budget approved notification"""
        office_module_DeanS_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='budget_approved'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('approved', call_kwargs['verb'])
    
    @patch('notification.views.notify.send')
    def test_club_approved_notification(self, mock_notify):
        """Test club approved notification"""
        office_module_DeanS_notif(
            sender=self.sender,
            recipient=self.recipient,
            type='club_approved'
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertIn('Club', call_kwargs['verb'])
        self.assertIn('approved', call_kwargs['verb'])


class GymkhanaVotingNotifTest(NotificationTestCase):
    """Test cases for gymkhana_voting function"""
    
    @patch('notification.views.notify.send')
    def test_voting_open_notification(self, mock_notify):
        """Test voting open notification"""
        title = 'President Election'
        desc = 'Election details'
        gymkhana_voting(
            sender=self.sender,
            recipient=self.recipient,
            type='voting_open',
            title=title,
            desc=desc
        )
        
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args[1]
        self.assertEqual(call_kwargs['module'], 'Gymkhana Module')
        self.assertIn(title, call_kwargs['verb'])
        self.assertEqual(call_kwargs['description'], desc)
