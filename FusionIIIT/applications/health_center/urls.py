from django import views
from django.conf.urls import url,include

from .views import *

app_name = 'healthcenter'

urlpatterns = [

    #health_center home page
    url(r'^$', healthcenter, name='healthcenter'),

    #views
    url(r'^compounder/$', compounder_view, name='compounder_view'),
    url(r'^student/$', student_view, name='student_view'),
    url(r'announcement/', announcement, name='announcement'),
    
    #database entry
    url(r'^schedule_entry', schedule_entry, name='schedule_entry'),
    url(r'^doctor_entry', doctor_entry, name='doctor_entry'),
    url(r'^compounder_entry', compounder_entry, name='compounder_entry'),  
    # url(r'^fetch_designations', fetch_designations, name='fetch_designations'),  
    url(r'^medical_relief', medicalrelief, name='medical_relief'),  
   
    #api
    url(r'^api/',include('applications.health_center.api.urls'))
]