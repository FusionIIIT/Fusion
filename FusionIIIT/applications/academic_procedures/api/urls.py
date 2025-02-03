from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^stu/details', views.academic_procedures_student, name='student_procedures'),
    url(r'^stu/pre_registration' , views.student_pre_registration , name = 'pre_registration'),
    url(r'^stu/final_registration' , views.final_registration , name = 'final_registration'),
    url(r'^stu/add_one_course/' , views.add_one_course , name = 'add_one_course'),
    url(r'^stu/view_registration' , views.student_view_registration , name = 'view_registration'),
    url(r'^stu/view_offered_courses' , views.view_offered_courses , name = 'student_view_offered_courses'),
    url(r'^stu/backlog_courses', views.student_backlog_courses , name = 'student_backlog_courses'),
    url(r'^stu/add_course' , views.add_course , name ='add_course') ,
    url(r'^stu/drop_course' , views.drop_course , name = 'drop_course'),
    # url(r'^stu/replaceCourse' , views.replaceCourse , name = 'replaceCourse')



    url(r'^acad/view_registrations' , views.acad_view_reigstrations , name='acad_view_registrations'),
    url(r'^acad/verify_registration' , views.verify_registration , name='verify_registration'),
    url(r'^acad/verify_course' , views.verify_course , name='verify_course'),
    url(r'^acad/get_course_list' , views.get_course_list , name = 'get_course_list' ),
    url(r'^acad/get_all_courses' , views.get_all_courses , name = 'get_all_courses' ),
    url(r'^acad/gen_roll_list' , views.gen_roll_list , name = 'gen_roll_list' ),
    url(r'^acad/configure_pre_registration' , views.configure_pre_registration_date , name = 'configure_pre_registration'),
    url(r'^acad/configure_final_registration' , views.configure_final_registration_date , name = 'configure_final_registration'),
    url(r'^acad/add_course_to_slot' , views.add_course_to_slot , name = 'add_course_to_slot'),
    url(r'^acad/remove_course_from_slot' , views.remove_course_from_slot , name = 'remove_course_from_slot'),
    url(r'^get_next_sem_courses' , views.get_next_sem_courses , name= 'get_next_sem_courses'),


    url(r'^fac/view_assigned_courses' , views.faculty_assigned_courses , name = 'faculty_assigned_courses'),
    # url(r'^fac/get_roll_list' , views.fetch_roll_list , name = 'fetch_roll_list'),



    url(r'^get_user_info' , views.get_user_info , name  = 'get_user_info'),

    #  these urls were designed previously and are not working any more

    # url(r'^fac/', views.academic_procedures_faculty, name='faculty_procedures'),
    # url(r'^stu', views.academic_procedures_student, name='student_procedures'),
    # url(r'^addThesis/', views.add_thesis, name='add_thesis'),
    # url(r'^approve_thesis/(?P<id>[0-9]+)/', views.approve_thesis, name='approve_thesis')

]