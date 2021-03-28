from django.conf.urls import url

from . import views

app_name = 'dep'

urlpatterns = [

    url(r'^$', views.hod, name='dep'),
    url(r'^file_request/$', views.file_request, name='file_request'),
    url(r'^BtechFirstYear_Students/$', views.BtechFirstYear_Students, name='BtechFirstYear_Students'),
    url(r'^BtechSecondYear_Students/$', views.BtechSecondYear_Students, name='BtechSecondYear_Students'),
    url(r'^BtechThirdYear_Students/$', views.BtechThirdYear_Students, name='BtechThirdYear_Students'),
    url(r'^BtechFinalYear_Students/$', views.BtechFinalYear_Students, name='BtechFinalYear_Students'),

    url(r'^BtechFirstYear_Students_Announcements/$', views.BtechFirstYear_Students_Announcements, name='BtechFirstYear_Students_Announcements'),
    url(r'^BtechSecondYear_Students_Announcements/$', views.BtechSecondYear_Students_Announcements, name='BtechSecondYear_Students_Announcements'),
    url(r'^BtechThirdYear_Students_Announcements/$', views.BtechThirdYear_Students_Announcements, name='BtechThirdYear_Students_Announcements'),
    url(r'^BtechFinalYear_Students_Announcements/$', views.BtechFinalYear_Students_Announcements, name='BtechFinalYear_Students_Announcements'),
    
    url(r'^cse_faculty/$', views.cse_faculty, name='cse_faculty'),
    url(r'^ece_faculty/$', views.ece_faculty, name='ece_faculty'),
    url(r'^me_faculty/$', views.me_faculty, name='me_faculty')
]