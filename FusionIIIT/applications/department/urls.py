from django.conf.urls import url
from django.urls import include 

from . import views

app_name = 'dep'

urlpatterns = [

    url(r'^$', views.dep_main, name='dep'),
    url(r'^facView/$', views.faculty_view, name='faculty_view'),
    url(r'^staffView/$', views.staff_view, name='staff_view'),
    url(r'All_Students/(?P<bid>[0-9]+)/$', views.all_students,name='all_students'),
    url(r'alumni/$', views.alumni, name='alumni'),
    url(r'^approved/$', views.approved, name='approved'),
    url(r'^deny/$', views.deny, name='deny'),
    
    url(r'^api/', include("applications.department.api.urls"))
    
]