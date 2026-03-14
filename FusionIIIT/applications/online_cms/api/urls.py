# from django.conf.urls import url

# from . import views

# urlpatterns = [
#     url(r'^courses', views.viewcourses_serialized, name="registered_courses")
# ]
from django.conf.urls import url
# from .views import course
from . import views
urlpatterns = [
    # url(r'^courses', CourseListView.as_view(), name='courses'),
    url(r'^(?P<course_code>[A-Za-z0-9]+)/(?P<version>[\d.]+)/$', views.course, name='course'),
    url(r'^courses', views.courseview, name='courseview'),
]
