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
    url(r'^upload-grading-scheme/', views.create_grading_scheme, name='create_grading_scheme'),

    url(r'^modules/add/$', views.add_module, name='add_module'),
    url(r'^modules/delete/(?P<module_id>\d+)/$', views.delete_module, name='delete_module'),
   
    url(r'^slides/(?P<module_id>\d+)/add_document/$', views.add_slide, name='add_document'),
    url(r'^slides/delete/(?P<slide_id>\d+)/$', views.delete_slide, name='delete_document'),

]
