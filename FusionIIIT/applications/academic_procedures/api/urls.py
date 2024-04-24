from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'^fac/', views.academic_procedures_faculty, name='faculty_procedures'),
    url(r'^stu/', views.academic_procedures_student, name='student_procedures'),
    url(r'^addThesis/', views.add_thesis, name='add_thesis'),
    url(r'^approve_thesis/(?P<id>[0-9]+)/', views.approve_thesis, name='approve_thesis'),

]
