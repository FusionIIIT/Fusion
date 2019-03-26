from django.conf.urls import url

from . import views

app_name = 'leave'

urlpatterns = [
    url(r'^$', views.leave, name='leave'),
    url(r'^process-request/', views.process_request, name='process_request'),
    url(r'^leave-requests/', views.get_leave_requests, name='get_leave_requests'),
    url(r'^delete-leave/', views.delete_leave, name='delete_leave'),
    url(r'^generate-form', views.generate_form, name='generate_form')
]
