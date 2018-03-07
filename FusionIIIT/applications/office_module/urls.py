from django.conf.urls import url

from . import views

app_name = 'office'

urlpatterns = [

    url(r'^officeOfDeanStudents/', views.officeOfDeanStudents, name='officeOfDeanStudents'),
    url(r'^officeOfPurchaseOfficer/', views.officeOfPurchaseOfficer, name='officeOfPurchaseOfficer'),
    url(r'^officeOfRegistrar/', views.officeOfRegistrar, name='officeOfRegistrar'),

    url(r'^genericModule/', views.genericModule, name='genericModule'),

]
