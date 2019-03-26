from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = [
    # url used to add data
    url(r'uploadcsv/$', views.upload_file),
    url(r'^profile/$', views.profile, name='profile'),

    url(r'^rspc_profile/$', views.rspc_profile, name='rspc_profile'),

    #delete
    url(r'^achv/(?P<pk>[0-9]+)/$', views.achievementDelete, name='achievement_delete'),
    url(r'^emp_confrence_organisedDelete/(?P<pk>[0-9]+)/$', views.emp_confrence_organisedDelete, name='emp_confrence_organisedDelete'),
    url(r'^emp_consultancy_projectsDelete/(?P<pk>[0-9]+)/$', views.emp_consultancy_projectsDelete, name='emp_consultancy_projectsDelete'),
    url(r'^emp_event_organizedDelete/(?P<pk>[0-9]+)/$', views.emp_event_organizedDelete, name='emp_event_organizedDelete'),
    url(r'^emp_expert_lecturesDelete/(?P<pk>[0-9]+)/$', views.emp_expert_lecturesDelete, name='emp_expert_lecturesDelete'),
    url(r'^emp_keynote_addressDelete/(?P<pk>[0-9]+)/$', views.emp_keynote_addressDelete, name='emp_keynote_addressDelete'),
    url(r'^emp_mtechphd_thesisDelete/(?P<pk>[0-9]+)/$', views.emp_mtechphd_thesisDelete, name='emp_mtechphd_thesisDelete'),
    url(r'^emp_patentsDelete/(?P<pk>[0-9]+)/$', views.emp_patentsDelete, name='emp_patentsDelete'),
    url(r'^emp_published_booksDelete/(?P<pk>[0-9]+)/$', views.emp_published_booksDelete, name='emp_published_booksDelete'),
    url(r'^emp_research_papersDelete/(?P<pk>[0-9]+)/$', views.emp_research_papersDelete, name='emp_research_papersDelete'),
    url(r'^emp_research_projectsDelete/(?P<pk>[0-9]+)/$', views.emp_research_projectsDelete, name='emp_research_projectsDelete'),
    url(r'^emp_session_chairDelete/(?P<pk>[0-9]+)/$', views.emp_session_chairDelete, name='emp_session_chairDelete'),
    url(r'^emp_techtransferDelete/(?P<pk>[0-9]+)/$', views.emp_techtransferDelete, name='emp_techtransferDelete'),
    url(r'^emp_visitsDelete/(?P<pk>[0-9]+)/$', views.emp_visitsDelete, name='emp_visitsDelete'),

    # edit personal information
    url(r'^persinfo/$', views.persinfo, name='persinfo'),

    # insert
    url(r'^pg/$', views.pg_insert, name='pg_insert'),
    url(r'^phd/$', views.phd_insert, name='phd_insert'),
    url(r'^fvisit/$', views.fvisit_insert, name='fvisit_insert'),
    url(r'^ivisit/$', views.ivisit_insert, name='ivisit_insert'),
    url(r'^journal/$', views.journal_insert, name='journal_insert'),
    url(r'^confrence/$', views.confrence_insert, name='confrence_insert'),
    url(r'^book/$', views.book_insert, name='book_insert'),
    url(r'^consym/$', views.consym_insert, name='consym_insert'),
    url(r'^event/$', views.event_insert, name='event_insert'),
    url(r'^award/$', views.award_insert, name='award_insert'),
    url(r'^talk/$', views.talk_insert, name='talk_insert'),
    url(r'^chaired/$', views.chaired_insert, name='chaired_insert'),
    url(r'^keynote/$', views.keynote_insert, name='keynote_insert'),
    url(r'^project/$', views.project_insert, name='project_insert'),
    url(r'^consult_insert/$', views.consult_insert, name='consult_insert'),
    url(r'^patent_insert/$', views.patent_insert, name='patent_insert'),
    url(r'^transfer_insert/$', views.transfer_insert, name='transfer_insert'),

    # generate report
    url(r'^report/$', views.generate_report, name='generate_report'),
    url(r'^rspc_report/$', views.rspc_generate_report, name='rspc_generate_report'),

]
