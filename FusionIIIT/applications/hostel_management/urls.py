from django.urls import path
from . import views

app_name = 'hostelmanagement'

urlpatterns = [
    path('', views.hostel_view, name="hostel_view"),
    path('upload/', views.add_hall_room, name="upload"),
    path('notice_form/', views.notice_board, name="notice_board"),
    path('edit_schedule/', views.staff_edit_schedule, name='staff_edit_schedule'),
    path('delete_schedule/', views.staff_delete_schedule, name='staff_delete_schedule'),
    path('guestroom/', views.hostel_guest_room, name="guest_room"),
    path('guestroombooking/', views.guest_room_book, name="guest_room_book"),
    path('request_booking/' , views.request_booking , name ='request_booking'),
]