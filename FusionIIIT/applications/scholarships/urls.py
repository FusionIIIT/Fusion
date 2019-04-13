from django.conf.urls import url

from . import views

app_name = 'spacs'

urlpatterns = [

    url(r'^$', views.spacs, name='spacs'),
    url(r'^student_view/$', views.student_view, name='student_view'),
    url(r'^convener_view/$', views.convener_view, name='convener_view'),
    url(r'^staff_view/$', views.staff_view, name='staff_view'),
    url(r'^stats/$', views.stats, name='stats'),
    url(r'^convener_catalogue/$', views.convener_catalogue, name='convener_catalogue'),
    url(r'^get_winners/$', views.get_winners, name='get_winners'),
    url(r'^get_win/$', views.get_win, name='get_win'),
    url(r'^get_mcm_flag/$', views.get_mcm_flag, name='get_mcm_flag'),
    url(r'^get_convocation_flag/$', views.get_convocation_flag, name='get_convocation_flag'),
    url(r'^get_content/$', views.get_content, name='get_content'),
    url(r'^update_enddate/$', views.update_enddate, name='update_enddate'),

]
