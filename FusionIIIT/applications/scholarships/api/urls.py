from django.conf.urls import include, url
from . import views

urlpatterns = [

    url(r'previous-winner/', views.get_previous_winner, name='previous-winner-detail'),
    url(r'awards/', views.browse_award_info, name='browse_award_info'),
    url(r'mcmform/', views.create_mcm, name='create-mcm'),
    url(r'^invitations',views.invitations,name='invitations'),
    url(r'apply_notional_prize/', views.apply_notional_prize, name='apply_notional_prize'),
    url(r'director-gold-detail/(?P<id>[0-9]+)', views.director_gold_detail, name='director-gold-detail'),
    url(r'director-silver-detail/(?P<id>[0-9]+)', views.director_silver_detail, name='director-silver-detail'),
    url(r'dm-proficiency-gold-detail/(?P<id>[0-9]+)', views.dm_proficiency_gold_detail, name='dm-proficiency-gold-detail'),



    url(r'apply_director_gold/', views.apply_director_gold, name='apply_director_gold'),
    url(r'apply_director_silver/', views.apply_director_silver, name='apply_director_silver'),
    url(r'apply_dm_proficiency_gold/', views.apply_dm_proficiency_gold, name='apply_dm_proficiency_gold'),


    url(r'applications/', views.applications, name='applications'),
    url(r'applications_details/(?P<id>[0-9]+)', views.application_detail, name='application_detail'),
       
    url(r'mcm_detail/(?P<id>[0-9]+)', views.mcm_detail, name='mcm-detail'),
    url(r'allmcms/', views.allmcms, name='allmcms'),
    url(r'update_award_info/(?P<id>[0-9]+)', views.update_award_info, name='update-award-info'),

    url(r'invitaion_form/',views.create_invitation,name='create-invitations'),
    url(r'invitaion_update/(?P<id>[0-9]+)',views.update_invitation,name='update-invitations')
]
