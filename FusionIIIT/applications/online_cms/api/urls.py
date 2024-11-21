from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^(?P<course_code>[A-Za-z0-9]+)/(?P<version>[\d.]+)', views.course, name='course'),
    url(r'^courses', views.course, name='courseview'),
    url(r'^attendance', views.view_attendance, name='view_attendance'),
    url(r'^(?P<course_code>[A-z0-9]+)/(?P<version>[\d.]+)/submit_marks$',views.submit_marks, name='submit_marks')
]