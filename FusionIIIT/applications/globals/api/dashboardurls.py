from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'^dashboard/',views.dashboard,name='dashboard-api')
]
