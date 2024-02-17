from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.urls import include
from django.contrib import admin
from django.conf.urls import url, include

app_name = 'hostelmanagement'

urlpatterns = [

    path('admin/', admin.site.urls),
    #Home 
    path('', views.hostel_view, name="hostel_view"),

    #Notice Board
    path('notice_form/', views.notice_board, name="notice_board"),
    path('delete_notice/', views.delete_notice, name="delete_notice"),

    #Worker Schedule
    path('edit_schedule/', views.staff_edit_schedule, name='staff_edit_schedule'),
    path('delete_schedule/', views.staff_delete_schedule, name='staff_delete_schedule'),
    
    #Student Room
    path('edit_student/',views.edit_student_room,name="edit_student_room"),
    path('edit_student_rooms_sheet/', views.edit_student_rooms_sheet, name="edit_student_rooms_sheet"),

    #Attendance
    path('edit_attendance/', views.edit_attendance, name='edit_attendance'),

    #Attendance
    path('edit_attendance/', views.edit_attendance, name='edit_attendance'),

    #Worker Report
    path('worker_report/', views.generate_worker_report, name='workerreport'),
    path('pdf/', views.GeneratePDF.as_view(), name="pdf"),

    path('assign-batch/', views.AssignBatchView.as_view(),name='AssignBatchView'),
    path('hall-ids/', views.HallIdView.as_view(), name='hall'),
    path('assign-caretaker', views.AssignCaretakerView.as_view(), name='AssignCaretakerView'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('logout/', views.logout_view, name='logout_view'),
    # path('logout/', auth_views.LogoutView.as_view(), name='logout'),
  
    # !! My Change
    path('alloted_rooms/<str:hall_id>/', views.alloted_rooms, name="alloted_rooms"),
    path('all_staff/', views.all_staff, name='all_staff')

]