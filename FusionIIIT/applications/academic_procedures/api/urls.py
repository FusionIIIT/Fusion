from django.conf.urls import url
from . import views


urlpatterns = [
    # url(r'^stu/details', views.academic_procedures_student, name='student_procedures'),
    # url(r'^stu/pre_registration' , views.student_pre_registration , name = 'pre_registration'),
    url(r'^stu/final_registration' , views.final_registration , name = 'final_registration'),
    # url(r'^stu/add_one_course/' , views.add_one_course , name = 'add_one_course'),
    url(r'^stu/view_registration' , views.student_view_registration , name = 'view_registration'),
    url(r'^stu/view_offered_courses' , views.view_offered_courses , name = 'student_view_offered_courses'),
    # url(r'^stu/backlog_courses', views.student_backlog_courses , name = 'student_backlog_courses'),
    url(r'^stu/add_course/$' , views.add_course , name ='add_course') ,
    url(r'^stu/add_course_slots/$' , views.get_student_add_course_slots , name ='student_add_course_slots') ,
    url(r'^stu/add_course_courses/$' , views.get_student_add_courses , name ='student_add_courses') ,
    # url(r'^stu/drop_course/$' , views.drop_course , name = 'drop_course'),
    # url(r'^stu/swayam_add_course/', views.student_swayam_add_course, name = 'student_swayam_add_course'),
    # url(r'^stu/replaceCourse' , views.replaceCourse , name = 'replaceCourse')
    # url(r'^stu/next_sem_courses/', views.student_next_sem_courses, name = 'student_next_sem_courses'),
    # url(r'^stu/current_courseregistration/$', views.current_courseregistration, name='current_courseregistration'),
    url(r'^stu/preregistration/$', views.get_preregistration_data, name='get_preregistration_data'),
    url(r'^stu/preregistration/submit/$', views.submit_preregistration, name='preregistration-submit'),
    url(r'^stu/swayam_courses/$', views.get_swayam_registration_data, name='get_swayam_data'),
    url(r'^stu/swayam/submit/$', views.submit_swayam_registration, name='swayam-submit'),
    url(r'^stu/next_sem_courses/', views.student_next_sem_courses, name = 'student_next_sem_courses'),
    url(r'^stu/current_courseregistration/$', views.course_registration_view, name='current_courseregistration'),
    url(r'^stu/finalregistrationpage/$', views.final_registration_page, name='final_registration_page'),
    url(r'^fac/academic_procedures_faculty', views.academic_procedures_faculty_api, name='academic_procedures_faculty_api'),
    url(r'^stu/registered-slots/$', views.registered_slots, name='registered_slots'),
    url(r'^stu/batch-create/$', views.batch_create_requests, name='batch_create_requests'),
    url(r'^stu/replacement-requests/$', views.student_list_requests, name='list_requests'),
    url(r'^stu/registrations_drop/$', views.student_registrations_for_drop, name='student_registrations_drop'),
    url(r'^stu/drop-course/$',   views.drop_course, name='drop_course'),
    url(r'^stu/calendar/student/$', views.student_calendar_view, name='student-calendar'),
    url(r'^stu/course_reg/semesters/$', views.student_registration_semesters_view, name='student-course_reg-semesters'),
    url(r'^stu/feedback_questions/$', views.student_questions, name='student-questions'),
    url(r'^stu/feedback_submit/$', views.student_submit, name='student-feedback-submit'),



    url(r'^acad/change-requests/allocate_all/$', views.allocate_all, name='allocate_all'),
    url(r'^acad/view_registrations' , views.acad_view_reigstrations , name='acad_view_registrations'),
    url(r'^acad/verify_registration' , views.verify_registration , name='verify_registration'),
    url(r'^acad/verify_course/drop/$' , views.dropcourseadmin , name='dropcourseadmin'),
    url(r'^acad/verify_course' , views.verify_course , name='verify_course'),
    url(r'^acad/get_add_course_slots' , views.get_add_course_slots , name = 'get_add_course_slots' ),
    url(r'^acad/get_add_courses' , views.get_add_course_courses , name = 'get_add_course_slots' ),
    url(r'^acad/addCourse/', views.acad_add_course, name="acad_add_course"),
    url(r'^acad/get_course_list' , views.get_course_list , name = 'get_course_list' ),
    url(r'^acad/get_all_courses' , views.get_all_courses , name = 'get_all_courses' ),
    # url(r'^acad/gen_roll_list' , views.gen_roll_list , name = 'gen_roll_list' ),
    url(r'^acad/student_list/$' , views.student_list , name = 'student_list_with_slash' ),
    url(r'^acad/student_list$' , views.student_list , name = 'student_list_without_slash' ),
    url(r'^acad/course_list' , views.course_list , name = 'course_list' ),
    url(r'^acad/configure_pre_registration' , views.configure_pre_registration_date , name = 'configure_pre_registration'),
    url(r'^acad/configure_final_registration' , views.configure_final_registration_date , name = 'configure_final_registration'),
    # url(r'^acad/add_course_to_slot' , views.add_course_to_slot , name = 'add_course_to_slot'),
    # url(r'^acad/remove_course_from_slot' , views.remove_course_from_slot , name = 'remove_course_from_slot'),
    url(r'^acad/search_preregistration' , views.search_preregistration , name = 'search_preregistration'),
    url(r'^acad/delete_preregistration' , views.delete_preregistration , name = 'delete_preregistration'),
    url(r'^acad/allot_courses' , views.allot_courses , name = 'allot_courses'),
    url(r'^acad/change-requests/allocate_all/$', views.allocate_all, name='allocate_all'),
    url(r'^acad/replacement-requests/$', views.admin_list_requests, name='admin_list_requests'),
    url(r'^acad/student-search/$',views.student_search,name='student-search'),
    url(r"^acad/feedback_courses/$",    views.admin_course_list,   name="admin-course-list"),
    url(r"^acad/stats/all/$",  views.admin_all_stats,     name="admin-all-stats"),
    url(r'^acad/batch_change/batches/$', views.list_batches, name='batch-list'),
    url(r'^acad/batch_change/students/$', views.list_students_in_batch, name='batch-students'),
    url(r'^acad/batch_change/apply/$', views.apply_batch_changes, name='batch-apply'),
    url(r'^acad/promote/students/$', views.list_students_in_batch_semester_promotion, name='promote-batch-students'),
    url(r'^acad/promote/apply/$', views.apply_promotion, name='promote-apply'),
    url(r'^get_next_sem_courses' , views.get_next_sem_courses , name= 'get_next_sem_courses'),


    url(r'^fac/view_assigned_courses' , views.faculty_assigned_courses , name = 'faculty_assigned_courses'),
    # url(r'^fac/get_roll_list' , views.fetch_roll_list , name = 'fetch_roll_list'),
    url(r"^inst/courses/$", views.inst_courses, name="inst-courses"),
    url(r"^inst/stats/all/$", views.inst_all_stats, name="inst-all-stats"),



    url(r'^get_user_info' , views.get_user_info , name  = 'get_user_info'),

    #  these urls were designed previously and are not working any more

    # url(r'^fac/', views.academic_procedures_faculty, name='faculty_procedures'),
    # url(r'^stu', views.academic_procedures_student, name='student_procedures'),
    # url(r'^addThesis/', views.add_thesis, name='add_thesis'),
    # url(r'^approve_thesis/(?P<id>[0-9]+)/', views.approve_thesis, name='approve_thesis')
    url(r'^upload-excel_relacement' , views.upload_excel_replacement , name  = 'upload_excel_replacement'),


    url(r'^api/tas/$', views.tas_list, name='tas_list'),
    url(r'^api/faculties/$', views.faculties_list, name='faculties_list'),

    #pg urls
    url(r'^hod/students/$',            views.hod_students),
    url(r'^hod/assign/$',              views.hod_assign_manual),
    url(r'^hod/assign/upload-excel/$', views.hod_upload_excel),
    url(r'^hod/pending/$',             views.hod_pending),
    url(r'^hod/approved/$',            views.hod_approved),
    url(r'^hod/approve/(?P<sid>\d+)/$', views.hod_approve),

    # pg Faculty
    url(r'^faculty/assignments/$',     views.faculty_assignments),
    url(r'^faculty/pending/$',         views.faculty_pending),
    url(r'^faculty/approved/$',        views.faculty_approved),
    url(r'^faculty/approve/(?P<sid>\d+)/$', views.faculty_approve),

    # pg TA
    url(r'^ta/stipends/$',             views.ta_stipends),
]