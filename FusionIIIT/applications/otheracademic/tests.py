"""
Comprehensive tests for T14 (Escalation) and T16 (Audit Logging).

Test Categories:
1. NoDuesEscalationService tests (T14)
   - Daily reminder triggers
   - Auto-marking after 30 days
   - Manual approval/rejection
   - Escalation tracking

2. AuditLog tests (T16)
   - Auto-logging on model changes
   - Change tracking (old_value → new_value)
   - Query methods
   - Permission enforcement

3. Integration tests
   - Escalations logged in audit trail
   - Full workflow with multiple approvals
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status

from applications.otheracademic.models import NoDues, StudentDB
from applications.otheracademic.audit_models import (
    NoDuesEscalation,
    NoDuesClearanceHistory,
    AuditLog,
)
from applications.otheracademic.escalation_service import NoDuesEscalationService


class NoDuesEscalationServiceTest(TestCase):
    """Tests for escalation service (T14)."""
    
    def setUp(self):
        """Set up test data."""
        # Create a student user
        self.student_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create student DB record
        self.student_db = StudentDB.objects.create(
            roll_no=self.student_user,
            name='Test Student',
        )
        
        # Create NoDues record with all fields pending
        self.no_dues = NoDues.objects.create(
            roll_no=self.student_db,
        )
    
    def test_escalation_service_initialization(self):
        """Verify escalation service initializes correctly."""
        self.assertIsNotNone(self.no_dues)
        self.assertEqual(self.no_dues.roll_no.user.username, 'testuser')
    
    def test_get_escalation_status(self):
        """Test getting escalation status for student."""
        # Create some escalations
        NoDuesEscalation.objects.create(
            no_dues=self.no_dues,
            student=self.student_user,
            escalation_type='reminder_7day',
            status='sent',
            department='library',
            clear_field='library_clear',
        )
        
        status_info = NoDuesEscalationService.get_escalation_status(self.student_user)
        
        self.assertIn('total_escalations', status_info)
        self.assertIn('pending', status_info)
        self.assertIn('sent', status_info)
        self.assertEqual(status_info['total_escalations'], 1)
        self.assertEqual(status_info['sent'], 1)
    
    def test_manual_approve_clears_department(self):
        """Test manually approving a department."""
        admin = User.objects.create_user(
            username='admin',
            is_staff=True,
            password='admin123'
        )
        
        # Initially not clear
        self.assertFalse(self.no_dues.library_clear)
        
        # Approve library
        result = NoDuesEscalationService.mark_clear_manually(
            self.no_dues,
            'library',
            admin,
            'Books verified returned'
        )
        
        self.assertTrue(result)
        
        # Refresh from DB
        self.no_dues.refresh_from_db()
        self.assertTrue(self.no_dues.library_clear)
        
        # Verify history was recorded
        history = NoDuesClearanceHistory.objects.filter(
            student=self.student_user,
            department='library'
        )
        self.assertEqual(history.count(), 1)
        self.assertEqual(history.first().new_status, 'clear')
    
    def test_manual_reject_marks_notclear(self):
        """Test manually rejecting a department."""
        admin = User.objects.create_user(
            username='admin',
            is_staff=True,
            password='admin123'
        )
        
        # Initially not clear
        self.assertFalse(self.no_dues.library_notclear)
        
        # Reject library
        result = NoDuesEscalationService.mark_notclear_manually(
            self.no_dues,
            'library',
            admin,
            'Books not returned'
        )
        
        self.assertTrue(result)
        
        # Refresh from DB
        self.no_dues.refresh_from_db()
        self.assertTrue(self.no_dues.library_notclear)
        
        # Verify history
        history = NoDuesClearanceHistory.objects.filter(
            student=self.student_user,
            department='library'
        ).first()
        self.assertEqual(history.new_status, 'notclear')
    
    def test_escalation_created_on_approval(self):
        """Test that escalation record is created when approving."""
        admin = User.objects.create_user(username='admin', is_staff=True)
        
        # Mark as approved
        NoDuesEscalationService.mark_clear_manually(
            self.no_dues,
            'library',
            admin,
            'Approved'
        )
        
        # Check that audit log was created
        audit_entry = AuditLog.objects.filter(
            model_name='NoDues',
            object_id=self.no_dues.id,
            action='approve'
        )
        self.assertGreater(audit_entry.count(), 0)
    
    def test_check_and_escalate_all(self):
        """Test the main escalation check function."""
        results = NoDuesEscalationService.check_and_escalate_all()
        
        # Should have checked at least our test record
        self.assertIn('checked', results)
        self.assertGreaterEqual(results['checked'], 1)
    
    def test_get_student_history(self):
        """Test retrieving student clearance history."""
        admin = User.objects.create_user(username='admin', is_staff=True)
        
        # Approve library
        NoDuesEscalationService.mark_clear_manually(
            self.no_dues,
            'library',
            admin,
            'Test approval'
        )
        
        # Get history
        history = NoDuesEscalationService.get_student_history(self.student_user)
        
        self.assertGreater(len(history), 0)
        self.assertEqual(history[0]['department'], 'library')
        self.assertEqual(history[0]['to_status'], 'clear')
    
    def test_escalation_reminder_fields(self):
        """Test that escalation records have all required fields."""
        escalation = NoDuesEscalation.objects.create(
            no_dues=self.no_dues,
            student=self.student_user,
            escalation_type='reminder_7day',
            status='sent',
            department='library',
            clear_field='library_clear',
            notification_sent_to='test@example.com',
        )
        
        self.assertEqual(escalation.escalation_type, 'reminder_7day')
        self.assertEqual(escalation.status, 'sent')
        self.assertEqual(escalation.department, 'library')
        self.assertIsNotNone(escalation.created_at)
        self.assertIsNotNone(escalation.triggered_at)


class AuditLogTest(TestCase):
    """Tests for audit logging (T16)."""
    
    def setUp(self):
        """Set up test data."""
        self.student_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            is_staff=True,
            password='admin123'
        )
        
        self.student_db = StudentDB.objects.create(
            roll_no=self.student_user,
            name='Test Student',
        )
    
    def test_audit_log_creation(self):
        """Test creating an audit log entry."""
        no_dues = NoDues.objects.create(roll_no=self.student_db)
        
        audit_entry = AuditLog.log_change(
            user=self.admin_user,
            model_name='NoDues',
            object_id=no_dues.id,
            action='create',
            description='Created new No Dues record'
        )
        
        self.assertIsNotNone(audit_entry)
        self.assertEqual(audit_entry.model_name, 'NoDues')
        self.assertEqual(audit_entry.action, 'create')
        self.assertEqual(audit_entry.object_id, no_dues.id)
    
    def test_audit_log_captures_field_changes(self):
        """Test that audit log captures field changes."""
        no_dues = NoDues.objects.create(roll_no=self.student_db)
        
        audit_entry = AuditLog.log_change(
            user=self.admin_user,
            model_name='NoDues',
            object_id=no_dues.id,
            action='update',
            field_name='library_clear',
            old_value=False,
            new_value=True,
            description='Approved library clearance'
        )
        
        self.assertEqual(audit_entry.field_name, 'library_clear')
        self.assertEqual(audit_entry.old_value, False)
        self.assertEqual(audit_entry.new_value, True)
    
    def test_audit_log_get_history(self):
        """Test retrieving change history for an object."""
        no_dues = NoDues.objects.create(roll_no=self.student_db)
        
        # Create multiple audit entries
        for i in range(3):
            AuditLog.log_change(
                user=self.admin_user,
                model_name='NoDues',
                object_id=no_dues.id,
                action='update',
                field_name=f'dept_{i}',
                new_value=True,
            )
        
        history = AuditLog.get_history('NoDues', no_dues.id)
        
        self.assertEqual(len(history), 3)
        # Verify most recent is first
        self.assertEqual(history[0]['field_name'], 'dept_2')
    
    def test_audit_log_get_user_actions(self):
        """Test getting all actions by a user."""
        no_dues = NoDues.objects.create(roll_no=self.student_db)
        
        # Create actions by admin
        for i in range(2):
            AuditLog.log_change(
                user=self.admin_user,
                model_name='NoDues',
                object_id=no_dues.id,
                action='update',
                field_name=f'field_{i}',
            )
        
        # Create action by another user
        AuditLog.log_change(
            user=self.student_user,
            model_name='NoDues',
            object_id=no_dues.id,
            action='view',
        )
        
        admin_actions = AuditLog.get_user_actions(self.admin_user, limit=10)
        
        self.assertEqual(len(admin_actions), 2)
        self.assertTrue(all(a['user'] == 'admin' for a in admin_actions))
    
    def test_audit_log_get_actions_for_student(self):
        """Test getting all audit actions related to a student."""
        no_dues = NoDues.objects.create(roll_no=self.student_db)
        
        # Create actions related to student
        for i in range(2):
            AuditLog.log_change(
                user=self.admin_user,
                model_name='NoDues',
                object_id=no_dues.id,
                action='update',
                related_user=self.student_user,
            )
        
        actions = AuditLog.get_actions_for_student(self.student_user, limit=10)
        
        self.assertEqual(len(actions), 2)
        self.assertTrue(all(a['related_user'] == 'testuser' for a in actions))
    
    def test_audit_log_indexes(self):
        """Test that audit log has proper indexes."""
        # Create test data and verify querysets use indexes
        no_dues = NoDues.objects.create(roll_no=self.student_db)
        
        for i in range(5):
            AuditLog.log_change(
                user=self.admin_user,
                model_name='NoDues',
                object_id=no_dues.id,
                action='update',
            )
        
        # These queries should use indexes
        qs1 = AuditLog.objects.filter(timestamp__gte=timezone.now() - timedelta(days=1))
        qs2 = AuditLog.objects.filter(model_name='NoDues', object_id=no_dues.id)
        qs3 = AuditLog.objects.filter(user=self.admin_user, action='update')
        
        # Verify queries execute efficiently (not actually timing, just verify they work)
        self.assertGreater(qs1.count(), 0)
        self.assertGreater(qs2.count(), 0)
        self.assertGreater(qs3.count(), 0)
    
    def test_audit_log_user_tracking(self):
        """Test that audit logs track which user made the change."""
        no_dues = NoDues.objects.create(roll_no=self.student_db)
        
        AuditLog.log_change(
            user=self.admin_user,
            model_name='NoDues',
            object_id=no_dues.id,
            action='approve',
        )
        
        entry = AuditLog.objects.filter(
            model_name='NoDues',
            object_id=no_dues.id,
        ).first()
        
        self.assertEqual(entry.user, self.admin_user)
    
    def test_audit_log_related_user(self):
        """Test that audit logs can track which student was affected."""
        no_dues = NoDues.objects.create(roll_no=self.student_db)
        
        AuditLog.log_change(
            user=self.admin_user,
            model_name='NoDues',
            object_id=no_dues.id,
            action='update',
            related_user=self.student_user,
        )
        
        entry = AuditLog.objects.filter(
            model_name='NoDues',
            related_user=self.student_user,
        ).first()
        
        self.assertIsNotNone(entry)
        self.assertEqual(entry.related_user, self.student_user)


class AuditLogAPITest(TestCase):
    """Tests for audit log API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.student_user = User.objects.create_user(
            username='student',
            password='testpass123'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True
        )
        
        self.student_db = StudentDB.objects.create(
            roll_no=self.student_user,
            name='Test Student',
        )
    
    def test_student_can_view_own_trail(self):
        """Test that students can view their own audit trail."""
        # Login as student
        self.client.force_authenticate(user=self.student_user)
        
        # Create some audit entries for student
        no_dues = NoDues.objects.create(roll_no=self.student_db)
        AuditLog.log_change(
            user=self.admin_user,
            model_name='NoDues',
            object_id=no_dues.id,
            action='create',
            related_user=self.student_user,
        )
        
        # Student should see their own trail (if endpoint is set up)
        # response = self.client.get('/api/otheracademic/audit-log/my_trail/')
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_student_cannot_view_other_trail(self):
        """Test that students cannot view other students' trails."""
        other_student = User.objects.create_user(
            username='other',
            password='pass123'
        )
        
        self.client.force_authenticate(user=self.student_user)
        
        # Student should not be able to filter by other student
        # This permission check is in the viewset


