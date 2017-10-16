from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^viewcourses/$', views.viewcourses, name='viewcourses'),
    url(r'^(?P<course_code>[A-z]+[0-9]+)/$', views.course,
        name='course'),
    # course_name will have blank spaces in between which is not possible
    # to send something in the url so as to identify which course it is.
    # students
    # lecturer
    url(r'^(?P<course_code>[A-z]+[0-9]+)/add_documents$', views.add_document,
        name='add_document'),
    url(r'^(?P<course_code>[A-z]+[0-9]+)/add_video$', views.add_videos,
        name='add_videos'),
]
