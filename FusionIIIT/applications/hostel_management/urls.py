from django.urls import path
from . import views

app_name = 'hostelmanagement'

urlpatterns = [
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

    # !! My Change
    path('allotted_rooms/<str:hall_id>/', views.alloted_rooms, name="alloted_rooms"),
    path('all_staff/<int:hall_id>/', views.all_staff, name='all_staff'),
    path('staff/<str:staff_id>/', views.StaffScheduleView.as_view(), name='staff_schedule'),
    
    # !!? Inventory
    path('inventory/', views.HostelInventoryView.as_view(), name='hostel_inventory_list'),
    path('inventory/<int:inventory_id>/modify/', views.HostelInventoryUpdateView.as_view(), name='hostel_inventory_update'),
    path('inventory/<int:inventory_id>/delete/', views.HostelInventoryView.as_view(), name='hostel_inventory_detail'),
    path('inventory/<int:hall_id>/', views.HostelInventoryView.as_view(), name='hostel_inventory_by_hall'),
    path('inventory/form/', views.get_inventory_form, name='get_inventory_form'),
    path('inventory/edit_inventory/<int:inventory_id>/', views.edit_inventory, name='edit_inventory'),


    # !!todo: Add Fine Functionality
    path('fine/', views.impose_fine_view, name='fine_form_show'),
    path('fine/impose/', views.HostelFineView.as_view(), name='fine_form_show'),
    path('fine/impose/list/', views.hostel_fine_list, name='fine_list_show'),
    path('fine/impose/list/update/<int:fine_id>/', views.HostelFineUpdateView.as_view(), name='fine_update'),
    path('fine/delete/<int:fine_id>/', views.HostelFineUpdateView.as_view(), name='fine_delete'),
    path('fine/show/', views.student_fine_details, name='fine_show'),
    
    
    
    path('student/<str:username>/name/', views.get_student_name, name='find_name'),

     
]