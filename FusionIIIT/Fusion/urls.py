from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^', include('applications.globals.urls')),
    url(r'^eis/', include('applications.eis.urls')),
    url(r'^mess/', include('applications.central_mess.urls')),
    url(r'^complaint/', include('applications.complaint_system.urls')),
    url(r'^finance/', include('applications.finance_accounts.urls')),
    url(r'^gymkhana/', include('applications.gymkhana.urls')),
    url(r'^healthcenter/', include('applications.health_center.urls')),
    url(r'^library/', include('applications.library.urls')),
    url(r'^leave/', include('applications.leave.urls')),
    url(r'^placement/', include('applications.placement_cell.urls')),
    url(r'^spacs/', include('applications.scholarships.urls')),
    url(r'^office/', include('applications.office_module.urls')),
    url(r'^visitorhostel/', include('applications.visitor_hostel.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^ocms/', include('applications.online_cms.urls')),
    url(r'^login/', auth_views.login, name='login'),
    url(r'^logout/', auth_views.logout, name='logout'),
    url(r'^academic-procedures/', include('applications.academic_procedures.urls',
                                          namespace='procedures')),

]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
