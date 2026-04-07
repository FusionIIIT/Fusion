"""
Notification Service Module
============================

This service layer provides a clean API for internal modules to send notifications.
Other modules should use this service instead of directly calling notification functions.

Usage Example:
    from notification.services import NotificationService
    
    NotificationService.send_leave_notification(
        sender=request.user,
        recipient=student_user,
        type='leave_accepted'
    )
"""

import hashlib
from django.contrib.auth.models import User
from notifications.signals import notify
from .models import Announcements, AnnouncementRecipients, RegisteredModule
from applications.globals.models import ExtraInfo


class IdempotencyHelper:
    """
    Helper class for implementing idempotency (T-NT-01).
    Generates unique hash for each notification to prevent duplicates.
    """
    
    @staticmethod
    def generate_notification_hash(sender_id, recipient_id, verb, target=None):
        """
        Generate a unique hash for a notification based on:
        - sender_id: ID of notification sender
        - recipient_id: ID of notification recipient
        - verb: The action/message type
        - target: Optional target object identifier
        
        Returns:
            str: SHA256 hash of the notification payload
        """
        payload = f"{sender_id}:{recipient_id}:{verb}:{target or 'none'}"
        return hashlib.sha256(payload.encode()).hexdigest()
    
    @staticmethod
    def check_duplicate_notification(sender_id, recipient_id, verb, target=None, time_window_seconds=300):
        """
        Check if an identical notification was sent within the last N seconds.
        Time window defaults to 5 minutes to prevent rapid duplicate triggers.
        
        Args:
            sender_id: ID of sender
            recipient_id: ID of recipient
            verb: Notification action
            target: Optional target identifier
            time_window_seconds: Duplicate checking window (default: 300s = 5 min)
        
        Returns:
            bool: True if duplicate found (should NOT send), False if safe to send
        """
        from django.utils import timezone
        from datetime import timedelta
        from notifications.models import Notification
        
        try:
            hash_val = IdempotencyHelper.generate_notification_hash(sender_id, recipient_id, verb, target)
            cutoff_time = timezone.now() - timedelta(seconds=time_window_seconds)
            
            # Check if identical notification exists in recent time window
            existing = Notification.objects.filter(
                actor_object_id=sender_id,
                recipient_id=recipient_id,
                verb=verb,
                timestamp__gte=cutoff_time,
                data__contains=hash_val  # Store hash in data JSON
            ).exists()
            
            return existing
        except Exception as e:
            print(f"Error checking duplicate notification: {str(e)}")
            return False  # On error, allow the notification to go through


