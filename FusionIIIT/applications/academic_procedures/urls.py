from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^', views.academic_procedures, name='procedures'),
    url(r'addCourse/', views.add_course, name='addCourse'),
    url(r'^dropCourse/', views.drop_course, name='dropCourse'),
]
