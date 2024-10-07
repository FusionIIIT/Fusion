from django import views
from django.conf.urls import url,include

from .views import *

app_name = 'healthcenter'

urlpatterns = [

    # health_center home page
    url(r'^$', healthcenter, name='healthcenter'),

    #views
    url(r'^compounder/view_prescription/(?P<prescription_id>[0-9]+)/$',compounder_view_prescription,name='view_prescription'),
    url(r'^compounder/view_file/(?P<file_id>[\w-]+)/$',view_file, name='view_file'),
    url(r'^compounder/$', compounder_view, name='compounder_view'),
    url(r'^student/$', student_view, name='student_view'),
    url(r'announcement/', announcement, name='announcement'),
    url(r'medical_profile/', medical_profile, name='medical_profile'),
    
    #database entry
    url(r'^schedule_entry', schedule_entry, name='schedule_entry'),
    url(r'^doctor_entry', doctor_entry, name='doctor_entry'),
    url(r'^compounder_entry', compounder_entry, name='compounder_entry'), 
   
    # #api
    # url(r'^api/',include('applications.health_center.api.urls'))
]