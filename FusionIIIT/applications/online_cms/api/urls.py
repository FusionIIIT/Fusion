from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^(?P<course_code>[A-Za-z0-9]+)/(?P<version>[\d.]+)', views.course, name='course'),
    url(r'^courses', views.course, name='courseview'),
    url(r'^attendance', views.view_attendance, name='view_attendance'),
    url(r'^(?P<course_code>[A-z0-9]+)/(?P<version>[\d.]+)/submit_marks$',views.submit_marks, name='submit_marks'),
    url(r'^modules/add/$', views.add_module, name='add_module'),
    url(r'^modules/delete/(?P<module_id>\d+)/$', views.delete_module, name='delete_module'),
    
    url(r'^slides/(?P<module_id>\d+)/add_document/$', views.add_slide, name='add_document'),
    url(r'^slides/delete/(?P<slide_id>\d+)/$', views.delete_slide, name='delete_document'),
]