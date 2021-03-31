from django.conf.urls import url

from . import views
appname = 'procedures'
urlpatterns = [
    # url(r'^$', views.academic_procedures_redirect, name='redirect'),
    # url(r'^main/', views.academic_procedures, name='procedures'),
    # url(r'^register/', views.register, name='register'),
    url(r'^main/', views.main_page, name='main_page'),
]
