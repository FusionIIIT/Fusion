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

import notifications.urls
import debug_toolbar
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views


urlpatterns = [
    url(r'^', include('applications.globals.urls')),
    url(r'^feeds/', include('applications.feeds.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^academic-procedures/', include('applications.academic_procedures.urls')),
    url(r'^aims/', include('applications.academic_information.urls')),
    url(r'^notifications/', include('applications.notifications_extension.urls')),
    url(r'^estate/', include('applications.estate_module.urls')),
    url(r'^dep/', include('applications.department.urls')),
    url(r'^programme_curriculum/',include('applications.programme_curriculum.urls')),
    url(r'^iwdModuleV2/', include('applications.iwdModuleV2.urls')),
    url(r'^__debug__/', include(debug_toolbar.urls)),
    url(r'^research_procedures/', include('applications.research_procedures.urls')),
    url(r'^accounts/', include('allauth.urls')),


    url(r'^eis/', include('applications.eis.urls')),
    url(r'^mess/', include('applications.central_mess.urls')),
    url(r'^complaint/', include('applications.complaint_system.urls')),
    url(r'^healthcenter/', include('applications.health_center.urls')),
    url(r'^leave/', include('applications.leave.urls')),
    url(r'^placement/', include('applications.placement_cell.urls')),
    url(r'^filetracking/', include('applications.filetracking.urls')),
    url(r'^spacs/', include('applications.scholarships.urls')),
    url(r'^visitorhostel/', include('applications.visitor_hostel.urls')),
    url(r'^office/', include('applications.office_module.urls')),
    url(r'^finance/', include('applications.finance_accounts.urls')),
    url(r'^purchase-and-store/', include('applications.ps1.urls')),
    url(r'^gymkhana/', include('applications.gymkhana.urls')),
    url(r'^library/', include('applications.library.urls')),
    url(r'^establishment/', include('applications.establishment.urls')),
    url(r'^ocms/', include('applications.online_cms.urls')),
    url(r'^counselling/', include('applications.counselling_cell.urls')),
    url(r'^hostelmanagement/', include('applications.hostel_management.urls')),
    url(r'^income-expenditure/', include('applications.income_expenditure.urls')),
    url(r'^hr2/', include('applications.hr2.urls')),
    url(r'^recruitment/', include('applications.recruitment.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
