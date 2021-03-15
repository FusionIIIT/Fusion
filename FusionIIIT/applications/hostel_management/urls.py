from django.conf.urls import url
from . import views

app_name = 'hostelmanagement'

urlpatterns = [
    url('allotedroom', views.view_alloted_room, name="allotedroom")
]