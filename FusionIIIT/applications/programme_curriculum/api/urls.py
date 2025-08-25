from django.conf.urls import url
from django.urls import path, include
from django.contrib import admin
from . import views 
from . import views_student_management
from .. import views_password_email


urlpatterns = [
    # path('admin/', admin.site.urls),
    # path('', views.programme_curriculum, name='programme_curriculum'),

    path('programmes/', views.view_all_programmes, name='view_all_programmes'),
    path('working_curriculums/', views.view_all_working_curriculums, name='view_all_working_curriculums'),
    path('curriculums/<programme_id>/', views.view_curriculums_of_a_programme, name='view_curriculums_of_a_programme'),
    path('curriculum_semesters/<curriculum_id>/', views.view_semesters_of_a_curriculum, name='view_semesters_of_a_curriculum'),
    path('semester/<semester_id>/', views.view_a_semester_of_a_curriculum, name='view_a_semester_of_a_curriculum'),
    path('courseslot/<courseslot_id>/', views.view_a_courseslot, name='view_a_courseslot'),
    path('courses/', views.view_all_courses, name='view_all_courses'),
    path('course/<course_id>/', views.view_a_course, name='view_a_course'),
    path('disciplines/', views.view_all_discplines, name='view_all_discplines'),
    path('batches/', views.view_all_batches, name='view_all_batches'),
    

    path('admin_programmes/', views.admin_view_all_programmes, name='admin_view_all_programmes'),
    path('admin_working_curriculums/', views.Admin_view_all_working_curriculums, name='admin_view_all_working_curriculums'),
    path('admin_curriculums/<programme_id>/', views.admin_view_curriculums_of_a_programme, name='admin_view_curriculums_of_a_programme'),
    path('admin_curriculum_semesters/<curriculum_id>/', views.admin_view_semesters_of_a_curriculum, name='admin_view_semesters_of_a_curriculum'),
    path('admin_semester/<semester_id>/', views.admin_view_a_semester_of_a_curriculum, name='admin_view_a_semester_of_a_curriculum'),
    path('admin_courseslot/<courseslot_id>/', views.admin_view_a_courseslot, name='admin_view_a_courseslot'),
    path('admin_courses/', views.admin_view_all_courses, name='admin_view_all_courses'),
    path('admin_course/<course_id>/', views.admin_view_a_course, name='admin_view_a_course'),
    path('admin_disciplines/', views.admin_view_all_discplines, name='admin_view_all_discplines'),
    path('admin_batches/', views.admin_view_all_batches, name='admin_view_all_batches'),
    
    path('admin_add_programme/', views.add_programme_form, name='add_programme_form'),
    path('admin_add_discipline/', views.add_discipline_form, name='add_discipline_form'),
    path('admin_add_curriculum/', views.add_curriculum_form, name='add_curriculum_form'),
    path('admin_add_course/', views.add_course_form, name='add_course_form'),
    path('admin_add_courseslot/', views.add_courseslot_form, name='add_courseslot_form'),
    path('admin_add_course/', views.add_course_form, name='add_course_form'),
    path('admin_add_batch/', views.add_batch_form, name='add_batch_form'),

    path('admin_update_course/<course_id>/', views.update_course_form, name='update_course_form'),
    path('admin_edit_curriculum/<curriculum_id>/', views.edit_curriculum_form, name='edit_curriculum_form'),
    path('admin_edit_programme/<programme_id>/', views.edit_programme_form, name='edit_programme_form'),
    path('admin_edit_courseslot/<courseslot_id>/', views.edit_courseslot_form, name='edit_courseslot_form'),
    path('admin_delete_courseslot/<courseslot_id>/', views.delete_courseslot, name='delete_courseslot'),
    path('admin_edit_batch/<batch_id>/', views.edit_batch_form, name='edit_batch_form'),
    path('admin_edit_discipline/<discipline_id>/', views.edit_discipline_form, name='edit_discipline_form'),
    path('admin_instigate_semester/<semester_id>/', views.instigate_semester, name='instigate_semester'),
    path('admin_replicate_curriculum/<curriculum_id>/', views.replicate_curriculum, name='replicate_curriculum'),
    
    
    
    #new
    path('view_course_proposal_forms/',views.view_course_proposal_forms,name='view_course_proposal_forms'),
    path('faculty_view_all_courses/', views.faculty_view_all_courses, name='faculty_view_all_courses'),
    path('faculty_view_a_course/<course_id>/',views.faculty_view_a_course,name="faculty_view_a_course"),
    path('reject_form/<ProposalId>/', views.reject_form, name='reject_form'),
    path('new_course_proposal_file/',views.new_course_proposal_file,name='new_course_proposal_file'),
    path('update_course_proposal_file/<course_id>/',views.update_course_proposal_file,name='update_course_proposal_file'),
    
    path('view_a_course_proposal_form/<CourseProposal_id>/',views.view_a_course_proposal_form,name='view_a_course_proposal_form'),
    path('filetracking/<proposal_id>/',views.filetracking,name='filetracking'),
    path('inward_files/',views.inward_files,name='inward_files'),
    path('forward_course_forms/<ProposalId>/',views.forward_course_forms,name='forward_course_forms'),
    path('forward_course_forms_II/',views.forward_course_forms_II,name='forward_course_forms'),
    path('view_inward_files/<ProposalId>/',views.view_inward_files,name='view_inward_files'),
    path('outward_files/',views.outward_files,name='outward_files'),
    path('tracking_archive/<ProposalId>/',views.tracking_archive,name='tracking_archive'),
    path('tracking_unarchive/<ProposalId>/',views.tracking_unarchive,name='tracking_unarchive'),
    path('file_archive/<FileId>/',views.file_archive,name='file_archive'),
    path('file_unarchive/<FileId>/',views.file_unarchive,name='file_unarchive'),
    path('get_superior_data/', views.get_superior_data, name='get_superior_data'),

    path('admin_get_course_slot_type/',views.course_slot_type_choices,name='course_slot_type_choices'),
    path('admin_get_semesterDetails/',views.semester_details,name='semester_details'),
    path('admin_get_program/<programme_id>/',views.get_programme,name='get_program'), 

    path('admin_get_batch_name/', views.get_batch_names, name='get_batch_names'),
    path('admin_get_disciplines/', views.get_all_disciplines, name='get_all_disciplines'),
    path('admin_get_unlinked_curriculam/', views.get_unused_curriculam, name='get_unused_curricula'),
    
    path('admin_instructor/',views.admin_view_all_course_instructor,name='admin_view_all_course_instructor'),
    path('admin_faculties/', views.admin_view_all_faculties, name='admin_view_all_faculties'),
    path('admin_add_course_instructor/', views.add_course_instructor, name='add_course_instructor'),
    path('admin_update_course_instructor/<instructor_id>/', views.update_course_instructor_form, name='update_course_instructor_form'),
    
    # Student Data Management APIs
    path('admin_batches_overview/', views_student_management.admin_batches_overview, name='admin_batches_overview'),
    path('process_excel_upload/', views_student_management.process_excel_upload, name='process_excel_upload'),
    path('admin_process_excel_upload/', views_student_management.process_excel_upload, name='admin_process_excel_upload'),  # Alias for frontend
    path('save_students_batch/', views_student_management.save_students_batch, name='save_students_batch'),
    path('admin_save_students_batch/', views_student_management.save_students_batch, name='admin_save_students_batch'),  # Alias for frontend
    path('admin_add_single_student/', views_student_management.add_single_student, name='admin_add_single_student'),
    path('set_total_seats/', views_student_management.set_total_seats, name='set_total_seats'),
    path('admin_set_total_seats/', views_student_management.set_total_seats, name='admin_set_total_seats'),  # Alias for frontend
    path('update_student_status/', views_student_management.update_student_status, name='update_student_status'),
    path('admin_update_student_status/', views_student_management.update_student_status, name='admin_update_student_status'),  # Alias for frontend
    path('export_students/<str:programme_type>/', views_student_management.export_students, name='export_students'),
    path('admin_export_students/<str:programme_type>/', views_student_management.export_students, name='admin_export_students'),  # Alias for frontend
    path('upload_history/', views_student_management.upload_history, name='upload_history'),
    path('admin_upload_history/', views_student_management.upload_history, name='admin_upload_history'),  # Alias for frontend
    path('list_students/', views_student_management.list_students, name='list_students'),
    path('admin_list_students/', views_student_management.list_students, name='admin_list_students'),  # Alias for frontend
    
    # Individual Student CRUD APIs
    path('student/<int:student_id>/', views_student_management.get_student, name='get_student'),
    path('student/<int:student_id>/update/', views_student_management.update_student, name='update_student'),
    path('student/<int:student_id>/delete/', views_student_management.delete_student, name='delete_student'),
    path('admin_student/<int:student_id>/', views_student_management.get_student, name='admin_get_student'),  # Alias for frontend
    path('admin_student/<int:student_id>/update/', views_student_management.update_student, name='admin_update_student'),  # Alias for frontend
    path('admin_student/<int:student_id>/delete/', views_student_management.delete_student, name='admin_delete_student'),  # Alias for frontend
    
    # Batch Management CRUD APIs
    path('batches/create/', views_student_management.create_batch, name='create_batch'),
    path('batches/<int:batch_id>/update/', views_student_management.update_batch, name='update_batch'),
    path('batches/<int:batch_id>/delete/', views_student_management.delete_batch, name='delete_batch'),
    path('batches/list/', views_student_management.list_batches_with_status, name='list_batches_with_status'),
    
    # Student Status Management
    path('students/<int:student_id>/update_status/', views_student_management.update_student_status_crud, name='update_student_status_crud'),
    
    # Password Management
    path('batches/auto_generate_passwords/', views_student_management.auto_generate_passwords_for_batch, name='auto_generate_passwords_for_batch'),
    
    # Password Email Management APIs
    path('send_student_password/', views_password_email.send_student_password, name='send_student_password'),
    path('admin_send_student_password/', views_password_email.send_student_password, name='admin_send_student_password'),  # Alias for frontend
    path('bulk_send_passwords/', views_password_email.bulk_send_passwords, name='bulk_send_passwords'),
    path('admin_bulk_send_passwords/', views_password_email.bulk_send_passwords, name='admin_bulk_send_passwords'),  # Alias for frontend
    path('password_email_status/<int:email_log_id>/', views_password_email.password_email_status, name='password_email_status'),
    path('bulk_operation_status/<str:operation_id>/', views_password_email.bulk_operation_status, name='bulk_operation_status'),
    path('manage_email_templates/', views_password_email.manage_email_templates, name='manage_email_templates'),
    
]
