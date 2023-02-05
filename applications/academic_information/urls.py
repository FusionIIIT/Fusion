
from django.conf.urls import url, include

from . import views

app_name = 'academic_information'

urlpatterns = [
    url(r'^$', views.homepage, name='homepage'),
    url(r'^generateSheet$',views.generatexlsheet, name = 'generatexlsheet'),
    url(r'^senator/$', views.senator, name='senator'),
    url(r'^deleteSenator/(?P<pk>[0-9]+)$', views.deleteSenator, name='deleteSenator'),
    url(r'^add_convenor/$', views.add_convenor, name='add_convenor'),
    url(r'^deleteConvenor/(?P<pk>[0-9]+)$', views.deleteConvenor, name='deleteConvenor'),
    url(r'^addMinute/$', views.addMinute, name="addMinute"),
    url(r'^deleteMinute/$', views.deleteMinute, name='deleteMinute'),
    url(r'^add_basic_profile/$', views.add_basic_profile, name='add_basic_profile'),
    url(r'^add_advanced_profile', views.add_advanced_profile, name='add_advanced_profile'),
    url(r'^add_new_profile', views.add_new_profile, name='add_new_profile'),
    url(r'^verify_grade', views.verify_grade, name='verify_grade'),
    url(r'^view_course', views.view_course, name='view_course'),
    url(r'^confirm_grades', views.confirm_grades, name='confirm_grades'),
    url(r'^delete_advanced_profile', views.delete_advanced_profile, name="delete_advanced_profile"),
    url(r'^delete_basic_profile/(?P<pk>[0-9]+)$', views.delete_basic_profile,
        name="delete_basic_profile"),
    url(r'^delete_grade', views.delete_grade, name="delete_grade"),
    url(r'^add_exam_timetable', views.add_exam_timetable, name="add_exam_timetable"),
    url(r'^delete_exam_timetable', views.delete_exam_timetable, name='delete_exam_timetable'),
    url(r'^add_timetable', views.add_timetable, name="add_timetable"),
    url(r'^delete_timetable', views.delete_timetable, name='delete_timetable'),
    url(r'^add_calendar', views.add_calendar, name='Add Calendar'),
    url(r'^update_calendar', views.update_calendar, name='Add Calendar'),
    url(r'^select_opt', views.add_optional, name="Add Optional"),
    url(r'^set_min_cred', views.min_cred, name="Minimum Credit"),
    url(r'^generate_preregistration_report',views.generate_preregistration_report, name = "generate_preregistration_report"),
    url(r'^view_curriculum', views.curriculum, name="view_curriculum"),
    url(r'^add_curriculum', views.add_curriculum, name="add_curriculum"),
    url(r'^edit_curriculum', views.edit_curriculum, name="edit_curriculum"),
    url(r'^next_curriculum', views.next_curriculum, name="next_curriculum"),
    url(r'^delete_curriculum', views.delete_curriculum, name="delete_curriculum"),
    url(r'^float_course_submit', views.float_course_submit, name="float_course_submit"),
    url(r'^float_course', views.float_course, name="float_course"),
    url(r'^api/',include('applications.academic_information.api.urls')),
    url(r'^view_all_student_data', views.view_all_student_data, name='view_all_student_data'),
    url(r'^generateStudentSheet$',views.generatestudentxlsheet, name = 'generatestudentxlsheet'),
]
