from django.urls import path
from . import views

app_name = 'lms'
urlpatterns = [
    path('', views.index, name='index'),
    path('courses/<int:pk>/', views.workspace, name='workspace'),
    path('courses/<int:pk>/edit/<str:kind>/', views.edit, name='create'),
    path('courses/<int:pk>/edit/<str:kind>/<int:item_id>/', views.edit, name='edit'),
    path('courses/<int:pk>/assignments/<int:item_id>/publish/', views.publish, name='publish'),
    path('courses/<int:pk>/assignments/<int:item_id>/submit/', views.submit, name='submit'),
    path('courses/<int:pk>/submissions/<int:item_id>/grade/', views.grade, name='grade'),
    path('courses/<int:pk>/download/<str:kind>/<int:item_id>/', views.download, name='download'),
]
