
from django.conf.urls import url
from django.urls import path, include
from . import views
from django.contrib import admin
from .views import update_authentication
from .views import DownloadExcelView, updateGrades

app_name = 'examination'

urlpatterns = [
    url(r'^api/', include('applications.examination.api.urls')),
    url(r'^$', views.exam, name='exam'),
    
    
    url(r'submit/', views.submit, name='submit'),#old
    url(r'verify/', views.verify, name='verify'),#old
    url(r'publish/', views.publish, name='publish'),#old
    url(r'notReady_publish/', views.notReady_publish, name='notReady_publish'),#old
    url(r'timetable/', views.timetable, name='timetable'),#old
    # entering and updataing grade
    path('entergrades/', views.entergrades, name='entergrades'),#old
    path('update_hidden_grades_multiple/', views.Updatehidden_gradesMultipleView.as_view(),
         name='update_hidden_grades_multiple'),#old
    path('verifygrades/', views.verifygrades, name='verifygrades'),#old
    path('update_hidden_grades_multiple/', views.Updatehidden_gradesMultipleView.as_view(),
         name='update_hidden_grades_multiple'),#old
    path('submit_hidden_grades_multiple/', views.Submithidden_gradesMultipleView.as_view(),
         name='submit_hidden_grades_multiple'),#old
    path('download_excel/', DownloadExcelView.as_view(), name='download_excel'),#old

    #new
    url(r'submitGrades/', views.submitGrades, name='submitGrades'),#new
    url(r'submitEntergrades/', views.submitEntergrades, name='submitEntergrades'),#new
    path('submitEntergradesStoring/', views.submitEntergradesStoring.as_view(),#new
         name='submitEntergradesStoring'),
    #new
    url(r'updateGrades/', views.updateGrades, name='updateGrades'),#new
    path('updateEntergrades/', views.updateEntergrades, name='updateEntergrades'),#new
     path('moderate_student_grades/', views.moderate_student_grades.as_view(),#new
         name='moderate_student_grades'),
    # authenticate new
    path('authenticate/', views.authenticate, name='authenticate'), #new
    path('authenticategrades/', views.authenticategrades,
         name='authenticategrades'),#new
    path('update_authentication/', update_authentication.as_view(),
         name='update_authentication'),#new
    # generate transcript new
    path('generate_transcript/', views.generate_transcript,
         name='generate_transcript'), #new
    path('generate_transcript_form/', views.generate_transcript_form,
         name='generate_transcript_form'),#new
    # Announcement
    url(r'announcement/', views.announcement, name='announcement'),#new
    

]