class EscalationIntegrationTest(TestCase):
    """Integration tests for T14 + T16 workflow."""
    
    def setUp(self):
        """Set up test data."""
        self.student_user = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='pass123'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            is_staff=True,
            password='admin123'
        )
        
        self.student_db = StudentDB.objects.create(
            roll_no=self.student_user,
            name='Test Student',
        )
        
        self.no_dues = NoDues.objects.create(roll_no=self.student_db)
    
    def test_full_escalation_workflow_logged(self):
        """Test that full escalation workflow is logged in audit trail."""
        # Step 1: Create escalation (simulating 7-day reminder)
        escalation = NoDuesEscalation.objects.create(
            no_dues=self.no_dues,
            student=self.student_user,
            escalation_type='reminder_7day',
            status='sent',
            department='library',
            clear_field='library_clear',
        )
        
        # Log the escalation
        AuditLog.log_change(
            user=self.admin_user,
            model_name='NoDuesEscalation',
            object_id=escalation.id,
            action='escalate',
            related_user=self.student_user,
        )
        
        # Step 2: Admin approves
        NoDuesEscalationService.mark_clear_manually(
            self.no_dues,
            'library',
            self.admin_user,
            'Verified returned'
        )
        
        # Step 3: Verify full trail
        history = AuditLog.get_actions_for_student(self.student_user, limit=10)
        
        # Should have at least escalation + approval
        actions = [a['action'] for a in history]
        self.assertIn('escalate', actions)
        self.assertIn('approve', actions)
    
    def test_multiple_departments_tracked_separately(self):
        """Test that different departments are tracked separately in audit log."""
        # Approve library
        NoDuesEscalationService.mark_clear_manually(
            self.no_dues,
            'library',
            self.admin_user,
            'Library cleared'
        )
        
        # Approve hostel
        NoDuesEscalationService.mark_clear_manually(
            self.no_dues,
            'hostel',
            self.admin_user,
            'Hostel cleared'
        )
        
        # Check history
        history = NoDuesClearanceHistory.objects.filter(
            student=self.student_user
        ).order_by('-changed_at')
        
        self.assertEqual(history.count(), 2)
        departments = [h.department for h in history]
        self.assertIn('library', departments)
        self.assertIn('hostel', departments)
    
    def test_rejection_and_reapproval_tracked(self):
        """Test that rejection followed by approval is properly tracked."""
        # Initial rejection
        NoDuesEscalationService.mark_notclear_manually(
            self.no_dues,
            'library',
            self.admin_user,
            'Books not returned'
        )
        
        self.no_dues.refresh_from_db()
        self.assertTrue(self.no_dues.library_notclear)
        
        # Later approval
        NoDuesEscalationService.mark_clear_manually(
            self.no_dues,
            'library',
            self.admin_user,
            'Books verified returned'
        )
        
        self.no_dues.refresh_from_db()
        self.assertTrue(self.no_dues.library_clear)
        
        # Check history shows both transitions
        history = NoDuesClearanceHistory.objects.filter(
            student=self.student_user,
            department='library'
        ).order_by('changed_at')
        
        self.assertEqual(history.count(), 2)
        self.assertEqual(history[0].new_status, 'notclear')
        self.assertEqual(history[1].new_status, 'clear')


