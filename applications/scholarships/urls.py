from django.conf.urls import url

from . import views

app_name = 'spacs'

urlpatterns = [

    url(r'^$', views.spacs, name='spacs'),
    url(r'^student_view/$', views.student_view, name='student_view'),
    url(r'^convener_view/$', views.convener_view, name='convener_view'),
    url(r'^staff_view/$', views.staff_view, name='staff_view'),
    url(r'^convener_catalogue/$', views.convener_catalogue, name='convener_catalogue'),
    url(r'^get_winners/$', views.get_winners, name='get_winners'),
    url(r'^get_content/$', views.get_content, name='get_content'),

]
