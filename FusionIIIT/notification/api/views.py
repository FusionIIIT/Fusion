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
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth.models import User
from notifications.models import Notification

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
            notifications = notifications.filter(data__module=module)
        
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
    
    def get_queryset(self):
        """
        Return announcements visible to the current user.
        
        Admins see all announcements.
        Regular users see announcements targeted to them.
        """
        if self.request.user.is_staff or self.request.user.is_superuser:
            return Announcements.objects.all()
        
        return get_announcements_for_user(self.request.user)
    
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
        
        Only staff/admins can create announcements.
        """
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'detail': 'You do not have permission to create announcements.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Add created_by
        serializer.validated_data['created_by'] = request.user
        serializer.validated_data['is_published'] = True
        serializer.validated_data['published_at'] = timezone.now()
        
        announcement = serializer.save()
        
        return Response(
            AnnouncementDetailSerializer(announcement).data,
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """
        Update an announcement.
        
        Only the creator or admins can update announcements.
        """
        announcement = self.get_object()
        
        # Check permissions
        if not (request.user.is_staff or request.user == announcement.created_by):
            return Response(
                {'detail': 'You do not have permission to update this announcement.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(announcement, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        serializer.save()
        
        return Response(AnnouncementDetailSerializer(announcement).data)
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete an announcement.
        
        Only the creator or admins can delete announcements.
        """
        announcement = self.get_object()
        
        # Check permissions
        if not (request.user.is_staff or request.user == announcement.created_by):
            return Response(
                {'detail': 'You do not have permission to delete this announcement.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        announcement.is_active = False
        announcement.save()
        
        return Response(
            {'message': 'Announcement deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
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
        announcements = Announcements.objects.filter(created_by=request.user).order_by('-created_at')
        
        serializer = AnnouncementListSerializer(announcements, many=True)
        
        return Response({
            'count': len(announcements),
            'results': serializer.data,
        })
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get statistics for an announcement"""
        announcement = self.get_object()
        
        # Get recipient count based on target group
        recipients = AnnouncementRecipients.objects.filter(announcement=announcement)
        total_recipients = recipients.count()
        
        if total_recipients == 0:
            return Response({
                'announcement_id': announcement.id,
                'message': announcement.message,
                'target_group': announcement.get_target_group_display(),
                'total_recipients': 0,
                'read_count': 0,
                'unread_count': 0,
                'read_percentage': 0,
            })
        
        read_count = recipients.filter(is_read=True).count()
        unread_count = total_recipients - read_count
        read_percentage = (read_count / total_recipients * 100) if total_recipients > 0 else 0
        
        return Response({
            'announcement_id': announcement.id,
            'message': announcement.message,
            'target_group': announcement.get_target_group_display(),
            'total_recipients': total_recipients,
            'read_count': read_count,
            'unread_count': unread_count,
            'read_percentage': round(read_percentage, 2),
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
