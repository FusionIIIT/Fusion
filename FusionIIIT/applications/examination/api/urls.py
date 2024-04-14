
from django.conf.urls import url
from django.urls import path, include
from . import views


urlpatterns = [
    url(r'^registered_student_details/', views.fetch_student_details, name='fetch_student_details'),
    
    # url(r'^add_student/', views.add_student, name='add_student'),

    url(r'^update_hidden_grade/', views.update_hidden_grade, name='update_hidden_grade'),

    url(r'^add_courses/' , views.add_courses , name = 'add_courses'),

    url(r'^update_authenticator/', views.update_authenticator, name='update_authenticator'),

    url(r'^check_all_authenticators/', views.check_all_authenticators, name='check_all_authenticators'),


    url(r'^publish_grade/' , views.publish_grade , name='publish_grade'),

    # url(r'^announcement/',views.announcement , name = 'announcement')

    url(r'^generate_transcript_form/' , views.generate_transcript_form , name = 'generate_transcript_form'),

    url(r'^generate_transcript/' , views.generate_transcript , name = 'generate_transcript'),

    url(r'^getGrades/' , views.get_grade_for_course , name='get_grade_for_course'),

    url(r'^get_course_names/' , views.get_course_names , name='get_course_names'),

    url(r'^update_grades/' , views.update_grades , name='update_grades'),

    url(r'^fetch_roll_of_courses/' , views.fetch_roll_of_courses , name='fetch_roll_of_courses/'),

    url(r'^get_registered_students_roll_no/' , views.get_registered_students_roll_no , name='get_registered_students_roll_no/'),
    

]