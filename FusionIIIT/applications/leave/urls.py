from django.conf.urls import url,include

from . import views

app_name = 'leave'

urlpatterns = [
    url(r'^$', views.leave, name='leave'),
    url(r'^process-request/', views.process_request, name='process_request'),
    url(r'^leave-requests/', views.get_leave_requests, name='get_leave_requests'),
    url(r'^delete-leave/', views.delete_leave, name='delete_leave'),
    url(r'^generate_form', views.generate_form, name='generate_form'),
    url(r'^generate_form_offline', views.generate_form_offline, name='generate_form_offline'),
    url(r'^leavemanager', views.leavemanager, name='leavemanager'),
    url(r'^elm/$', views.elm_dashboard, name='elm-dashboard'),
    url(r'^elm/tasks/(?P<task_id>[0-9]+)/action/$', views.elm_task_action, name='elm-task-action'),
    url(r'^elm/leave/(?P<leave_id>[0-9]+)/withdraw/$', views.elm_withdraw, name='elm-withdraw'),
    url(r'^elm/leave/(?P<leave_id>[0-9]+)/change/$', views.elm_change, name='elm-change'),
    url(r'^elm/leave/(?P<leave_id>[0-9]+)/substitute/$', views.elm_substitute, name='elm-substitute'),
    url(r'^elm/leave/(?P<leave_id>[0-9]+)/modify/$', views.elm_modify, name='elm-modify'),
    url(r'^elm/leave/(?P<leave_id>[0-9]+)/export/$', views.elm_export, name='elm-export'),
    url(r'^elm/offline/$', views.elm_offline_entry, name='elm-offline'),
    url(r'^api/',include('applications.leave.api.urls'))
]
