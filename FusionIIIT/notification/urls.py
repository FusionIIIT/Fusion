"""
Notification Module URLs
=========================

This file routes all notification-related API endpoints.

Main Routes:
    /notification/api/              - All API endpoints (viewsets)
    /notifications/                 - Legacy endpoints (from notifications_extension)
"""

from django.urls import path, include
from django.conf.urls import url

app_name = 'notification'

urlpatterns = [
    # API endpoints (new REST API using proper structure)
    path('api/', include('notification.api.urls', namespace='api')),
]
