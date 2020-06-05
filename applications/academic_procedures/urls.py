from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.academic_procedures_redirect, name='redirect'),
    url(r'^main/', views.academic_procedures, name='procedures'),
    url(r'^register/', views.register, name='register'),
    url(r'^pre_registration/', views.pre_registration, name='pre_register'),
    url(r'^final_registration/', views.final_registration, name='final_register'),
    url(r'^addCourse/', views.register, name='addCourse'),
    url(r'^drop_course/', views.drop_course, name='drop_course'),
    url(r'^branch-change/', views.approve_branch_change, name='branch_change'),
    url(r'^brach-change-request/', views.branch_change_request, name='branch_change_request'),
    url(r'^acad_person/verifyCourse/$', views.verify_course, name='verifyCourse'),
    url(r'^acad_person/student_list$', views.student_list, name='studentlist'),
    url(r'^acad_person/$', views.acad_person, name='acad_person'),
    url(r'^acad_person/verifyCourse/drop/$', views.dropcourseadmin, name='dropcourseadmin'),
    url(r'^branch-validate', views.approve_branch_change, name='branch_validate'),
    url(r'^acad_person/branch_change/$', views.acad_branch_change, name='acad_branch_change'),
    url(r'^stu/', views.academic_procedures_student),
    url(r'^fac/', views.academic_procedures_faculty, name='faculty_procedures'),
    url(r'^addThesis/$', views.add_thesis, name='add_thesis'),
    url(r'^process_verification_request/$', views.process_verification_request),
    url(r'^teaching_credit/$', views.teaching_credit_register),
    url(r'^course_marks_data/$', views.course_marks_data),
    url(r'^submit_marks/$', views.submit_marks),
    url(r'^verify_course_marks_data/$', views.verify_course_marks_data),
    url(r'^verify_marks/$', views.verify_marks),
    url(r'^announce_results/$', views.announce_results),
    url(r'^generate_grade_pdf/$', views.generate_grade_pdf),
    url(r'^manual_grade_submission/$', views.manual_grade_submission),
    url(r'^generate_result_pdf/$', views.generate_result_pdf),
    url(r'^generate_grade_sheet_pdf/$', views.generate_grade_sheet_pdf),
    url(r'^test/$', views.test),
    url(r'^test_ret/$', views.test_ret),
    
    

]
