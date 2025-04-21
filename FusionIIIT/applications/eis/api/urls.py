from django.conf.urls import url, re_path

from . import views

urlpatterns = [
    # url used to add data
    # url(r'uploadcsv/$', views.upload_file),
    re_path(r'^$', views.index, name='index'),
    # url(r'^profile/(?P<username>\w+)/$', views.profile, name='profile'),
    re_path(r'^profile/$', views.profile, name='profile'),

    re_path(r'^rspc_profile/$', views.rspc_profile, name='rspc_profile'),

    # delete
    re_path(r'^achv/$', views.achievementDelete, name='achievement_delete'),
    re_path(r'^emp_confrence_organisedDelete/$', views.emp_confrence_organisedDelete, name='emp_confrence_organisedDelete'),
    re_path(r'^emp_consultancy_projectsDelete/$', views.emp_consultancy_projectsDelete, name='emp_consultancy_projectsDelete'),

    re_path(r'^emp_confrence_organisedDelete/$', views.emp_confrence_organisedDelete, name='emp_confrence_organisedDelete'),
    re_path(r'^emp_event_organizedDelete/$', views.emp_event_organizedDelete, name='emp_event_organizedDelete'),
    re_path(r'^emp_expert_lecturesDelete/$', views.emp_expert_lecturesDelete, name='emp_expert_lecturesDelete'),
    re_path(r'^emp_keynote_addressDelete/$', views.emp_keynote_addressDelete, name='emp_keynote_addressDelete'),
    re_path(r'^emp_mtechphd_thesisDelete/$', views.emp_mtechphd_thesisDelete, name='emp_mtechphd_thesisDelete'),
    re_path(r'^emp_patentsDelete/$', views.emp_patentsDelete, name='emp_patentsDelete'),
    re_path(r'^emp_published_booksDelete/$', views.emp_published_booksDelete, name='emp_published_booksDelete'),
    re_path(r'^emp_research_papersDelete/$', views.emp_research_papersDelete, name='emp_research_papersDelete'),
    re_path(r'^emp_research_projectsDelete/$', views.emp_research_projectsDelete, name='emp_research_projectsDelete'),
    re_path(r'^emp_session_chairDelete/$', views.emp_session_chairDelete, name='emp_session_chairDelete'),

    re_path(r'^emp_techtransferDelete/$', views.emp_techtransferDelete, name='emp_techtransferDelete'),
    re_path(r'^emp_visitsDelete/$', views.emp_visitsDelete, name='emp_visitsDelete'),
    re_path(r'^emp_consymDelete/$', views.emp_consymDelete, name='emp_consymDelete'),


    # edit personal information
    re_path(r'^extra/$', views.view_all_extra_infos, name='extra'),
    re_path(r'^persinfo/$', views.persinfo, name='persinfo'),
    re_path(r'^journal/edit$', views.editjournal, name='editjournal'),
    re_path(r'^foreignvisit/edit$', views.editforeignvisit, name='editforeignvisit'),
    re_path(r'^indianvisit/edit$', views.editindianvisit, name='editindianvisit'),
    re_path(r'^consym/edit$', views.editconsym, name='editconsym'),
    re_path(r'^event/edit$', views.editevent, name='editevent'),
    re_path(r'^conference/edit$', views.editconference, name='editconference'),
    re_path(r'^books/edit$', views.editbooks, name='editbooks'),

    re_path(r'^update_personal_info/$', views.update_personal_info, name='update_personal_info'),

    # insert
    re_path(r'^pg/$', views.pg_insert, name='pg_insert'),
    re_path(r'^phd/$', views.phd_insert, name='phd_insert'),
    re_path(r'^fvisit/$', views.fvisit_insert, name='fvisit_insert'),
    re_path(r'^ivisit/$', views.ivisit_insert, name='ivisit_insert'),
    re_path(r'^journal/$', views.journal_insert, name='journal_insert'),
    re_path(r'^conference/$', views.conference_insert, name='conference_insert'),
    re_path(r'^book/$', views.book_insert, name='book_insert'),
    re_path(r'^consym/$', views.consym_insert, name='consym_insert'),
    re_path(r'^event/$', views.event_insert, name='event_insert'),
    re_path(r'^award/$', views.award_insert, name='award_insert'),
    re_path(r'^talk/$', views.talk_insert, name='talk_insert'),
    re_path(r'^chaired/$', views.chaired_insert, name='chaired_insert'),
    re_path(r'^keynote/$', views.keynote_insert, name='keynote_insert'),
    re_path(r'^project/$', views.project_insert, name='project_insert'),
    re_path(r'^consult_insert/$', views.consult_insert, name='consult_insert'),
    re_path(r'^patent_insert/$', views.patent_insert, name='patent_insert'),
    re_path(r'^transfer_insert/$', views.transfer_insert, name='transfer_insert'),

    # generate report
    url(r'^report/$', views.generate_report, name='generate_report'),


    # Fetch Details from Database
    re_path(r'^get_personal_info/$', views.get_personal_info, name='get_personal_info'),
    re_path(r'^projects/pf_no/$', views.get_research_projects, name='projects_by_pf_no'),
    re_path(r'^projects/all/$', views.get_all_research_projects, name='projects_all'),
    re_path(r'^consultancy_projects/pf_no/$', views.get_consultancy_projects, name='consultancy_projects_by_pf_no'),
    re_path(r'^patents/pf_no/$', views.get_patents, name='patents_by_pf_no'),
    re_path(r'^pg_thesis/pf_no/$', views.get_pg_thesis, name='pg_thesis_by_pf_no'),
    re_path(r'^phd_thesis/pf_no/$', views.get_phd_thesis, name='phd_thesis_by_pf_no'),
    re_path(r'^event/pf_no/$', views.get_event, name='event_by_pf_no'),
    re_path(r'^fvisits/pf_no/$', views.get_fvisits, name='fvisits_by_pf_no'),
    re_path(r'^ivisits/pf_no/$', views.get_ivisits, name='ivisits_by_pf_no'),
    re_path(r'^consym/pf_no/$', views.get_consym, name='consym_by_pf_no'),
    re_path(r'^fetch_book/$', views.get_books, name="get_books_of_prof"),
    re_path(r'^fetch_journal/$', views.get_journals, name="get_journals_of_prof"),
    re_path(r'^fetch_conference/$', views.get_conference, name="get_conference_of_prof"),
    re_path(r'^award/pf_no/$', views.get_achievements, name="get_achievements_of_prof"),
    re_path(r'^talk/pf_no/$', views.get_talks, name="get_talks_of_prof"),

    # Filter and Fetch
    re_path(r'^projects/filter/$', views.filter_research_projects, name='projects_by_filter'),
    re_path(r'^consultancy_projects/filter/$', views.filter_consultancy_projects, name='consultancy_projects_by_filter'),
    re_path(r'^patents/filter/$', views.filter_patents, name='patents_by_filter'),
    re_path(r'^pg_phd_thesis/filter/$', views.filter_mtechphd_thesis, name='pg_thesis_by_filter'),
    re_path(r'^event/filter/$', views.filter_events, name='event_by_filter'),
    re_path(r'^visits/filter/$', views.filter_visits, name='visits_by_filter'),
    re_path(r'^consym/filter/$', views.filter_consym, name='consym_by_filter'),
    re_path(r'^fetch_book/filter/$', views.filter_books, name="get_books_of_prof_filter"),
    re_path(r'^fetch_journal_or_conference/filter/$', views.filter_journal_or_conference, name="get_journals_or_conference_of_prof_filter"),
    re_path(r'^award/filter/$', views.filter_achievements, name="get_achievements_of_prof_filter"),
    re_path(r'^talk/filter/$', views.filter_talks, name="get_talks_of_prof_filter"),

    # special

    re_path(r'^get_id/$', views.get_all_faculty_ids, name='get_all_faculty_ids'),

    # 4 forms

    re_path(r'^add_administrative_position/$', views.add_administrative_position, name='add_administrative_position'),
    re_path(r'^get_administrative_positions/$', views.get_administrative_position, name='get_administrative_positions'),
    re_path(r'^delete_administrative_position/$', views.delete_administrative_position, name='delete_administrative_position'),

    re_path(r'^add_qualification/$', views.add_qualification, name='add_qualification'),
    re_path(r'^get_qualifications/$', views.get_qualifications, name='get_qualifications'),
    re_path(r'^delete_qualification/$', views.delete_qualification, name='delete_qualification'),

    re_path(r'^add_honor/$', views.add_honor, name='add_honor'),
    re_path(r'^get_honors/$', views.get_honors, name='get_honors'),
    re_path(r'^delete_honor/$', views.delete_honor, name='delete_honor'),

    re_path(r'^add_professional_experience/$', views.add_professional_experience, name='add_professional_experience'),
    re_path(r'^get_professional_experiences/$', views.get_professional_experiences, name='get_professional_experiences'),
    re_path(r'^delete_professional_experience/$', views.delete_professional_experience, name='delete_professional_experience'),

    # csrf
    re_path(r'^csrf/$', views.get_csrf_token, name='csrf'), 
]