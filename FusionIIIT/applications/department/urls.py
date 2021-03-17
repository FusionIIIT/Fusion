from django.conf.urls import url

from . import views

app_name = 'dep'

urlpatterns = [

    url(r'^$', views.hod, name='dep'),
    url(r'^file_complaint/$', views.file_complaint, name='file_complaint'),
    url(r'^BtechFirstYear_Students/$', views.BtechFirstYear_Students, name='BtechFirstYear_Students'),
    url(r'^BtechSecondYear_Students/$', views.BtechSecondYear_Students, name='BtechSecondYear_Students'),
    url(r'^BtechThirdYear_Students/$', views.BtechThirdYear_Students, name='BtechThirdYear_Students'),
    url(r'^BtechFinalYear_Students/$', views.BtechFinalYear_Students, name='BtechFinalYear_Students'),
    url(r'^cse_faculty/$', views.cse_faculty, name='cse_faculty')
]