from django.conf.urls import url
from django.urls import path, include
from . import views
from django.contrib import admin
from applications.programme_curriculum.api import views as v2
app_name = 'programme_curriculum'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.programme_curriculum, name='programme_curriculum'),

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
    path('admin_working_curriculums/', views.admin_view_all_working_curriculums, name='admin_view_all_working_curriculums'),
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
    path('view_inward_files/<ProposalId>/',views.view_inward_files,name='view_inward_files'),
    path('outward_files/',views.outward_files,name='outward_files'),
    path('tracking_archive/<ProposalId>/',views.tracking_archive,name='tracking_archive'),
    path('tracking_unarchive/<ProposalId>/',views.tracking_unarchive,name='tracking_unarchive'),
    path('file_archive/<FileId>/',views.file_archive,name='file_archive'),
    path('file_unarchive/<FileId>/',views.file_unarchive,name='file_unarchive'),
    

    # urls for api view
    path('api/programmes_ug/', v2.view_ug_programmes, name='view_ug_programmes_api'),
    path('api/programmes_pg/', v2.view_pg_programmes, name='view_pg_programmes_api'),
    path('api/programmes_phd/', v2.view_phd_programmes, name='view_phd_programmes_api'),
    path('api/programme_info/', v2.get_programme_info, name='programme_info_api'),
    path('api/curriculumns/', v2.view_curriculumns, name='curriculumns_api'),
    path('api/add_programme/', v2.create_programme, name='add_programme_api'),
]