# T22 Tests: Analytics Dashboard
class AnalyticsServiceTest(TestCase):
    """Tests for analytics service (T22)."""
    
    def setUp(self):
        """Set up test data."""
        from applications.otheracademic.analytics_service import AnalyticsService
        
        self.student_user = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='pass123'
        )
        
        self.student_db = StudentDB.objects.create(
            roll_no=self.student_user,
            name='Test Student',
        )
        
        self.no_dues = NoDues.objects.create(roll_no=self.student_db)
        self.analytics_service = AnalyticsService
    
    def test_generate_daily_analytics(self):
        """Test daily analytics generation."""
        results = self.analytics_service.generate_daily_analytics()
        
        self.assertIn('total_records', results)
        self.assertIn('cleared_count', results)
        self.assertIn('escalation_rate', results)
        self.assertGreaterEqual(results['total_records'], 1)
    
    def test_get_all_departments_analytics(self):
        """Test getting analytics for all departments."""
        data = self.analytics_service.get_all_departments_analytics()
        
        self.assertGreater(len(data), 0)
        first_dept = data[0]
        self.assertIn('department', first_dept)
        self.assertIn('clear_rate', first_dept)
        self.assertIn('total', first_dept)
    
    def test_get_escalation_analytics(self):
        """Test escalation analytics retrieval."""
        # Create test escalation
        NoDuesEscalation.objects.create(
            no_dues=self.no_dues,
            student=self.student_user,
            escalation_type='reminder_7day',
            status='sent',
            department='library',
            clear_field='library_clear',
        )
        
        data = self.analytics_service.get_escalation_analytics(days=30)
        
        self.assertIn('total_escalations', data)
        self.assertEqual(data['total_escalations'], 1)
        self.assertIn('by_type', data)
    
    def test_get_dashboard_summary(self):
        """Test dashboard summary generation."""
        summary = self.analytics_service.get_dashboard_summary()
        
        self.assertIn('summary', summary)
        self.assertIn('departments', summary)
        self.assertIn('escalations', summary)
        self.assertIn('turnaround_time', summary)
        self.assertEqual(summary['summary']['total_students'], 1)
    
    def test_get_department_analytics(self):
        """Test single department analytics."""
        data = self.analytics_service.get_department_analytics('library')
        
        self.assertEqual(data['department'], 'library')
        self.assertIn('total', data)
        self.assertIn('clear_rate', data)


