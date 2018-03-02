from django.conf.urls import url

from . import views

app_name = 'office'

urlpatterns = [

    url(r'^officeOfDeanStudents/', views.officeOfDeanStudents, name='officeOfDeanStudents'),

]
