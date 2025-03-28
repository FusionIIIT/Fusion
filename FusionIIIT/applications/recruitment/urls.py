from django.conf.urls import url
from django.urls import path
from . import views

app_name = 'recruitment'
urlpatterns = [
    path('', views.home_page, name='homepage'),
    path('register/',views.register,name='register'),
    path('logout/',views.logout,name='logout'),
    path('login/',views.login,name='login'),
    path('post/',views.post,name='post'),
    path('teaching/',views.teaching,name='teaching'),
    path('non-teaching/',views.non_teaching,name='non_teaching'),
    path('teaching/apply',views.apply_teaching,name='apply_teaching'),
    path('non-teaching/apply',views.apply_non_teaching,name='apply_non_teaching'),
    path('create',views.create,name='create'),
]
