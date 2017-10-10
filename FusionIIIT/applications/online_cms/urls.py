from django.conf.urls import url, include
from django.contrib import admin
from . import views
urlpatterns = [

    url(r'^viewcourses/$',views.viewcourses,name='viewcourses'),
    url(r'^(?P<course_code>[A-z]+)/$',views.courses,name='courses')
    # because course_name will have blank spaces in between which is not possible and i need to send something in the url so as to identify which course it is.
    #students
    #lecturer

]
