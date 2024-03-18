
from django.conf.urls import url
from django.urls import path, include
from . import views
from django.contrib import admin
from .views import update_authentication
from .views import DownloadExcelView

app_name = 'examination'

urlpatterns = [
    url(r'^api/', include('applications.examination.api.urls')),
    url(r'^$', views.exam, name='exam'),
    url(r'submit/', views.submit, name='submit'),
    url(r'verify/', views.verify, name='verify'),
    url(r'publish/', views.publish, name='publish'),
    url(r'notReady_publish/', views.notReady_publish, name='notReady_publish'),
    url(r'announcement/', views.announcement, name='announcement'),
    url(r'timetable/', views.timetable, name='timetable'),
    
    #entering and updataing grade
    path('entergrades/', views.entergrades, name='entergrades'),
    path('update_hidden_grades_multiple/', views.Updatehidden_gradesMultipleView.as_view(),
         name='update_hidden_grades_multiple'),
    path('verifygrades/', views.verifygrades, name='verifygrades'),
    path('update_hidden_grades_multiple/', views.Updatehidden_gradesMultipleView.as_view(),
         name='update_hidden_grades_multiple'),
    path('submit_hidden_grades_multiple/', views.Submithidden_gradesMultipleView.as_view(),
         name='submit_hidden_grades_multiple'),

    # authenticate
    path('authenticate/', views.authenticate, name='authenticate'),
    path('authenticategrades/', views.authenticategrades,
         name='authenticategrades'),
    path('update_authentication/', update_authentication.as_view(),
         name='update_authentication'),
    
    #download result
     path('download_excel/', DownloadExcelView.as_view(), name='download_excel'),
     
    # generate transcript
    path('generate_transcript/', views.generate_transcript, name='generate_transcript'),
    path('generate_transcript_form/', views.generate_transcript_form, name='generate_transcript_form'),
    # url(r'entergrades/', views.entergrades, name='entergrades'),

]
