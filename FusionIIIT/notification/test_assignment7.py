"""
Comprehensive Test Suite for Assignment 7 Implementation
=========================================================

Tests for all 5 completed tasks:
- T-NT-01: Idempotency Hashing
- T-NT-02: Announcement Expiry
- T-NT-04: Module Registry
- T-NT-05: Priority Sorting
- T-NT-07: Email Config (indirectly)

Run tests: python manage.py test notification.tests.test_assignment7 -v2
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from notifications.models import Notification

from .models import Announcements, RegisteredModule, AnnouncementRecipients
from .services import NotificationService, IdempotencyHelper
from .selectors import get_announcements_for_user, get_user_notifications
from applications.globals.models import ExtraInfo


class IdempotencyHelperTests(TestCase):
    """Tests for T-NT-01: Idempotency Hashing"""
    
    def setUp(self):
        self.sender = User.objects.create_user(username='sender', password='test123')
        self.recipient = User.objects.create_user(username='recipient', password='test123')
    
    def test_generate_notification_hash(self):
        """Test that hash generation is deterministic"""
        hash1 = IdempotencyHelper.generate_notification_hash(
            sender_id=self.sender.id,
            recipient_id=self.recipient.id,
            verb='leave_approved',
            target='leave_123'
        )
        
        hash2 = IdempotencyHelper.generate_notification_hash(
            sender_id=self.sender.id,
            recipient_id=self.recipient.id,
            verb='leave_approved',
            target='leave_123'
        )
        
        # Same inputs should produce same hash
        self.assertEqual(hash1, hash2)
    
    def test_different_payload_different_hash(self):
        """Test that different payloads produce different hashes"""
        hash1 = IdempotencyHelper.generate_notification_hash(
            sender_id=self.sender.id,
            recipient_id=self.recipient.id,
            verb='leave_approved'
        )
        
        hash2 = IdempotencyHelper.generate_notification_hash(
            sender_id=self.sender.id,
            recipient_id=self.recipient.id,
            verb='leave_rejected'
        )
        
        # Different verbs should produce different hashes
        self.assertNotEqual(hash1, hash2)
    
    def test_hash_format(self):
        """Test that hash is a valid SHA256 hex string"""
        hash_val = IdempotencyHelper.generate_notification_hash(
            sender_id=1, recipient_id=2, verb='test'
        )
        
        # SHA256 produces 64 character hex string
        self.assertEqual(len(hash_val), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in hash_val))


class RegisteredModuleTests(TestCase):
    """Tests for T-NT-04: Module Registry Model"""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin',
            password='test123',
            is_staff=True
        )
    
    def test_create_registered_module(self):
        """Test creating a registered module"""
        module = RegisteredModule.objects.create(
            module_name='Leave Module',
            api_key='leave-api-key-12345',
            is_active=True,
            default_priority=2,
            created_by=self.admin_user
        )
        
        self.assertEqual(module.module_name, 'Leave Module')
        self.assertTrue(module.is_active)
        self.assertEqual(module.default_priority, 2)
    
    def test_module_unique_name(self):
        """Test that module names are unique"""
        RegisteredModule.objects.create(
            module_name='Leave Module',
            api_key='key1',
            created_by=self.admin_user
        )
        
        with self.assertRaises(Exception):
            RegisteredModule.objects.create(
                module_name='Leave Module',  # Duplicate name
                api_key='key2',
                created_by=self.admin_user
            )
    
    def test_module_unique_api_key(self):
        """Test that API keys are unique"""
        RegisteredModule.objects.create(
            module_name='Module 1',
            api_key='unique-key',
            created_by=self.admin_user
        )
        
        with self.assertRaises(Exception):
            RegisteredModule.objects.create(
                module_name='Module 2',
                api_key='unique-key',  # Duplicate API key
                created_by=self.admin_user
            )
    
    def test_validate_module_registration_success(self):
        """Test successful module validation"""
        RegisteredModule.objects.create(
            module_name='Leave Module',
            api_key='leave-key-123',
            is_active=True,
            created_by=self.admin_user
        )
        
        result = NotificationService.validate_module_registration(
            'Leave Module',
            'leave-key-123'
        )
        
        self.assertTrue(result)
    
    def test_validate_module_registration_inactive(self):
        """Test validation fails for inactive module"""
        RegisteredModule.objects.create(
            module_name='Leave Module',
            api_key='leave-key-123',
            is_active=False,  # Inactive
            created_by=self.admin_user
        )
        
        result = NotificationService.validate_module_registration(
            'Leave Module',
            'leave-key-123'
        )
        
        self.assertFalse(result)
    
    def test_validate_module_wrong_api_key(self):
        """Test validation fails for wrong API key"""
        RegisteredModule.objects.create(
            module_name='Leave Module',
            api_key='leave-key-123',
            created_by=self.admin_user
        )
        
        result = NotificationService.validate_module_registration(
            'Leave Module',
            'wrong-key'
        )
        
        self.assertFalse(result)


class AnnouncementExpiryTests(TestCase):
    """Tests for T-NT-02: Announcement Expiry"""
    
    def setUp(self):
        self.creator = User.objects.create_user(
            username='creator',
            password='test123',
            is_staff=True
        )
    
    def test_create_announcement_with_expiry_date(self):
        """Test creating announcement with expiry date"""
        future_date = timezone.now() + timedelta(days=7)
        
        announcement = Announcements.objects.create(
            message='Test announcement',
            created_by=self.creator,
            is_published=True,
            expiry_date=future_date
        )
        
        self.assertEqual(announcement.expiry_date, future_date)
        self.assertFalse(announcement.is_expired())
    
    def test_announcement_is_expired_true(self):
        """Test is_expired() returns True for expired announcement"""
        past_date = timezone.now() - timedelta(days=1)
        
        announcement = Announcements.objects.create(
            message='Expired announcement',
            created_by=self.creator,
            is_published=True,
            expiry_date=past_date
        )
        
        self.assertTrue(announcement.is_expired())
    
    def test_announcement_is_expired_false(self):
        """Test is_expired() returns False for future expiry"""
        future_date = timezone.now() + timedelta(days=7)
        
        announcement = Announcements.objects.create(
            message='Active announcement',
            created_by=self.creator,
            is_published=True,
            expiry_date=future_date
        )
        
        self.assertFalse(announcement.is_expired())
    
    def test_announcement_without_expiry_date(self):
        """Test announcement without expiry date never expires"""
        announcement = Announcements.objects.create(
            message='No expiry announcement',
            created_by=self.creator,
            is_published=True,
            expiry_date=None
        )
        
        self.assertFalse(announcement.is_expired())


class PrioritySortingTests(TestCase):
    """Tests for T-NT-05: Priority-based Sorting"""
    
    def setUp(self):
        self.creator = User.objects.create_user(
            username='creator',
            password='test123',
            is_staff=True
        )
        self.user = User.objects.create_user(
            username='user',
            password='test123'
        )
        
        # Create announcements with different priorities
        self.critical = Announcements.objects.create(
            message='Critical announcement',
            created_by=self.creator,
            is_published=True,
            priority=1  # Critical
        )
        
        self.medium = Announcements.objects.create(
            message='Medium announcement',
            created_by=self.creator,
            is_published=True,
            priority=3  # Medium
        )
        
        self.low = Announcements.objects.create(
            message='Low announcement',
            created_by=self.creator,
            is_published=True,
            priority=4  # Low
        )
    
    def test_announcements_sorted_by_priority(self):
        """Test that announcements are sorted by priority (lower number = higher priority)"""
        announcements = get_announcements_for_user(self.user)
        announcements_list = list(announcements)
        
        # Critical should be first
        self.assertEqual(announcements_list[0].priority, 1)
        # Medium should be second
        self.assertEqual(announcements_list[1].priority, 3)
        # Low should be last
        self.assertEqual(announcements_list[2].priority, 4)
    
    def test_announcement_priority_choices(self):
        """Test that priority field has correct choices"""
        priorities = dict(Announcements._meta.get_field('priority').choices)
        
        self.assertEqual(priorities[1], 'Critical')
        self.assertEqual(priorities[2], 'High')
        self.assertEqual(priorities[3], 'Medium')
        self.assertEqual(priorities[4], 'Low')


class AnnouncementExpiryFilteringTests(TestCase):
    """Tests for T-NT-02: Expiry filtering in selectors"""
    
    def setUp(self):
        self.creator = User.objects.create_user(
            username='creator',
            password='test123',
            is_staff=True
        )
        self.user = User.objects.create_user(
            username='user',
            password='test123'
        )
    
    def test_expired_announcements_not_visible(self):
        """Test that expired announcements are filtered out"""
        past_date = timezone.now() - timedelta(days=1)
        
        # Create expired announcement
        Announcements.objects.create(
            message='Expired announcement',
            created_by=self.creator,
            is_published=True,
            expiry_date=past_date
        )
        
        # Create active announcement
        Announcements.objects.create(
            message='Active announcement',
            created_by=self.creator,
            is_published=True
        )
        
        announcements = get_announcements_for_user(self.user)
        
        # Only active announcement should be visible
        self.assertEqual(announcements.count(), 1)
        self.assertEqual(announcements[0].message, 'Active announcement')
    
    def test_future_expiry_announcements_visible(self):
        """Test that announcements with future expiry date are visible"""
        future_date = timezone.now() + timedelta(days=7)
        
        Announcements.objects.create(
            message='Future expiry announcement',
            created_by=self.creator,
            is_published=True,
            expiry_date=future_date
        )
        
        announcements = get_announcements_for_user(self.user)
        
        self.assertEqual(announcements.count(), 1)
        self.assertEqual(announcements[0].message, 'Future expiry announcement')


class EmailConfigurationTests(TestCase):
    """Tests for T-NT-07: Externalized Email Configuration"""
    
    def test_email_settings_exist(self):
        """Test that email settings are configured"""
        from django.conf import settings
        
        # These should exist and not be None
        self.assertIsNotNone(settings.EMAIL_HOST)
        self.assertIsNotNone(settings.EMAIL_HOST_USER)
        self.assertIsNotNone(settings.EMAIL_PORT)
        
        # Check basic validation
        self.assertGreater(settings.EMAIL_PORT, 0)
        self.assertIn('@', settings.EMAIL_HOST_USER)
    
    def test_email_backend_configured(self):
        """Test that email backend is properly configured"""
        from django.conf import settings
        
        self.assertEqual(
            settings.EMAIL_BACKEND,
            'django.core.mail.backends.smtp.EmailBackend'
        )


class IntegrationTests(TestCase):
    """Integration tests combining multiple features"""
    
    def setUp(self):
        self.sender = User.objects.create_user(
            username='sender',
            password='test123',
            is_staff=True
        )
        self.recipient = User.objects.create_user(
            username='recipient',
            password='test123'
        )
    
    def test_send_notification_with_priority_and_idempotency(self):
        """Test sending notification with priority and idempotency checks"""
        result = NotificationService.send_notification(
            sender=self.sender,
            recipient=self.recipient,
            url='leave:leave',
            module='Leave Module',
            verb='leave_approved',
            priority=1,  # Critical priority
            check_idempotency=True
        )
        
        self.assertTrue(result)
    
    def test_announcement_with_all_features(self):
        """Test announcement with priority and expiry date"""
        future_date = timezone.now() + timedelta(days=7)
        
        announcement = Announcements.objects.create(
            message='Priority announcement with expiry',
            created_by=self.sender,
            is_published=True,
            priority=1,  # Critical
            expiry_date=future_date
        )
        
        self.assertEqual(announcement.priority, 1)
        self.assertEqual(announcement.expiry_date, future_date)
        self.assertFalse(announcement.is_expired())


class ModelIndexesTests(TestCase):
    """Tests for database indexes on models"""
    
    def test_announcement_indexes_exist(self):
        """Test that indexes are created for performance"""
        meta = Announcements._meta
        indexes = meta.indexes
        
        # Check that indexes exist
        self.assertGreater(len(indexes), 0)


# Test execution instructions
if __name__ == '__main__':
    import django
    django.setup()
    
    from django.core.management import execute_from_command_line
    execute_from_command_line(['manage.py', 'test', 'notification.tests.test_assignment7', '-v2'])
