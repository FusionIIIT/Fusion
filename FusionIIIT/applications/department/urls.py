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
    url(r'^MtechFirstYear_Students/$', views.MtechFirstYear_Students, name='MtechFirstYear_Students'),
    url(r'^MtechSecondYear_Students/$', views.MtechSecondYear_Students, name='MtechSecondYear_Students'),
    url(r'^PhD_Students/$', views.PhD_Students, name='PhD_Students'),
    url(r'^cse_faculty/$', views.cse_faculty, name='cse_faculty'),
    url(r'^ece_faculty/$', views.ece_faculty, name='ece_faculty'),
    url(r'^me_faculty/$', views.me_faculty, name='me_faculty')
]