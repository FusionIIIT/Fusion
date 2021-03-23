from django.conf.urls import url

from . import views

urlpatterns = [
    
    url(r'^students',views.student_api,name='student-get-api'),

    url(r'^courses',views.course_api,name='course-get-api'),

    url(r'^curriculum',views.curriculum_api,name='curriculum-get-api'),

]