from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^main/', views.academic_procedures, name='procedures'),
    url(r'^register/', views.register, name='register'),
    url(r'^finalregister/', views.final_register, name='final_register'),
    url(r'addCourse/', views.add_course, name='addCourse'),
    url(r'^dropCourse/', views.drop_course, name='dropCourse'),
]
