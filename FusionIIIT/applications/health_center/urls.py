"""
Health Center URL bridge
========================
Routes all /healthcenter/api/phc/ requests into the PHC REST API.

Included from project root urls.py as:
    url(r'^healthcenter/', include('applications.health_center.urls'))

API then becomes available at:
    /healthcenter/api/phc/patient/dashboard/
    /healthcenter/api/phc/compounder/dashboard/
    etc.
"""

from django.urls import path, include

urlpatterns = [
    path('api/phc/', include('applications.health_center.api.urls')),
]
