from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'^user/detail/(?P<detailcomp_id1>[0-9]+)/$', views.complaint_details_api,name='Detail-api'),
    url(r'^studentcomplain',views.student_complain_api,name='StudentComplain-api'),
    url(r'^caretakers',views.caretaker_api,name='StudentComplain-api'),
    url(r'^supervisors',views.supervisor_api,name='StudentComplain-api'),
    url(r'^workers',views.worker_api,name='StudentComplain-api'),
    url(r'^newcomplain',views.create_complain_api,name='create-complain-api'),
    url(r'^addworker',views.add_worker_api,name='add-worker-api'),
    url(r'^removeworker/(?P<w_id>[0-9]+)',views.remove_worker_api,name='remove-worker-api')
]
