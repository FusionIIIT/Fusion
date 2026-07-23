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
    url(r'^stu/swayam/replace/check/$', views.swayam_replace_check, name='swayam-replace-check'),
    url(r'^stu/swayam/replace/slots/$', views.swayam_replace_slots, name='swayam-replace-slots'),
    url(r'^stu/swayam/replace/courses/$', views.swayam_replace_courses, name='swayam-replace-courses'),
    url(r'^stu/swayam/target/slots/$', views.swayam_target_slots, name='swayam-target-slots'),
    url(r'^stu/swayam/target/courses/$', views.swayam_target_courses, name='swayam-target-courses'),
    url(r'^stu/swayam/current/courses/$', views.swayam_current_courses, name='swayam-current-courses'),
    url(r'^stu/swayam/replace/submit/$', views.swayam_replace_submit, name='swayam-replace-submit'),
    url(r'^stu/swayam/requests/$', views.student_swayam_requests, name='student-swayam-requests'),
    url(r'^acad/swayam/requests/$', views.admin_swayam_list_requests, name='admin-swayam-list'),
    url(r'^acad/swayam/approve/$', views.admin_swayam_approve, name='admin-swayam-approve'),
    url(r'^acad/swayam/reject/$', views.admin_swayam_reject, name='admin-swayam-reject'),
    url(r'^acad/swayam/revert/$', views.admin_swayam_revert, name='admin-swayam-revert'),
    url(r'^acad/swayam/delete/$', views.admin_swayam_delete, name='admin-swayam-delete'),
    url(r'^stu/next_sem_courses/', views.student_next_sem_courses, name = 'student_next_sem_courses'),
    url(r'^stu/current_courseregistration/$', views.course_registration_view, name='current_courseregistration'),
    url(r'^stu/finalregistrationpage/$', views.final_registration_page, name='final_registration_page'),
    url(r'^fac/academic_procedures_faculty', views.academic_procedures_faculty_api, name='academic_procedures_faculty_api'),
    url(r'^stu/registered-slots/$', views.registered_slots, name='registered_slots'),
    url(r'^stu/batch-create/$', views.batch_create_requests, name='batch_create_requests'),
    url(r'^stu/replacement-requests/$', views.student_list_requests, name='list_requests'),
    url(r'^stu/registrations_drop/$', views.student_registrations_for_drop, name='student_registrations_drop'),
    url(r'^stu/drop-course/$',   views.drop_course, name='drop_course'),
    url(r'^stu/drop-requests/$', views.student_list_drop_requests, name='student_list_drop_requests'),
    url(r'^stu/add-requests/$', views.student_list_add_requests, name='student_list_add_requests'),
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
    url(r'^acad/replacement-requests/revert/$', views.revert_replacement_to_pending, name='revert_replacement_to_pending'),
    url(r'^acad/replacement-requests/delete/$', views.delete_replacement_requests, name='delete_replacement_requests'),
    url(r'^acad/drop-requests/$', views.admin_list_drop_requests, name='admin_list_drop_requests'),
    url(r'^acad/drop-requests/approve/$', views.approve_drop_requests, name='approve_drop_requests'),
    url(r'^acad/drop-requests/delete/$', views.delete_drop_requests, name='delete_drop_requests'),
    url(r'^acad/add-requests/$', views.admin_list_add_requests, name='admin_list_add_requests'),
    url(r'^acad/add-requests/approve/$', views.approve_add_requests, name='approve_add_requests'),
    url(r'^acad/add-requests/delete/$', views.delete_add_requests, name='delete_add_requests'),
    url(r'^acad/student-search/$',views.student_search,name='student-search'),
    url(r"^acad/feedback_courses/$",    views.admin_course_list,   name="admin-course-list"),
    url(r"^acad/stats/all/$",  views.admin_all_stats,     name="admin-all-stats"),
    url(r'^acad/batch_change/batches/$', views.list_batches, name='batch-list'),
    url(r'^acad/batch_change/students/$', views.list_students_in_batch, name='batch-students'),
    url(r'^acad/batch_change/apply/$', views.apply_batch_changes, name='batch-apply'),
    url(r'^acad/promote/students/$', views.list_students_in_batch_semester_promotion, name='promote-batch-students'),
    url(r'^acad/promote/apply/$', views.apply_promotion, name='promote-apply'),
    url(r'^acad/demote/apply/$', views.apply_demotion, name='demote-apply'),
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
    
    # ========================================================================
    # PhD-SPECIFIC URLS (Added for PhD student management)
    # ========================================================================

    # PhD Thesis Registration endpoints

    # Student endpoints
    url(r'^stu/thesis/$', views.student_thesis_api, name='student-thesis'),
    url(r'^stu/thesis/download/$', views.student_download_pdf_api, name='student-thesis-download'),

    # Faculty list for dropdowns
    url(r'^faculty/$', views.faculty_list_api, name='faculty-list'),

    # Supervisor endpoints
    url(r'^supervisor/dashboard/$', views.supervisor_thesis_topic_dashboard, name='supervisor-dashboard'),
    url(r'^supervisor/thesis/(?P<pk>\d+)/review/$', views.supervisor_review_api, name='supervisor-thesis-review'),

    # HOD endpoints
    url(r'^hod/dashboard/$', views.hod_dashboard, name='hod-dashboard'),
    url(r'^hod/thesis/(?P<pk>\d+)/review/$', views.hod_review_api, name='hod-thesis-review'),

    # Dean endpoints
    url(r'^dean/dashboard/$', views.dean_dashboard, name='dean-dashboard'),
    url(r'^dean/thesis/(?P<pk>\d+)/review/$', views.dean_review_api, name='dean-thesis-review'),
    url(r'^dean/thesis/(?P<pk>\d+)/generate/$', views.dean_generate_pdf_api, name='dean-thesis-generate'),

    # PhD Seminar endpoints

    # Student
    url(r'^seminar-reports/$', views.list_reports),
    url(r'^seminar-reports/create/(?P<thesis_pk>\d+)/$', views.create_report),
    url(r'^seminar-reports/(?P<pk>\d+)/$', views.detail_report),

    # RPC
    url(r'^seminar-reports/list/$', views.rpc_seminar_list),
    url(r'^seminar-reports/(?P<pk>\d+)/rpc-detail/$', views.rpc_detail),
    url(r'^seminar-reports/(?P<pk>\d+)/rpc-consent/$', views.rpc_consent),
    url(r'^seminar-reports/(?P<pk>\d+)/rpc-finalize/$', views.rpc_finalize),

    # ========================================================================
    # Thesis Slot Semester-Level Registration (Enrollment)
    # ========================================================================
    # Student
    url(r'^stu/thesis-enrollment/$', views.student_thesis_enrollment_api, name='student-thesis-enrollment'),
    # Acad Admin
    url(r'^acadadmin/thesis-enrollments/$', views.admin_thesis_enrollment_list, name='admin-thesis-enrollment-list'),
    url(r'^acadadmin/thesis-enrollments/verify/$', views.admin_verify_enrollments, name='admin-verify-enrollments'),
    url(r'^acadadmin/thesis-enrollments/reject/$', views.admin_reject_enrollments, name='admin-reject-enrollments'),

    # ========================================================================
    # Progress Seminar Slot Semester-Level Registration (Enrollment)
    # ========================================================================
    # Student
    url(r'^stu/progress-seminar-enrollment/$', views.student_progress_seminar_enrollment_api,
        name='student-progress-seminar-enrollment'),
    # Acad Admin
    url(r'^acadadmin/progress-seminar-enrollments/$', views.admin_progress_seminar_enrollment_list,
        name='admin-progress-seminar-enrollment-list'),
    url(r'^acadadmin/progress-seminar-enrollments/verify/$', views.admin_verify_progress_seminar_enrollments,
        name='admin-verify-progress-seminar-enrollments'),
    url(r'^acadadmin/progress-seminar-enrollments/reject/$', views.admin_reject_progress_seminar_enrollments,
        name='admin-reject-progress-seminar-enrollments'),

    # ========================================================================
    # Teaching Credit Slot Semester-Level Registration (Enrollment)
    # ========================================================================
    # Student
    url(r'^stu/teaching-credit-enrollment/$', views.student_teaching_credit_enrollment_api,
        name='student-teaching-credit-enrollment'),
    # Acad Admin
    url(r'^acadadmin/teaching-credit-enrollments/$', views.admin_teaching_credit_enrollment_list,
        name='admin-teaching-credit-enrollment-list'),
    url(r'^acadadmin/teaching-credit-enrollments/verify/$', views.admin_verify_teaching_credit_enrollments,
        name='admin-verify-teaching-credit-enrollments'),
    url(r'^acadadmin/teaching-credit-enrollments/reject/$', views.admin_reject_teaching_credit_enrollments,
        name='admin-reject-teaching-credit-enrollments'),

    # ========================================================================
    # PhD Course (Coursework) Registration — standalone workflow, independent
    # of the UG/PG backlog add-course flow (add_course / CourseAddRequest)
    # ========================================================================
    # Student
    url(r'^stu/phd/status/$', views.phd_student_status, name='phd-student-status'),
    url(r'^stu/phd/course-slots/$', views.phd_course_slots, name='phd-course-slots'),
    url(r'^stu/phd/course-slots/courses/$', views.phd_course_slot_courses, name='phd-course-slot-courses'),
    url(r'^stu/phd/course-request/$', views.phd_submit_course_request, name='phd-submit-course-request'),
    url(r'^stu/phd/my-course-requests/$', views.phd_my_course_requests, name='phd-my-course-requests'),
    # Acad Admin
    url(r'^acadadmin/phd/course-requests/$', views.phd_admin_list_requests, name='phd-admin-list-requests'),
    url(r'^acadadmin/phd/course-requests/process/$', views.phd_admin_process_requests, name='phd-admin-process-requests'),

    # PhD Thesis Evaluation (block-based S/X grades)
    # Supervisor — all blocks for a student are graded and submitted together
    url(r'^supervisor/thesis-grades/$',          views.supervisor_thesis_grades,       name='supervisor-thesis-grades'),
    # All blocks comprehensive upload
    url(r'^supervisor/thesis-grades-all-template/$', views.supervisor_download_all_thesis_grades_template, name='supervisor-thesis-grades-all-template'),
    url(r'^supervisor/thesis-grades-all/upload/$', views.supervisor_upload_all_thesis_grades, name='supervisor-thesis-grades-all-upload'),
    url(r'^supervisor/thesis-grades-all/bulk-submit/$', views.supervisor_bulk_submit_all_thesis_grades, name='supervisor-thesis-grades-all-bulk-submit'),
    # Acad Admin
    url(r'^acadadmin/thesis-grades/$',           views.admin_thesis_grades_list,       name='admin-thesis-grades-list'),
    url(r'^acadadmin/thesis-grades/verify/$',    views.admin_verify_thesis_grades,     name='admin-thesis-grades-verify'),
    url(r'^acadadmin/thesis-grades/announce/$',  views.admin_announce_thesis_grades,   name='admin-thesis-grades-announce'),

    # PhD Thesis Submission

    # Student
    url(r'^thesis/submit/$', views.thesis_submit, name='thesis_submit'),

    # Supervisor
    url(r'^thesis/supervisor-dashboard/$', views.supervisor_dashboard, name='supervisor_dashboard'),
    url(r'^thesis/submission-detail/(?P<submission_id>\d+)/$', views.supervisor_submission_detail, name='supervisor_submission_detail'),
    url(r'^thesis/supervisor-assign/$', views.supervisor_assign, name='supervisor_assign'),

    # Dean (panel approval + invitation dispatch)
    url(r'^thesis/dean-dashboard/$', views.dean_panel_dashboard, name='dean_panel_dashboard'),
    url(r'^thesis/dean-panel-approve/$', views.dean_panel_approve, name='dean_panel_approve'),
    url(r'^thesis/dean-send-invitations/$', views.dean_send_invitations, name='dean_send_invitations'),

    # Director
    url(r'^thesis/director-dashboard/$', views.director_dashboard, name='director_dashboard'),
    url(r'^thesis/director-approve/$', views.director_approve, name='director_approve'),

    # Professor Invitation (External reviewers)
    url(r'^invitation/(?P<token>[0-9a-f-]+)/(?P<action>accept|reject)/$',
        views.invitation_action, name='invitation_action'),

    # Review Form (External reviewers)
    url(r'^review/(?P<token>[0-9a-f-]+)/$', views.review_detail, name='review_detail'),

    # ========================================================================
    # PhD Comprehensive Examination
    # ========================================================================

    # Student
    url(r'^stu/comprehensive-exam/$', views.student_comprehensive_exam_api, name='student-comprehensive-exam'),
    url(r'^stu/comprehensive-exam/attempt/(?P<attempt_pk>\d+)/opt-subjects/$',
        views.student_opt_subjects_api, name='student-comprehensive-exam-opt-subjects'),

    # Supervisor
    url(r'^supervisor/comprehensive-exam/dashboard/$',
        views.supervisor_comprehensive_exam_dashboard, name='supervisor-comprehensive-exam-dashboard'),
    url(r'^supervisor/comprehensive-exam/student-info/(?P<roll_no>[^/]+)/$',
        views.supervisor_student_academic_info, name='supervisor-comprehensive-exam-student-info'),
    url(r'^supervisor/comprehensive-exam/propose/$',
        views.supervisor_propose_comprehensive_exam, name='supervisor-comprehensive-exam-propose'),
    url(r'^supervisor/comprehensive-exam/(?P<pk>\d+)/$',
        views.supervisor_comprehensive_exam_detail, name='supervisor-comprehensive-exam-detail'),
    url(r'^supervisor/comprehensive-exam/(?P<pk>\d+)/resubmit/$',
        views.supervisor_resubmit_proposal, name='supervisor-comprehensive-exam-resubmit'),
    url(r'^supervisor/comprehensive-exam/(?P<pk>\d+)/float-subjects/$',
        views.supervisor_float_subjects, name='supervisor-comprehensive-exam-float-subjects'),
    url(r'^supervisor/comprehensive-exam/attempt/(?P<attempt_pk>\d+)/confirm-subjects/$',
        views.supervisor_confirm_opted_subjects, name='supervisor-comprehensive-exam-confirm-subjects'),
    url(r'^courses/dropdown/$', views.list_courses_for_dropdown, name='list-courses-dropdown'),

    # Academic Office (acadadmin)
    url(r'^acadadmin/comprehensive-exam/$',
        views.academic_office_comprehensive_exam_list, name='academic-office-comprehensive-exam-list'),
    url(r'^acadadmin/comprehensive-exam/(?P<pk>\d+)/verify/$',
        views.academic_office_verify_comprehensive_exam, name='academic-office-comprehensive-exam-verify'),

    # Convener (Dean Academic stands in for DPGC/PGCS for now)
    url(r'^dean/comprehensive-exam/dashboard/$',
        views.convener_comprehensive_exam_dashboard, name='convener-comprehensive-exam-dashboard'),
    url(r'^dean/comprehensive-exam/(?P<pk>\d+)/approve-committee/$',
        views.convener_approve_committee, name='convener-comprehensive-exam-approve-committee'),
    url(r'^dean/comprehensive-exam/attempt/(?P<attempt_pk>\d+)/report/$',
        views.convener_submit_result, name='convener-comprehensive-exam-report'),

    # HOD (as discipline coordinator)
    url(r'^hod/comprehensive-exam/dashboard/$',
        views.hod_comprehensive_exam_dashboard, name='hod-comprehensive-exam-dashboard'),
    url(r'^hod/comprehensive-exam/attempt/(?P<attempt_pk>\d+)/review-subjects/$',
        views.hod_review_subjects, name='hod-comprehensive-exam-review-subjects'),

    # ========================================================================
    # PhD Open Seminar
    # ========================================================================

    # Shared
    url(r'^supervisor/open-seminar/eligibility/(?P<roll_no>[^/]+)/$',
        views.open_seminar_eligibility_preview, name='open-seminar-eligibility-preview'),

    # Student
    url(r'^stu/open-seminar/$', views.student_open_seminar_api, name='student-open-seminar'),

    # Supervisor
    url(r'^supervisor/open-seminar/dashboard/$',
        views.supervisor_open_seminar_dashboard, name='supervisor-open-seminar-dashboard'),
    url(r'^supervisor/open-seminar/propose/$',
        views.supervisor_propose_open_seminar, name='supervisor-open-seminar-propose'),
    url(r'^supervisor/open-seminar/(?P<pk>\d+)/$',
        views.supervisor_open_seminar_detail, name='supervisor-open-seminar-detail'),
    url(r'^supervisor/open-seminar/(?P<pk>\d+)/resubmit/$',
        views.supervisor_resubmit_open_seminar, name='supervisor-open-seminar-resubmit'),
    url(r'^supervisor/open-seminar/(?P<pk>\d+)/retry/$',
        views.supervisor_retry_open_seminar, name='supervisor-open-seminar-retry'),

    # Convener (Dean Academic stands in for DPGC/PGCS for now)
    url(r'^dean/open-seminar/dashboard/$',
        views.convener_open_seminar_dashboard, name='convener-open-seminar-dashboard'),
    url(r'^dean/open-seminar/attempt/(?P<attempt_pk>\d+)/approve-committee/$',
        views.convener_approve_open_seminar_committee, name='convener-open-seminar-approve-committee'),
    url(r'^dean/open-seminar/attempt/(?P<attempt_pk>\d+)/report/$',
        views.convener_submit_open_seminar_report, name='convener-open-seminar-report'),

    # Dean Nominee (ad-hoc faculty appointment)
    url(r'^faculty/open-seminar-nominee/dashboard/$',
        views.dean_nominee_open_seminar_dashboard, name='dean-nominee-open-seminar-dashboard'),
    url(r'^faculty/open-seminar-nominee/attempt/(?P<attempt_pk>\d+)/report/$',
        views.dean_nominee_submit_open_seminar_report, name='dean-nominee-open-seminar-report'),

    # ========================================================================
    # PhD Teaching Credit
    # ========================================================================

    # Student
    url(r'^stu/teaching-credit/$', views.student_teaching_credit_api, name='student-teaching-credit'),
    url(r'^stu/teaching-credit/propose/$',
        views.student_propose_teaching_credit, name='student-teaching-credit-propose'),
    url(r'^stu/teaching-credit/(?P<pk>\d+)/$',
        views.student_teaching_credit_detail, name='student-teaching-credit-detail'),
    url(r'^stu/teaching-credit/(?P<pk>\d+)/resubmit/$',
        views.student_resubmit_teaching_credit, name='student-teaching-credit-resubmit'),
    url(r'^stu/teaching-credit/evaluation-targets/$',
        views.student_teaching_credit_evaluation_targets, name='student-teaching-credit-evaluation-targets'),
    url(r'^stu/teaching-credit/(?P<pk>\d+)/evaluate/$',
        views.student_submit_teaching_credit_evaluation, name='student-teaching-credit-evaluate'),

    # HOD
    url(r'^hod/teaching-credit/dashboard/$',
        views.hod_teaching_credit_dashboard, name='hod-teaching-credit-dashboard'),
    url(r'^hod/teaching-credit/(?P<pk>\d+)/decide/$',
        views.hod_decide_teaching_credit, name='hod-teaching-credit-decide'),
    url(r'^hod/teaching-credit/(?P<pk>\d+)/complete/$',
        views.hod_complete_teaching_credit, name='hod-teaching-credit-complete'),

    # Supervisor (read-only)
    url(r'^supervisor/teaching-credit/$',
        views.supervisor_teaching_credit_list, name='supervisor-teaching-credit-list'),

    # Academic Office (read-only)
    url(r'^acadadmin/teaching-credit/$',
        views.academic_office_teaching_credit_list, name='academic-office-teaching-credit-list'),
]