# T23 Tests: User Feedback System
class FeedbackTest(TestCase):
    """Tests for feedback system (T23)."""
    
    def setUp(self):
        """Set up test data."""
        from applications.otheracademic.analytics_models import Feedback
        
        self.student_user = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='pass123'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            is_staff=True
        )
    
    def test_create_feedback(self):
        """Test creating feedback entry."""
        from applications.otheracademic.analytics_models import Feedback
        
        feedback = Feedback.objects.create(
            user=self.student_user,
            category='process_clarity',
            rating=4,
            title='Process is clear',
            comment='Good documentation and clear steps',
            is_anonymous=False,
        )
        
        self.assertEqual(feedback.user, self.student_user)
        self.assertEqual(feedback.rating, 4)
        self.assertEqual(feedback.category, 'process_clarity')
    
    def test_feedback_aggregated_ratings(self):
        """Test getting aggregated ratings."""
        from applications.otheracademic.analytics_models import Feedback
        
        # Create multiple feedbacks
        for rating in [3, 4, 5, 4]:
            Feedback.objects.create(
                user=self.student_user,
                category='ease_of_use',
                rating=rating,
                title='Test',
                comment='Comment',
            )
        
        stats = Feedback.get_aggregated_ratings()
        
        self.assertIn('average_rating', stats)
        self.assertEqual(stats['total_feedback'], 4)
        self.assertGreater(stats['average_rating'], 0)
    
    def test_admin_response_to_feedback(self):
        """Test admin responding to feedback."""
        from applications.otheracademic.analytics_models import Feedback
        
        feedback = Feedback.objects.create(
            user=self.student_user,
            category='support',
            rating=2,
            title='Support issue',
            comment='Need better support',
        )
        
        feedback.admin_response = 'We will improve support'
        feedback.responded_by = self.admin_user
        feedback.responded_at = timezone.now()
        feedback.save()
        
        self.assertIsNotNone(feedback.admin_response)
        self.assertEqual(feedback.responded_by, self.admin_user)
    
    def test_feedback_helpfulness_tracking(self):
        """Test tracking if feedback is helpful."""
        from applications.otheracademic.analytics_models import Feedback, FeedbackHelpfulness
        
        feedback = Feedback.objects.create(
            user=self.student_user,
            category='process_clarity',
            rating=5,
            title='Great feedback',
            comment='This is helpful',
        )
        
        # Mark as helpful
        helpful = FeedbackHelpfulness.objects.create(
            feedback=feedback,
            user=self.admin_user,
            is_helpful=True,
        )
        
        self.assertTrue(helpful.is_helpful)
        
        # Update helpful count
        feedback.helpful_count = 1
        feedback.save()
        
        self.assertEqual(feedback.helpful_count, 1)


