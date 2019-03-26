from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.academic_procedures_redirect, name='redirect'),
    url(r'^main/', views.academic_procedures, name='procedures'),
    url(r'^register/', views.register, name='register'),
    url(r'^finalregister/', views.final_register, name='final_register'),
    url(r'^addCourse/', views.register, name='addCourse'),
    url(r'^dropCourse/', views.drop_course, name='dropCourse'),
    url(r'^branch-change/', views.approve_branch_change, name='branch_change'),
    url(r'^brach-change-request/', views.branch_change_request, name='branch_change_request'),
    url(r'^acad_person/verifyCourse/$', views.verify_course, name='verifyCourse'),
    url(r'^acad_person/student_list$', views.student_list, name='studentlist'),
    url(r'^acad_person/$', views.acad_person, name='acad_person'),
    url(r'^acad_person/verifyCourse/drop/$', views.dropcourseadmin, name='dropcourseadmin'),
    url(r'^branch-validate', views.approve_branch_change, name='branch_validate'),
    url(r'^acad_person/branch_change/$', views.acad_branch_change, name='acad_branch_change'),
    url(r'^PhD/$', views.phd_details, name='phd_details'),
    url(r'^addThesis/$', views.add_thesis, name='add_thesis'),
]