class NotificationService:
    """
    Service class for handling all notification operations.
    All modules should use this service to send notifications.
    """
    
    @staticmethod
    def send_notification(sender, recipient, url, module, verb, description=None, 
                         priority=3, check_idempotency=True, **kwargs):
        """
        Generic notification sender with idempotency support (T-NT-01).
        
        Args:
            sender: User object - who is sending notification
            recipient: User object - who receives notification
            url: str - URL name where user will be redirected
            module: str - Module name (e.g., 'Leave Module')
            verb: str - The notification message/action
            description: str - Additional description (optional)
            priority: int - Priority level (1=Critical, 4=Low) for T-NT-05
            check_idempotency: bool - Check for duplicate before sending (default: True)
            **kwargs: Additional data to pass to notification
        
        Returns:
            bool - True if successful, False otherwise
        """
        try:
            # T-NT-01: Check for duplicate notifications (idempotency)
            if check_idempotency:
                target_id = kwargs.get('target_id', None)
                is_duplicate = IdempotencyHelper.check_duplicate_notification(
                    sender_id=sender.id,
                    recipient_id=recipient.id,
                    verb=verb,
                    target=target_id
                )
                if is_duplicate:
                    print(f"Duplicate notification prevented: {verb} from {sender.username} to {recipient.username}")
                    return False  # Don't send duplicate
            
            # Generate hash for deduplication tracking
            notification_hash = IdempotencyHelper.generate_notification_hash(
                sender_id=sender.id,
                recipient_id=recipient.id,
                verb=verb,
                target=kwargs.get('target_id')
            )
            
            # Add hash and priority to notification data
            kwargs['notification_hash'] = notification_hash
            kwargs['priority'] = priority
            
            # Validate module if API key provided (T-NT-04)
            if 'api_key' in kwargs:
                if not NotificationService.validate_module_registration(kwargs.get('module_name'), kwargs['api_key']):
                    print(f"Unauthorized module attempted to send notification: {kwargs.get('module_name')}")
                    return False
            
            notify.send(
                sender=sender,
                recipient=recipient,
                url=url,
                module=module,
                verb=verb,
                description=description,
                **kwargs
            )
            return True
        except Exception as e:
            print(f"Error sending notification: {str(e)}")
            return False
    
    @staticmethod
    def validate_module_registration(module_name, api_key):
        """
        Validate that a module is registered and has correct API key (T-NT-04).
        
        Args:
            module_name: str - Name of the module
            api_key: str - API key provided by module
        
        Returns:
            bool - True if module is registered and active, False otherwise
        """
        try:
            registered_module = RegisteredModule.objects.get(
                module_name=module_name,
                api_key=api_key,
                is_active=True
            )
            return True
        except RegisteredModule.DoesNotExist:
            return False
        except Exception as e:
            print(f"Error validating module registration: {str(e)}")
            return False
    
    # ==================== LEAVE MODULE ====================
    
    @staticmethod
    def send_leave_notification(sender, recipient, type, date=None):
        """Send Leave Module Notification"""
        from notification.views import leave_module_notif
        try:
            leave_module_notif(sender, recipient, type, date)
            return True
        except Exception as e:
            print(f"Error in leave notification: {str(e)}")
            return False
    
    # ==================== PLACEMENT MODULE ====================
    
    @staticmethod
    def send_placement_notification(sender, recipient, type, description=None):
        """Send Placement Cell Notification"""
        from notification.views import placement_cell_notif
        try:
            placement_cell_notif(sender, recipient, type, description)
            return True
        except Exception as e:
            print(f"Error in placement notification: {str(e)}")
            return False
    
    # ==================== ACADEMICS MODULE ====================
    
    @staticmethod
    def send_academics_notification(sender, recipient, type):
        """Send Academics Module Notification"""
        from notification.views import academics_module_notif
        try:
            academics_module_notif(sender, recipient, type)
            return True
        except Exception as e:
            print(f"Error in academics notification: {str(e)}")
            return False
    
    # ==================== OFFICE MODULE ====================
    
    @staticmethod
    def send_office_notification(sender, recipient):
        """Send Office Module Notification"""
        from notification.views import office_module_notif
        try:
            office_module_notif(sender, recipient)
            return True
        except Exception as e:
            print(f"Error in office notification: {str(e)}")
            return False
    
    # ==================== CENTRAL MESS ====================
    
    @staticmethod
    def send_mess_notification(sender, recipient, type, message=None):
        """Send Central Mess Notification"""
        from notification.views import central_mess_notif
        try:
            central_mess_notif(sender, recipient, type, message)
            return True
        except Exception as e:
            print(f"Error in mess notification: {str(e)}")
            return False
    
    # ==================== VISITOR HOSTEL ====================
    
    @staticmethod
    def send_visitor_hostel_notification(sender, recipient, type):
        """Send Visitor Hostel Notification"""
        from notification.views import visitors_hostel_notif
        try:
            visitors_hostel_notif(sender, recipient, type)
            return True
        except Exception as e:
            print(f"Error in visitor hostel notification: {str(e)}")
            return False
    
    # ==================== HEALTHCARE CENTER ====================
    
    @staticmethod
    def send_healthcare_notification(sender, recipient, type, message=None):
        """Send Healthcare Center Notification"""
        from notification.views import healthcare_center_notif
        try:
            healthcare_center_notif(sender, recipient, type, message)
            return True
        except Exception as e:
            print(f"Error in healthcare notification: {str(e)}")
            return False
    
    # ==================== FILE TRACKING ====================
    
    @staticmethod
    def send_file_tracking_notification(sender, recipient, title):
        """Send File Tracking Notification"""
        from notification.views import file_tracking_notif
        try:
            file_tracking_notif(sender, recipient, title)
            return True
        except Exception as e:
            print(f"Error in file tracking notification: {str(e)}")
            return False
    
    # ==================== SCHOLARSHIPS ====================
    
    @staticmethod
    def send_scholarship_notification(sender, recipient, type):
        """Send Scholarship Portal Notification"""
        from notification.views import scholarship_portal_notif
        try:
            scholarship_portal_notif(sender, recipient, type)
            return True
        except Exception as e:
            print(f"Error in scholarship notification: {str(e)}")
            return False
    
    # ==================== COMPLAINT SYSTEM ====================
    
    @staticmethod
    def send_complaint_notification(sender, recipient, type, complaint_id, student, message):
        """Send Complaint System Notification"""
        from notification.views import complaint_system_notif
        try:
            complaint_system_notif(sender, recipient, type, complaint_id, student, message)
            return True
        except Exception as e:
            print(f"Error in complaint notification: {str(e)}")
            return False
    
    # ==================== DEPARTMENT ====================
    
    @staticmethod
    def send_department_notification(sender, recipient, type):
        """Send Department Notification"""
        from notification.views import department_notif
        try:
            department_notif(sender, recipient, type)
            return True
        except Exception as e:
            print(f"Error in department notification: {str(e)}")
            return False
    
    # ==================== RESEARCH PROCEDURES ====================
    
    @staticmethod
    def send_research_notification(sender, recipient, type):
        """Send Research Procedures Notification"""
        from notification.views import research_procedures_notif
        try:
            research_procedures_notif(sender, recipient, type)
            return True
        except Exception as e:
            print(f"Error in research notification: {str(e)}")
            return False
    
    # ==================== HOSTEL MANAGEMENT ====================
    
    @staticmethod
    def send_hostel_notification(sender, recipient, type):
        """Send Hostel Management Notification"""
        from notification.views import hostel_notifications
        try:
            hostel_notifications(sender, recipient, type)
            return True
        except Exception as e:
            print(f"Error in hostel notification: {str(e)}")
            return False
    
    # ==================== ANNOUNCEMENTS ====================
    
    @staticmethod
    def create_announcement(created_by, message, target_group='all_users', 
                           module='Fusion', department=None, batch=None, 
                           specific_users=None):
        """
        Create a new announcement.
        
        Args:
            created_by: User who creates announcement
            message: str - Announcement content
            target_group: str - 'all_users', 'students', 'faculty', 'staff', 'specific_users', 'department', 'batch'
            module: str - Module this announcement belongs to
            department: DepartmentInfo object (optional)
            batch: str - Batch code (optional)
            specific_users: list of ExtraInfo IDs (optional)
        
        Returns:
            Announcements object or None if failed
        """
        try:
            announcement = Announcements.objects.create(
                created_by=created_by,
                message=message,
                target_group=target_group,
                module=module,
                department=department,
                batch=batch,
                is_published=True
            )
            
            # Handle specific users
            if target_group == 'specific_users' and specific_users:
                for user_id in specific_users:
                    try:
                        extra_info = ExtraInfo.objects.get(id=user_id)
                        AnnouncementRecipients.objects.create(
                            announcement=announcement,
                            user=extra_info
                        )
                    except ExtraInfo.DoesNotExist:
                        continue
            
            return announcement
        except Exception as e:
            print(f"Error creating announcement: {str(e)}")
            return None
    
    @staticmethod
    def get_user_announcements(user):
        """
        Get all announcements visible to the user.
        
        Args:
            user: User object
        
        Returns:
            QuerySet of Announcements
        """
        try:
            from django.db.models import Q
            
            announcements = Announcements.objects.filter(is_active=True, is_published=True)
            
            # Staff and admins see all
            if user.is_staff or user.is_superuser:
                return announcements
            
            # Filter by user's profile
            extra_info = getattr(user, 'extrainfo', None)
            if not extra_info:
                return announcements.filter(target_group='all_users')
            
            user_type = extra_info.user_type
            department = extra_info.department
            
            filter_query = Q(target_group='all_users')
            
            if user_type == 'student':
                filter_query |= Q(target_group='students')
                if hasattr(extra_info, 'student') and extra_info.student:
                    filter_query |= Q(
                        target_group='batch',
                        batch=extra_info.student.batch
                    )
            
            if user_type == 'faculty':
                filter_query |= Q(target_group='faculty')
            
            if user_type == 'staff':
                filter_query |= Q(target_group='staff')
            
            if department:
                filter_query |= Q(
                    target_group='department',
                    department=department
                )
            
            # Specific users
            filter_query |= Q(
                target_group='specific_users',
                recipients__user=extra_info
            )
            
            return announcements.filter(filter_query).distinct()
        
        except Exception as e:
            print(f"Error getting user announcements: {str(e)}")
            return Announcements.objects.filter(target_group='all_users', is_active=True, is_published=True)
    
    @staticmethod
    def create_announcement_notifications(announcement):
        """
        Create notifications for all eligible recipients of an announcement.
        
        Args:
            announcement: Announcements object
            
        Returns:
            int - Number of notifications created
        """
        from django.db.models import Q
        
        recipient_count = 0
        users_to_notify = set()
        
        try:
            print(f"\n[Notification] Starting notification creation for announcement ID {announcement.id}")
            print(f"[Notification] Target group: {announcement.target_group}")
            
            # Determine target users based on target_group
            if announcement.target_group == 'all_users':
                # Include ALL active users (with and without ExtraInfo, including superusers)
                all_users = User.objects.filter(is_active=True)
                print(f"[Notification] Total active users in system: {all_users.count()}")
                for u in all_users:
                    print(f"[Notification]   - User: {u.username} (id={u.id}, is_staff={u.is_staff})")
                
                users_to_notify = set(all_users.values_list('id', flat=True))
                print(f"[Notification] all_users target: Found {len(users_to_notify)} eligible users")
            
            elif announcement.target_group == 'students':
                users_to_notify = set(
                    User.objects.filter(
                        extrainfo__user_type='student'
                    ).values_list('id', flat=True)
                )
            
            elif announcement.target_group == 'faculty':
                users_to_notify = set(
                    User.objects.filter(
                        extrainfo__user_type='faculty'
                    ).values_list('id', flat=True)
                )
            
            elif announcement.target_group == 'staff':
                users_to_notify = set(
                    User.objects.filter(
                        extrainfo__user_type='staff'
                    ).values_list('id', flat=True)
                )
            
            elif announcement.target_group == 'department':
                users_to_notify = set(
                    User.objects.filter(
                        extrainfo__department=announcement.department
                    ).values_list('id', flat=True)
                )
            
            elif announcement.target_group == 'batch':
                users_to_notify = set(
                    User.objects.filter(
                        extrainfo__student__batch=announcement.batch
                    ).values_list('id', flat=True)
                )
            
            elif announcement.target_group == 'specific_users':
                # Get users from AnnouncementRecipients
                recipients = announcement.recipients.all()
                users_to_notify = set(recipients.values_list('user_id', flat=True))
            
            # Create AnnouncementRecipients entries and send notifications
            print(f"[Notification] Preparing to notify {len(users_to_notify)} users for announcement: {announcement.message[:50]}")
            
            for user_id in users_to_notify:
                try:
                    user = User.objects.get(id=user_id)
                    print(f"[Notification] Processing user {user.username} (id={user_id})")
                    
                    # Get ExtraInfo for the user (required for AnnouncementRecipients)
                    try:
                        extra_info = ExtraInfo.objects.get(user_id=user_id)
                    except ExtraInfo.DoesNotExist:
                        print(f"[Notification]   - WARNING: No ExtraInfo for user {user.username}, skipping")
                        continue
                    
                    # Create recipient entry if not exists
                    recipient_obj, created = AnnouncementRecipients.objects.get_or_create(
                        announcement=announcement,
                        user=extra_info,
                        defaults={'is_read': False}
                    )
                    print(f"[Notification]   - Recipient entry {'created' if created else 'already exists'}")
                    
                    # Send django-notifications-hq notification
                    print(f"[Notification]   - Sending django-notifications-hq notification...")
                    notify.send(
                        sender=announcement.created_by,
                        recipient=user,
                        verb='announcement',
                        description=announcement.message[:100],
                        action_object=announcement,
                        target=announcement,
                        data={'module': announcement.module, 'type': 'announcement'}
                    )
                    print(f"[Notification]   - Notification sent successfully!")
                    
                    recipient_count += 1
                
                except User.DoesNotExist:
                    print(f"[Notification] ERROR: User {user_id} not found")
                    continue
                except Exception as e:
                    print(f"[Notification] ERROR notifying user {user_id}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            print(f"[Notification] Total notifications created: {recipient_count}\n")
            return recipient_count
        
        except Exception as e:
            print(f"Error creating announcement notifications: {str(e)}")
            return 0
