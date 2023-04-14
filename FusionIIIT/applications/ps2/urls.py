from django.conf.urls import url

from . import views

app_name = 'ps2'

urlpatterns = [
    url(r'^$', views.ps2, name='ps2'),
    url(r'^addstock/$', views.addstock, name='addstock'),
    url(r'^transfers/$', views.viewtransfers, name='viewtransfers'),  
    url(r'^transfers_form/$', views.addtransfers, name='addtransfers'),
    url(r'^report/$',views.report,name="report")
]