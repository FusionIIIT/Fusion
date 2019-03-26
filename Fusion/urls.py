"""Fusion URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^', include('applications.globals.urls')),
    url(r'^feeds/', include('applications.feeds.urls')),
    url(r'^eis/', include('applications.eis.urls', namespace='eis')),
    url(r'^mess/', include('applications.central_mess.urls')),
    url(r'^complaint/', include('applications.complaint_system.urls')),
    url(r'^healthcenter/', include('applications.health_center.urls')),
    url(r'^leave/', include('applications.leave.urls')),
    url(r'^placement/', include('applications.placement_cell.urls', namespace='placement')),
    url(r'^filetracking/', include('applications.filetracking.urls')),
    url(r'^spacs/', include('applications.scholarships.urls')),
    url(r'^visitorhostel/', include('applications.visitor_hostel.urls')),
    url(r'^office/', include('applications.office_module.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^finance/', include('applications.finance_accounts.urls')),
    url(r'^gymkhana/', include('applications.gymkhana.urls')),
    url(r'^library/', include('applications.library.urls')),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^ocms/', include('applications.online_cms.urls')),
    url(r'^login/', auth_views.login, name='login'),
    url(r'^logout/', auth_views.logout, name='logout'),
    url(r'^academic-procedures/', include('applications.academic_procedures.urls',
                                          namespace='procedures')),
    url(r'^aims/', include('applications.academic_information.urls')),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
