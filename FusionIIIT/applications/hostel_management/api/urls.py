from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'students', views.get_student, name="students"),
    url(r'halls', views.get_hall, name="halls"),
    url(r'notices', views.get_notice, name="notices"),
]
