from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'^fac/', views.academic_procedures_faculty, name='faculty_procedures'),
    url(r'^stu/', views.academic_procedures_student, name='student_procedures'),

]
