"""
Notification Module URLs
=========================

This file routes all notification-related API endpoints.

Main Routes:
    /notification/api/              - All API endpoints (viewsets)
"""

from django.urls import path, include

app_name = 'notification'

urlpatterns = [
    # API endpoints (new REST API using proper structure)
    path('api/', include('notification.api.urls', namespace='api')),
]
