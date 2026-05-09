"""
PHC App Configuration
"""

from django.apps import AppConfig


class HealthCenterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name               = 'applications.health_center'
    verbose_name       = 'Primary Health Center'
