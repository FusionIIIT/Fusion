"""
Notification API Views
======================

REST API views for notifications and announcements.
Provides endpoints for frontend to fetch, create, and manage notifications.

Endpoints:
    GET    /notification/api/notifications/          - List user notifications
    POST   /notification/api/notifications/          - Trigger a notification
    GET    /notification/api/notifications/{id}/     - Get notification detail
    PUT    /notification/api/notifications/{id}/     - Mark as read
    DELETE /notification/api/notifications/{id}/     - Delete notification
    
    GET    /notification/api/announcements/          - List announcements for user
    POST   /notification/api/announcements/          - Create announcement
    GET    /notification/api/announcements/{id}/     - Get announcement detail
    PUT    /notification/api/announcements/{id}/     - Update announcement
    DELETE /notification/api/announcements/{id}/     - Delete announcement
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count, Q
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth.models import User
from notifications.models import Notification
from applications.globals.models import HoldsDesignation

from ..models import Announcements, AnnouncementRecipients
from ..services import NotificationService
from ..selectors import (
    get_user_notifications,
    get_announcements_for_user,
    get_user_unread_count,
    get_announcement_by_id,
)
from .serializers import (
    NotificationSerializer,
    AnnouncementSerializer,
    AnnouncementListSerializer,
    AnnouncementDetailSerializer,
    CreateAnnouncementWithRecipientsSerializer,
    NotificationModuleStatsSerializer,
    split_announcement_message,
)


class NotificationViewSet(viewsets.ViewSet):
    """
    ViewSet for managing user notifications.
    
    Provides endpoints to:
    - List user notifications
    - Mark notifications as read/unread
    - Delete notifications
    - Get notification statistics
    """
    
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """
        Get all notifications for the current user.
        
        Query Parameters:
            - unread_only: bool - Return only unread notifications
            - limit: int - Maximum number of notifications
            - module: str - Filter by module name
        """
        unread_only = request.query_params.get('unread_only', 'false').lower() == 'true'
        limit = request.query_params.get('limit', None)
        module = request.query_params.get('module', None)
        
        notifications = get_user_notifications(
            user=request.user,
            unread_only=unread_only,
            limit=limit
        )
        
        # Filter by module if provided
        if module:
            if isinstance(notifications, list):
                notifications = [n for n in notifications if n.data and n.data.get('module') == module]
            else:
                # text fallback for jsonfield 
                notifications = notifications.filter(data__icontains=f'"module": "{module}"')
        
        serializer = NotificationSerializer(notifications, many=True)
        
        return Response({
            'count': len(notifications),
            'unread_count': get_user_unread_count(request.user),
            'results': serializer.data,
        })
    
    def retrieve(self, request, pk=None):
        """Get a specific notification"""
        notification = get_object_or_404(
            Notification,
            id=pk,
            recipient=request.user
        )
        
        serializer = NotificationSerializer(notification)
        return Response(serializer.data)
    
    def destroy(self, request, pk=None):
        """
        Soft-delete a notification (mark as deleted without removing from DB).
        
        Args:
            pk: Notification ID
        """
        notification = get_object_or_404(
            Notification,
            id=pk,
            recipient=request.user
        )
        
        notification.deleted = True
        notification.save()
        
        return Response(
            {'message': 'Notification deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a notification as read"""
        notification = get_object_or_404(
            Notification,
            id=pk,
            recipient=request.user
        )
        
        notification.mark_as_read()
        
        return Response({
            'message': 'Notification marked as read',
            'unread_count': get_user_unread_count(request.user),
        })
    
    @action(detail=True, methods=['post'])
    def mark_as_unread(self, request, pk=None):
        """Mark a notification as unread"""
        notification = get_object_or_404(
            Notification,
            id=pk,
            recipient=request.user
        )
        
        notification.unread = True
        notification.save()
        
        return Response({
            'message': 'Notification marked as unread',
            'unread_count': get_user_unread_count(request.user),
        })
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all notifications as read"""
        notifications = get_user_notifications(request.user, unread_only=True)
        
        for notification in notifications:
            notification.mark_as_read()
        
        return Response({
            'message': f'{len(notifications)} notifications marked as read',
            'unread_count': 0,
        })
    
    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """Delete all notifications"""
        count, _ = Notification.objects.filter(
            recipient=request.user,
            deleted=False
        ).update(deleted=True)
        
        return Response({
            'message': f'{count} notifications deleted',
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get notification statistics"""
        notifications = get_user_notifications(request.user)
        
        # Group by module
        module_stats = {}
        total_count = 0
        total_unread = 0
        
        for notif in notifications:
            module = notif.data.get('module', 'Other')
            
            if module not in module_stats:
                module_stats[module] = {'count': 0, 'unread': 0}
            
            module_stats[module]['count'] += 1
            total_count += 1
            
            if notif.unread:
                module_stats[module]['unread'] += 1
                total_unread += 1
        
        # Calculate percentages
        for module in module_stats:
            count = module_stats[module]['count']
            module_stats[module]['percentage'] = (count / total_count * 100) if total_count > 0 else 0
        
        return Response({
            'total_count': total_count,
            'unread_count': total_unread,
            'read_count': total_count - total_unread,
            'by_module': module_stats,
        })


class AnnouncementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing announcements.
    
    Provides endpoints to:
    - List announcements visible to user
    - Create announcements
    - Update announcements
    - Delete announcements
    - Get announcement statistics
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = AnnouncementSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['message', 'module']
    ordering_fields = ['created_at', 'published_at']
    ordering = ['-created_at']

    @staticmethod
    def _announcement_notification_qs(announcement):
        try:
            ct = ContentType.objects.get_for_model(Announcements)
            return Notification.objects.filter(
                Q(target_content_type=ct, target_object_id=str(announcement.id)) |
                Q(action_object_content_type=ct, action_object_object_id=str(announcement.id))
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting notification queryset for announcement {announcement.id}: {str(e)}")
            return Notification.objects.none()  # Return empty queryset if error

    @classmethod
    def _cleanup_related_notifications(cls, announcement):
        try:
            notification_qs = cls._announcement_notification_qs(announcement)
            if notification_qs.exists():
                notification_qs.delete()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error cleaning up notifications for announcement {announcement.id}: {str(e)}")
            # Don't raise the error, just log it and continue

    @staticmethod
    def _can_create_announcement(user):
        """Allow admins and faculty/staff designations to create announcements."""
        if user.is_staff or user.is_superuser:
            return True

        extra_info = getattr(user, 'extrainfo', None)
        user_type = (getattr(extra_info, 'user_type', '') or '').strip().lower()

        # Primary profile type-based access
        if user_type in ['faculty', 'staff']:
            return True

        # Explicit deny for student/guest unless they also hold allowed designations
        allowed_keywords = [
            'professor',
            'faculty',
            'dean',
            'hod',
            'head',
            'registrar',
            'admin',
            'staff',
        ]

        designations = HoldsDesignation.objects.filter(working=user).select_related('designation')
        for holds in designations:
            designation_name = str(getattr(holds.designation, 'name', '')).strip().lower()
            if any(keyword in designation_name for keyword in allowed_keywords):
                return True

        return False
    
    def get_queryset(self):
        """
        Return announcements visible to the current user.
        
        Admins see all announcements.
        Regular users see announcements targeted to them.
        """
        if self.request.user.is_staff or self.request.user.is_superuser:
            return Announcements.objects.all()

        # For non-staff users, build a unified query that includes both
        # announcements visible to them AND announcements they created
        from django.utils import timezone
        
        # Base queryset with same filters as get_announcements_for_user
        base_qs = Announcements.objects.filter(
            is_active=True,
            is_published=True
        ).exclude(
            expiry_date__lt=timezone.now()
        )
        
        # Get user's profile information
        try:
            extra_info = self.request.user.extrainfo
        except ExtraInfo.DoesNotExist:
            # If no profile, only show all_users announcements + own announcements
            return base_qs.filter(
                Q(target_group='all_users') | Q(created_by=self.request.user)
            ).distinct().order_by('priority', '-created_at')
        
        user_type = extra_info.user_type
        department = extra_info.department
        username = (self.request.user.username or '').upper()
        
        # Build the same filter query as in get_announcements_for_user
        filter_query = Q(target_group='all_users')
        
        # Filter by user type
        if user_type == 'student':
            filter_query |= Q(target_group='students')
            # Roll-number based targeting
            if 'BCS' in username:
                filter_query |= Q(target_group='batch', batch__iexact='BCS')
            if 'BEC' in username:
                filter_query |= Q(target_group='batch', batch__iexact='BEC')
            if 'BME' in username:
                filter_query |= Q(target_group='batch', batch__iexact='BME')
            # Add regex patterns for UG/PG
            import re
            if re.match(r'^\d{2}B[A-Z]{2}\d{3}$', username):
                filter_query |= Q(target_group='batch', batch__iexact='UG')
            if re.match(r'^\d{2}M[A-Z]{2}\d{3}$', username):
                filter_query |= Q(target_group='batch', batch__iexact='PG')
        elif user_type == 'faculty':
            filter_query |= Q(target_group='faculty')
        elif user_type == 'staff':
            filter_query |= Q(target_group='staff')
        
        # Filter by department
        if department:
            filter_query |= Q(
                target_group='department',
                department=department
            )
        
        # Filter by specific users
        filter_query |= Q(
            target_group='specific_users',
            recipients__user=extra_info
        )
        
        # Include announcements created by the user
        filter_query |= Q(created_by=self.request.user)
        
        return base_qs.filter(filter_query).distinct().order_by('priority', '-created_at')
    
    def get_serializer_class(self):
        """Use different serializer for different actions"""
        if self.action == 'list':
            return AnnouncementListSerializer
        elif self.action == 'retrieve':
            return AnnouncementDetailSerializer
        elif self.action == 'create':
            return CreateAnnouncementWithRecipientsSerializer
        return AnnouncementSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a new announcement.
        
        Allowed for: admins, superusers, faculty, and staff users.
        Students cannot create announcements.
        """
        if not self._can_create_announcement(request.user):
            return Response(
                {'detail': 'Only faculty members or admins can create announcements.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Add created_by
        serializer.validated_data['created_by'] = request.user
        serializer.validated_data['is_published'] = True
        serializer.validated_data['published_at'] = timezone.now()
        
        announcement = serializer.save()

        # Send notifications immediately for published announcements
        notification_count = NotificationService.create_announcement_notifications(announcement)
        
        return Response(
            {
                **AnnouncementDetailSerializer(announcement).data,
                'notifications_sent': notification_count,
            },
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """
        Update an announcement.
        
        Only the creator or admins can update announcements.
        """
        try:
            announcement = self.get_object()
            
            # Check permissions
            if not (request.user.is_staff or request.user == announcement.created_by):
                return Response(
                    {'detail': 'You do not have permission to update this announcement.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = CreateAnnouncementWithRecipientsSerializer(
                announcement,
                data=request.data,
                partial=True,
            )
            serializer.is_valid(raise_exception=True)
            
            serializer.save()

            # Regenerate announcement notifications to reflect updated targeting/content
            if announcement.is_published and announcement.is_active:
                try:
                    self._cleanup_related_notifications(announcement)
                    NotificationService.create_announcement_notifications(announcement)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error updating notifications for announcement {announcement.id}: {str(e)}")
            
            return Response(AnnouncementDetailSerializer(announcement).data)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating announcement: {str(e)}")
            return Response(
                {'detail': f'Error updating announcement: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete an announcement.
        
        Only the creator or admins can delete announcements.
        """
        try:
            announcement = self.get_object()
            
            # Check permissions
            if not (request.user.is_staff or request.user == announcement.created_by):
                return Response(
                    {'detail': 'You do not have permission to delete this announcement.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Clean up related notifications first
            try:
                self._cleanup_related_notifications(announcement)
            except Exception as e:
                # Log the error but continue with deletion
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error cleaning up notifications for announcement {announcement.id}: {str(e)}")
            
            # Delete the announcement
            announcement.delete()
            
            return Response(
                {'message': 'Announcement deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error deleting announcement: {str(e)}")
            return Response(
                {'detail': f'Error deleting announcement: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish an announcement and send notifications to users"""
        announcement = self.get_object()
        
        if announcement.created_by != request.user and not request.user.is_staff:
            return Response(
                {'detail': 'You do not have permission to publish this announcement.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        announcement.is_published = True
        announcement.published_at = timezone.now()
        announcement.save()
        
        # Create notifications for all eligible users
        notification_count = NotificationService.create_announcement_notifications(announcement)
        
        return Response({
            'message': f'Announcement published and {notification_count} notifications sent',
            'announcement': AnnouncementDetailSerializer(announcement).data,
            'notifications_sent': notification_count,
        })
    
    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """Unpublish an announcement"""
        announcement = self.get_object()
        
        if announcement.created_by != request.user and not request.user.is_staff:
            return Response(
                {'detail': 'You do not have permission to unpublish this announcement.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        announcement.is_published = False
        announcement.save()
        
        return Response({
            'message': 'Announcement unpublished',
        })
    
    @action(detail=False, methods=['get'])
    def my_announcements(self, request):
        """Get announcements created by the current user"""
        announcements = Announcements.objects.filter(
            created_by=request.user,
            is_active=True,
        ).order_by('-created_at')
        
        serializer = AnnouncementListSerializer(announcements, many=True)
        
        return Response({
            'count': len(announcements),
            'results': serializer.data,
        })
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get statistics for an announcement"""
        announcement = self.get_object()
        notification_qs = self._announcement_notification_qs(announcement).filter(deleted=False)
        total_recipients = notification_qs.count()

        # Keep AnnouncementRecipients read flags in sync with actual notification read state.
        if announcement.target_group == 'specific_users':
            read_user_ids = set(
                notification_qs.filter(unread=False).values_list('recipient_id', flat=True)
            )
            recipients = AnnouncementRecipients.objects.filter(
                announcement=announcement
            ).select_related('user__user')

            for recipient in recipients:
                recipient_user_id = getattr(recipient.user, 'user_id', None)
                should_be_read = recipient_user_id in read_user_ids

                if should_be_read and not recipient.is_read:
                    recipient.is_read = True
                    recipient.read_at = timezone.now()
                    recipient.save(update_fields=['is_read', 'read_at'])
                elif not should_be_read and recipient.is_read:
                    recipient.is_read = False
                    recipient.read_at = None
                    recipient.save(update_fields=['is_read', 'read_at'])
        
        if total_recipients == 0:
            return Response({
                'announcement_id': announcement.id,
                'message': announcement.message,
                'title': split_announcement_message(announcement.message).get('title', ''),
                'target_group': announcement.get_target_group_display(),
                'total_recipients': 0,
                'read_count': 0,
                'unread_count': 0,
                'read_percentage': 0,
            })
        
        read_count = notification_qs.filter(unread=False).count()
        unread_count = notification_qs.filter(unread=True).count()
        read_percentage = (read_count / total_recipients * 100) if total_recipients > 0 else 0
        
        return Response({
            'announcement_id': announcement.id,
            'message': announcement.message,
            'title': split_announcement_message(announcement.message).get('title', ''),
            'target_group': announcement.get_target_group_display(),
            'total_recipients': total_recipients,
            'read_count': read_count,
            'unread_count': unread_count,
            'read_percentage': round(read_percentage, 2),
        })

    @action(detail=False, methods=['get'])
    def student_roll_numbers(self, request):
        """Return dynamic student roll numbers for announcement targeting."""
        students = User.objects.filter(
            is_active=True,
            extrainfo__user_type__iexact='student',
            username__regex=r'^\d{2}[BM][A-Z]{2}\d{3}$',
        ).order_by('username')

        results = []
        for student in students:
            roll = (student.username or '').upper()
            if 'BCS' in roll:
                branch = 'CSE'
            elif 'BEC' in roll:
                branch = 'ECE'
            elif 'BME' in roll:
                branch = 'ME'
            elif 'MCS' in roll:
                branch = 'PG'
            else:
                branch = 'OTHER'

            programme = 'PG' if roll[2:3] == 'M' else 'UG'
            results.append({
                'username': roll,
                'programme': programme,
                'branch': branch,
            })

        return Response({
            'count': len(results),
            'results': results,
        })
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent announcements"""
        days = int(request.query_params.get('days', 7))
        limit = int(request.query_params.get('limit', 10))
        
        announcements = get_announcements_for_user(request.user)[:limit]
        
        serializer = AnnouncementListSerializer(announcements, many=True)
        
        return Response({
            'count': len(announcements),
            'results': serializer.data,
        })
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Mark an announcement as read for the current user.
        Updates AnnouncementRecipients.is_read and read_at fields.
        Implements Data Integrity requirement: read tracking for specific users.
        """
        announcement = self.get_object()
        
        try:
            extra_info = request.user.extrainfo
        except Exception:
            return Response(
                {'detail': 'User profile not found.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            recipient = AnnouncementRecipients.objects.get(
                announcement=announcement,
                user=extra_info
            )
            if not recipient.is_read:
                recipient.is_read = True
                recipient.read_at = timezone.now()
                recipient.save(update_fields=['is_read', 'read_at'])
            
            return Response({
                'message': 'Announcement marked as read.',
                'read_at': recipient.read_at,
            })
        except AnnouncementRecipients.DoesNotExist:
            # User is not a specific recipient — still acknowledge (broadcast announcements)
            return Response({
                'message': 'Acknowledged.',
            })
