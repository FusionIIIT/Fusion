"""
Notification API URL Routing
=============================

This module defines all API endpoints for the notification module.
All endpoints are prefixed with /notification/api/

Routes:
    /notification/api/notifications/        - Notification endpoints
    /notification/api/announcements/        - Announcement endpoints
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, AnnouncementViewSet

# Create router for viewsets
router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'announcements', AnnouncementViewSet, basename='announcement')

app_name = 'notification-api'

urlpatterns = [
    path('', include(router.urls)),
]
