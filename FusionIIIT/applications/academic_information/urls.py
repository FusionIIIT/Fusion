from django.conf.urls import url

from . import views

app_name = 'academic_information'

urlpatterns = [
    url(r'^$', views.homepage, name='homepage'),
    url(r'^senator/$', views.senator, name='senator'),
    url(r'^deleteSenator/$', views.deleteSenator, name='deleteSenator'),
    url(r'^add_convenor/$', views.add_convenor, name='add_convenor'),
    url(r'^delete1/$', views.delete1, name='delete1'),
    url(r'^delete2/$', views.delete2, name='delete2'),
    url(r'^deleteMinute/$', views.deleteMinute, name='deleteMinute'),
    url(r'^attendance', views.add_attendance, name="add_attendance"),
    url(r'^get_attendance', views.get_attendance, name="get_attendance"),
    url(r'^add_basic_profile/$', views.add_basic_profile, name='add_basic_profile'),
    url(r'^add_advanced_profile', views.add_advanced_profile, name='add_advanced_profile'),
    url(r'^add_grade', views.add_grade, name='add_grade'),
    url(r'^add_course', views.add_course, name='add_course'),
    url(r'^delete_advanced_profile', views.delete_advanced_profile, name="delete_advanced_profile"),
    url(r'^delete_basic_profile', views.delete_basic_profile, name="delete_basic_profile"),
    url(r'^delete_grade', views.delete_grade, name="delete_grade"),
    url(r'^add_exam_timetable', views.add_exam_timetable, name="add_exam_timetable"),
    url(r'^add_timetable', views.add_timetable, name="add_timetable"),
    url(r'^delete_timetable', views.delete_timetable, name='delete_timetable'),
]