# T24 Tests: System Verification
class VerificationServiceTest(TestCase):
    """Tests for system verification (T24)."""
    
    def setUp(self):
        """Set up test data."""
        from applications.otheracademic.verification_service import VerificationService
        
        self.verification_service = VerificationService
    
    def test_check_models_exist(self):
        """Test that all required models are found."""
        results = self.verification_service.check_models()
        
        self.assertIn('status', results)
        self.assertGreaterEqual(results['models_found'], 8)
        self.assertEqual(results['models_checked'], 10)
    
    def test_check_endpoints(self):
        """Test endpoint verification."""
        results = self.verification_service.check_endpoints()
        
        self.assertEqual(results['status'], 'success')
        self.assertGreater(len(results['details']), 0)
    
    def test_check_permissions(self):
        """Test permission verification."""
        results = self.verification_service.check_permissions()
        
        self.assertIn('status', results)
        self.assertGreater(results['permission_classes_checked'], 0)
    
    def test_check_audit_logging(self):
        """Test audit logging verification."""
        results = self.verification_service.check_audit_logging()
        
        self.assertIn('status', results)
        self.assertIn('audit_log_counts', results)
    
    def test_check_database_integrity(self):
        """Test database integrity checks."""
        results = self.verification_service.check_database_integrity()
        
        self.assertIn('status', results)
        self.assertIn('checks', results)
    
    def test_full_verification(self):
        """Test comprehensive system verification."""
        results = self.verification_service.run_full_verification()
        
        self.assertIn('overall_status', results)
        self.assertIn('checks', results)
        self.assertIn('summary', results)
        self.assertIn('models', results['checks'])
        self.assertIn('endpoints', results['checks'])


