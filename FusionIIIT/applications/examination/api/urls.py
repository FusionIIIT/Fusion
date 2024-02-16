
from django.conf.urls import url
from django.urls import path, include
from . import views


urlpatterns = [
    url(r'^registered_student_details/', views.fetch_student_details, name='fetch_student_details')
]