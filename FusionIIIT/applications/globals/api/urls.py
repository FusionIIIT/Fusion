from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'^auth/login/', views.login, name='login-api'),
    url(r'^dashboard/',views.dashboard,name='dashboard-api'),
    url(r'^notification/read',views.NotificationRead,name='notifications-read')
    
]
