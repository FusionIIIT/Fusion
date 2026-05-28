from django.conf.urls import url,include

from .views import compounder_view, healthcenter, student_view, schedule_entry,doctor_entry,compounder_entry

app_name = 'healthcenter'

urlpatterns = [

    #health_center home page
    url(r'^$', healthcenter, name='healthcenter'),

    #views
    url(r'^compounder/$', compounder_view, name='compounder_view'),
    url(r'^student/$', student_view, name='student_view'),
    
    #database entry
    url(r'^schedule_entry', schedule_entry, name='schedule_entry'),
    url(r'^doctor_entry', doctor_entry, name='doctor_entry'),
    url(r'^compounder_entry', compounder_entry, name='compounder_entry'),  
   
    #api
    url(r'^api/',include('applications.health_center.api.urls'))
]
