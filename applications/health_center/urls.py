from django.conf.urls import url

from .views import compounder_view, healthcenter, student_view, schedule_entry,doctor_entry,compounder_entry

app_name = 'healthcenter'

urlpatterns = [

    url(r'^$', healthcenter, name='healthcenter'),
    url(r'^compounder/$', compounder_view, name='compounder_view'),
    url(r'^student/$', student_view, name='student_view'),
    url(r'^schedule_entry', schedule_entry, name='schedule_entry'),
    url(r'^doctor_entry', doctor_entry, name='doctor_entry'),
    url(r'^compounder_entry', compounder_entry, name='compounder_entry'),    
]
