from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from acdemic_procedures import views


urlpatterns = [
	url(r'addCourse/', views.add_course, name='addCourse'),
	url(r'^dropCourse/', views.drop_course, name='dropCourse'),
    url(r'^admin/', admin.site.urls),
]