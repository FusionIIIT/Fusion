from django.conf.urls import url
from . import views

app_name = 'gymkhana'

urlpatterns = [

    url(r'^$', views.gymkhana, name='gymkhana'),
    url(r'^new_club/$', views.new_club, name='new_club'),
    url(r'^club_membership/$', views.club_membership, name='membership'),
    url(r'^core_team/$', views.core_team, name='core_team'),
    url(r'^event_report/$', views.event_report, name='event_report'),
    url(r'^club_budget/$', views.club_budget, name='club_budget'),
    url(r'^act_calender/$', views.act_calender, name='act_calender'),
    url(r'^club_event_report/$', views.club_report, name='club_report'),
    url(r'^changehead/$', views.change_head, name='change_head'),
    url(r'^new_session/$', views.new_session, name='new_session'),
    url(r'^festbudget/$', views.fest_budget, name='fest_budget'),
    url(r'^approve/$', views.approve, name='approve'),
    url(r'^reject/$', views.reject, name='reject'),
    url(r'^club_approve/$', views.club_approve, name='club_approve'),
    url(r'^club_reject/$', views.club_reject, name='club_reject'),
    url(r'^cancel/$', views.cancel, name='cancel'),
    url(r'^date_sessions/$', views.date_sessions, name='date_sessions'),
    url(r'^get_venue/$', views.getVenue, name='get_venue'),
    url(r'^faculty_data/$', views.facultyData, name='faculty_data'),
    url(r'^students_data/$', views.studentsData, name='students_data'),
    url(r'^delete_sessions/$', views.delete_sessions, name='delete_sessions'),
    url(r'^delete_memberform/$', views.delete_memberform, name='delete_memberform'),
]
