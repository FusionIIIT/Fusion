from django.conf.urls import url

from . import views

app_name = 'leave'

urlpatterns = [
    url(r'^$', views.leave, name='leave'),
    url(r'^process-request/', views.process_request, name='process_request'),
    url(r'^leave-requests/', views.get_leave_requests, name='get_leave_requests'),
]