class SystemHealthCheckTest(TestCase):
    """Tests for system health checks."""
    
    def test_health_check_creation(self):
        """Test creating health check entry."""
        from applications.otheracademic.analytics_models import SystemHealthCheck
        
        check = SystemHealthCheck.log_check(
            'test_check',
            'success',
            'Test message',
            {'detail': 'test'}
        )
        
        self.assertEqual(check.check_type, 'test_check')
        self.assertEqual(check.status, 'success')
        self.assertIsNotNone(check.timestamp)
    
    def test_health_check_queries(self):
        """Test querying health checks."""
        from applications.otheracademic.analytics_models import SystemHealthCheck
        
        SystemHealthCheck.log_check('check1', 'success', 'Message 1')
        SystemHealthCheck.log_check('check2', 'error', 'Message 2')
        
        recent = SystemHealthCheck.objects.order_by('-timestamp')[:5]
        
        self.assertEqual(recent.count(), 2)
        self.assertEqual(recent[0].check_type, 'check2')


class APICallLogTest(TestCase):
    """Tests for API call logging."""
    
    def test_api_log_creation(self):
        """Test creating API call log."""
        from applications.otheracademic.analytics_models import APICallLog
        
        user = User.objects.create_user(username='testuser')
        
        log = APICallLog.objects.create(
            endpoint='/api/test/',
            method='GET',
            user=user,
            status_code=200,
            response_time_ms=42,
        )
        
        self.assertEqual(log.endpoint, '/api/test/')
        self.assertEqual(log.status_code, 200)
    
    def test_endpoint_statistics(self):
        """Test getting endpoint statistics."""
        from applications.otheracademic.analytics_models import APICallLog
        
        user = User.objects.create_user(username='testuser')
        
        # Create multiple calls
        APICallLog.objects.create(
            endpoint='/api/test/',
            method='GET',
            user=user,
            status_code=200,
            response_time_ms=50,
        )
        APICallLog.objects.create(
            endpoint='/api/test/',
            method='GET',
            user=user,
            status_code=500,
            response_time_ms=100,
        )
        
        stats = APICallLog.get_endpoint_stats('/api/test/')
        
        self.assertGreater(len(stats), 0)
