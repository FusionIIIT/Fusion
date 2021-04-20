from django.conf.urls import url

from . import views

app_name = 'dep'

urlpatterns = [

    url(r'^$', views.dep_main, name='dep'),
    url(r'^facView/$', views.faculty_view, name='faculty_view'),
    url(r'^All_Students/(?P<bid>[0-9]+)/$', views.all_students,name='all_students'),
    url(r'^approved/$', views.approved, name='approved'),
    url(r'^deny/$', views.deny, name='deny')
]
