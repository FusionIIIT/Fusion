from django.conf.urls import url

from . import views

app_name = 'gymkhana'

urlpatterns = [

    url(r'^$', views.gymkhana, name='gymkhana'),
]
