from django.conf.urls import url
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from applications.scholarships.api.views import GetWinnersView
from applications.scholarships.api.views import create_award
from applications.scholarships.api.views import DirectorGoldUpdateView,DirectorSilverUpdateView,ProficiencyDMUpdateView,McmUpdateView

app_name = 'spacs'

urlpatterns = [

    url(r'^$', views.spacs, name='spacs'),
    url(r'^student_view/$', views.student_view, name='student_view'),
    url(r'^convener_view/$', views.convener_view, name='convener_view'),
    url(r'^staff_view/$', views.staff_view, name='staff_view'),
    url(r'^stats/$', views.stats, name='stats'),
    url(r'^convenerCatalogue/$', views.convenerCatalogue, name='convenerCatalogue'),
    url(r'^getWinners/$', views.getWinners, name='getWinners'),
    url(r'^get_MCM_Flag/$', views.get_MCM_Flag, name='get_MCM_Flag'),
    url(r'^getConvocationFlag/$', views.getConvocationFlag, name='getConvocationFlag'),
    url(r'^getContent/$', views.getContent, name='getContent'),
    url(r'^updateEndDate/$', views.updateEndDate, name='updateEndDate'),
    #app
    url(r'get-winners/', GetWinnersView.as_view(), name='get-winners'),
    url(r'create-award/', create_award.as_view(), name='create-award'),
    url(r'director-gold/', DirectorGoldUpdateView.as_view(), name='director-gold-update'),
    path('director-silver/', DirectorSilverUpdateView.as_view(), name='director-silver-update'),
    path('proficiency-dm/', ProficiencyDMUpdateView.as_view(), name='proficiency-dm-update'),
    path('mcm/', McmUpdateView.as_view(), name='mcm-update'),


]