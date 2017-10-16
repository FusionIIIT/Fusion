from django.conf.urls import url, include
from . import views


app_name = 'eis'

urlpatterns = [

    url(r'^profile/', views.profile, name='profile'),

]