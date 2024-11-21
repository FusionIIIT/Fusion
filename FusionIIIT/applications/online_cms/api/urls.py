from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^(?P<course_code>[A-Za-z0-9]+)/(?P<version>[\d.]+)/$', views.course, name='course'),
    url(r'^courses', views.courseview, name='courseview'),
]
