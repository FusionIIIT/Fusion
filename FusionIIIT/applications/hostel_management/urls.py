from django.urls import path
from . import views

app_name = 'hostelmanagement'

urlpatterns = [
    path('', views.hostel_view, name="hostel_view"),
    path('upload/', views.add_hall_room, name="upload"),
    path('notice_form/', views.notice_board, name="notice_board")
]