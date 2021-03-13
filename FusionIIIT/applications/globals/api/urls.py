from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'^auth/login/', views.login, name='login-api'),
    url(r'^auth/logout/', views.logout, name='logout-api'),
    # generic profile endpoint
    url(r'^profile/(?P<username>.+)/', views.profile, name='profile-api'),
    # current user profile
    url(r'^profile/', views.profile, name='profile-api'),
  
    url(r'^dashboard/',views.dashboard,name='dashboard-api'),
    url(r'^notification/read',views.NotificationRead,name='notifications-read')
    
]
