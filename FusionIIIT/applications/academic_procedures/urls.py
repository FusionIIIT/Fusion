from django.conf.urls import url, include
from . import views
appname = 'procedures'
urlpatterns = [
    url(r'^$', views.academic_procedures_redirect, name='redirect'),
    url(r'^main/', views.academic_procedures, name='procedures'),
    url(r'^register/', views.register, name='register'),
    url(r'^pre_registration/', views.pre_registration, name='pre_register'),
    url(r'^auto_pre_registration/', views.auto_pre_registration, name='automatic_pre_register'),

    url(r'^final_registration/', views.final_registration, name='final_register'),
    url(r'^addCourse/', views.add_courses, name='addCourse'),
    url(r'^add_one_course/' , views.add_one_course , name = 'add_one_course'),
    url(r'^drop_course/', views.drop_course, name='drop_course'),
    url(r'^replaceCourse/', views.replace_courses, name='drop_course'),
    url(r'^branch-change/', views.approve_branch_change, name='branch_change'),
    url(r'^brach-change-request/', views.branch_change_request,
        name='branch_change_request'),
    url(r'^acad_person/verifyCourse/', views.verify_course, name='verifyCourse'),
    url(r'^acad_person/addCourse/', views.acad_add_course, name="acad_add_course"),
    url(r'^acad_person/student_list$', views.student_list, name='studentlist'),
    url(r'^acad_person/course_list$', views.course_list, name='courseList'),
    url(r'^acad_person/$', views.acad_person, name='acad_person'),
    url(r'^acad_person/verifyCourse/drop/$',
        views.dropcourseadmin, name='dropcourseadmin'),
    url(r'^branch-validate', views.approve_branch_change, name='branch_validate'),
    url(r'^acad_person/branch_change/$',
        views.acad_branch_change, name='acad_branch_change'),
    url(r'^stu/', views.academic_procedures_student),
    url(r'^fac/', views.academic_procedures_faculty, name='faculty_procedures'),
    url(r'^account/$', views.account),
    url(r'^addThesis/$', views.add_thesis, name='add_thesis'),
    url(r'^process_verification_request/$', views.process_verification_request),
    url(r'^auto_process_verification_request/$', views.auto_process_verification_request),
    url(r'^teaching_credit/$', views.teaching_credit_register),
    url(r'^course_marks_data/$', views.course_marks_data),  # --
    url(r'^submit_marks/$', views.submit_marks),  # --
    url(r'^verify_course_marks_data/$', views.verify_course_marks_data),  # --
    url(r'^verify_marks/$', views.verify_marks),
    url(r'^announce_results/$', views.announce_results),
    url(r'^generate_grade_pdf/$', views.generate_grade_pdf),
    url(r'^manual_grade_submission/$', views.manual_grade_submission),  # --
    url(r'^generate_result_pdf/$', views.generate_result_pdf),
    url(r'^generate_grade_sheet_pdf/$', views.generate_grade_sheet_pdf),
    url(r'^test/$', views.test),
    url(r'^bonafide_pdf/$', views.Bonafide_form),
    url(r'^test_ret/$', views.test_ret),

    url(r'^api/', include('applications.academic_procedures.api.urls')),


    url(r'^faculty_data/$', views.facultyData, name='faculty_data'),
    url(r'^ACF/$', views.ACF, name='ACF'),
    url(r'^MTSGF/$', views.MTSGF),
    url(r'^PHDPE/$', views.PHDPE),
    url(r'^update_assistantship/$', views.update_assistantship),
    url(r'^update_mtechsg/$', views.update_mtechsg),
    url(r'^update_phdform/$', views.update_phdform),
    url(r'^update_dues/$', views.update_dues),
    url(r'^dues_pdf/$', views.dues_pdf),
    url(r'^acad_person/gen_course_list$', views.gen_course_list, name='gen_course_list'),
    url(r'^update_acad_assistantship/$', views.update_acad_assis),
    url(r'^update_account_assistantship/$', views.update_account_assistantship),
    url(r'^update_hod_assistantship/$', views.update_hod_assistantship),
    url(r'^mdue/$', views.mdue),
    url(r'^assis_stat/$', views.assis_stat),
    url(r'^acad_person/allot_courses/' , views.allot_courses, name='allot_courses'),

    url(r'^acad_person/get_next_sem_courses/' , views.get_next_sem_courses , name = 'get_next_sem_courses'),

    url(r'^acad_person/remove_course_from_slot/' , views.remove_course_from_slot , name = 'remove_course_from_slot'),
    url(r'^acad_person/add_course_to_slot/' , views.add_course_to_slot , name = 'add_course_to_slot'),


]
