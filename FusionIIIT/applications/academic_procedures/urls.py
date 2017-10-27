from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^main/', views.academic_procedures, name='procedures'),
    url(r'^register/', views.register, name='register'),
    url(r'^final-register/', views.final_register, name='final_register'),
    url(r'addCourse/', views.add_course, name='addCourse'),
    url(r'^dropCourse/', views.drop_course, name='dropCourse'),
    url(r'^branch-change/', views.approve_branch_change, name='branch_change'),
    url(r'^brach-change-request/', views.branch_change_request, name='branch_change_request'),
    url(r'^acad_person/', views.acad_person, name='staffs_details'),
    url(r'^branch-validate', views.approve_branch_change, name='branch_validate')
]
