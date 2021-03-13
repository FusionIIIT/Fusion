from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'^user/detail/(?P<detailcomp_id1>[0-9]+)/$', views.complaint_details,name='detail-api'),
    url(r'^studentcomplain',views.StudentComplainApi,name='StudentComplain-api'),
    url(r'^caretakers',views.CaretakerApi,name='StudentComplain-api'),
    url(r'^supervisors',views.SupervisorApi,name='StudentComplain-api'),
    url(r'^workers',views.WorkerApi,name='StudentComplain-api')
]
