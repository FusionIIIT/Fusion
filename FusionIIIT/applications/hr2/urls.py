from django.conf.urls import url

from . import views

app_name = 'hr2'

urlpatterns = [

    url(r'^$',views.serviceBook, name='hr2'),
    url(r'^hradmin/$', views.hrAdmin, name='hradmin'),
    url(r'^edit/$', views.editEmployeeDetails, name='editEmployeeDetails'),
    
    # url(r'^servicebook/$', views.serviceBook, name='serviceBook'),

]

