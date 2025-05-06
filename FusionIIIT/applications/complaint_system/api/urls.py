from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'^user/detail/(?P<detailcomp_id1>[0-9]+)/$', views.complaint_details_api,name='complain-detail-get-api'),
    url(r'^studentcomplain',views.student_complain_api,name='complain-detail2-get-api'),
    url(r'^newcomplain',views.create_complain_api,name='complain-post-api'),
    url(r'^updatecomplain/(?P<c_id>[0-9]+)',views.edit_complain_api,name='complain-put-api'),
    url(r'^removecomplain/(?P<c_id>[0-9]+)',views.edit_complain_api,name='complain-delete-api'),
    
    
    url(r'^workers',views.worker_api,name='worker-get-api'),
    url(r'^addworker',views.worker_api,name='worker-post-api'),
    url(r'^removeworker/(?P<w_id>[0-9]+)',views.edit_worker_api,name='worker-delete-api'),
    url(r'updateworker/(?P<w_id>[0-9]+)',views.edit_worker_api,name='worker-put-api'),

    url(r'^caretakers',views.caretaker_api,name='caretaker-get-api'),
    url(r'^addcaretaker',views.caretaker_api,name='caretaker-post-api'),
    url(r'^removecaretaker/(?P<c_id>[0-9]+)',views.edit_caretaker_api,name='caretaker-delete-api'),
    url(r'^updatecaretaker/(?P<c_id>[0-9]+)',views.edit_caretaker_api,name='caretaker-put-api'),
    
    url(r'^service_providers',views.service_provider_api,name='service_provider-get-api'),
    url(r'^addservice_provider',views.service_provider_api,name='service_provider-post-api'),
    url(r'^removeservice_provider/(?P<s_id>[0-9]+)',views.edit_service_provider_api,name='service_provider-delete-api'),
    url(r'^updateservice_provider/(?P<s_id>[0-9]+)',views.edit_service_provider_api,name='service_provider-put-api'),
    
]