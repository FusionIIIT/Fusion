from django.conf.urls import url

from . import views

app_name = 'counselling_cell'

urlpatterns = [
    url(r'',views.counselling_cell,name="counselling")
]
