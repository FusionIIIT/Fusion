from django.conf.urls import url

from . import views

app_name = 'mess'

urlpatterns = [

    url(r'^$', views.mess, name='mess'),
    url(r'^placeorder/', views.placeorder, name='placeorder'),
    url(r'^submit/', views.submit, name='submit'),
    url(r'^vacasubmit/', views.vacasubmit, name='vacasubmit'),
    url(r'^menusubmit/', views.menusubmit, name='menusubmit'),
    url(r'^regsubmit/', views.regsubmit, name='regsubmit'),
    url(r'^regadd/', views.regadd, name='regadd'),
    url(r'^(?P<ap_id>[0-9]+)/response/', views.response, name='response'),
    url(r'^(?P<ap_id>[0-9]+)/processvacafood/', views.processvacafood, name='processvacafood'),
    url(r'^leave', views.leaverequest, name='leaverequest'),
    url(r'^invitation', views.invitation, name='invitation'),
    url(r'^minutes', views.minutes, name='minutes'),
    url(r'^placerequest', views.placerequest, name='placerequest'),
    url(r'^(?P<ap_id>[0-9]+)/responserebate/', views.responserebate, name='responserebate'),
    url(r'^(?P<ap_id>[0-9]+)/responsespl/', views.responsespl, name='responsespl'),
    url(r'^updatecost', views.updatecost, name='updatecost'),

]
