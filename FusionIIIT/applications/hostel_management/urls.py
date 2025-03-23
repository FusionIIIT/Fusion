from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.urls import include
from django.contrib import admin
from django.conf.urls import url, include

app_name = "hostelmanagement"

urlpatterns = [

    path("admin/", admin.site.urls),
    # Home
    path("", views.hostel_view, name="hostel_view"),
    path("hello", views.hostel_view, name="hello"),
    # Notice Board
    path("create_notice/", views.NoticeBoardCreate.as_view(), name="create_notice"),
    path("delete_notice/", views.NoticeBoardDelete.as_view(), name="delete_notice"),
    # Worker Schedule
    path("edit_schedule/", views.staff_edit_schedule, name="staff_edit_schedule"),
    path("delete_schedule/", views.staff_delete_schedule, name="staff_delete_schedule"),
    # Student Room
    path("edit_student/", views.edit_student_room, name="edit_student_room"),
    path(
        "edit_student_rooms_sheet/",
        views.edit_student_rooms_sheet,
        name="edit_student_rooms_sheet",
    ),
    # Attendance
    path("upload_attendance/", views.UploadAttendance.as_view(), name="edit_attendance"),
    # #Hostel Attandnace
    path("view_attendance/", views.ViewAttendance.as_view(), name="view_attendance"),
    # Worker Report
    path("worker_report/", views.generate_worker_report, name="workerreport"),
    path("pdf/", views.GeneratePDF.as_view(), name="pdf"),
    # for superUser
    path("hostel_notices/", views.NoticeBoardView.as_view(), name="hostel_notices_board"),
    # //caretaker and warden can see all leaves
    path("all_leave_data/", views.AllLeaveData.as_view(), name="all_leave_data"),
    # caretaker  or wardern can approve leave
    path("update_leave_status/", views.update_leave_status, name="update_leave_status"),
    # //apply for leave
    path("create_hostel_leave/", views.CreateHostelLeave.as_view(), name="create_hostel_leave"),
    # caretaker and warden can get all complaints
    path(
        "hostel_complaints/", views.hostel_complaint_list, name="hostel_complaint_list"
    ),
    path("register_complaint/", views.PostComplaint.as_view(), name="PostComplaint"),
    #  Student can view his leave status
    path("my_leaves/", views.my_leaves.as_view(), name="my_leaves"),
    # path("hostel_complaints/", views.HostelComplaintListView.as_view(), name="HostelComplaintList"),
    path("students_get_students_info/", views.students_get_students_info.as_view(), name="students_get_students_info"),
    path("caretaker_get_students_info/", views.caretaker_get_students_info.as_view(), name="caretaker_get_students_info"),
    path("assign-batch/", views.AssignBatchView.as_view(), name="AssignBatchView"),
    path("batch-assign/", views.AssignBatch.as_view(), name="AssignBatch"),
    path("Assign-RoomsbyWarden/", views.AssignRoomsbyWarden.as_view(), name="AssignRoomsbyWarden"),
    path("hall-ids/", views.HallIdView.as_view(), name="hall"),

    # Admin - Assign Caretaker
    path(
        "assign_caretakers/",
        views.AssignCaretakerView.as_view(),
        name="AssignCaretakerView",
    ),
    path("get_caretakers/", views.AssignCaretakerView.as_view(), name="get_caretakers"),

    # Admin - Assign Warden
    path("get_wardens/", views.AssignWardenView.as_view(), name="get_wardens"),
    path(
        "assign_warden/",
        views.AssignWardenView.as_view(),
        name="AssignWardenView"
    ),

    # Admin - Assign Batch
    path("get_batches/", views.AssignBatchView.as_view(), name="get_batches"),
    path(
        "assign_batch/",
        views.AssignBatchView.as_view(),
        name="AssignBatch"
    ),

    path("add-hostel/", views.AddHostelView.as_view(), name="add_hostel"),
    path(
        "admin-hostel-list",
        views.AdminHostelListView.as_view(),
        name="admin_hostel_list",
    ),  # URL for displaying the list of hostels
    path(
        "delete-hostel/<str:hall_id>/",
        views.DeleteHostelView.as_view(),
        name="delete_hostel",
    ),
    path(
        "check-hall-exists/",
        views.CheckHallExistsView.as_view(),
        name="check_hall_exists",
    ),
    path("accounts/", include("django.contrib.auth.urls")),
    path("logout/", views.logout_view, name="logout_view"),
    # !! My Change
    path("allotted_rooms/<str:hall_id>/", views.alloted_rooms, name="alloted_rooms"),
    path("all_staff/<int:hall_id>/", views.all_staff, name="all_staff"),
    path(
        "staff/<str:staff_id>/",
        views.StaffScheduleView.as_view(),
        name="staff_schedule",
    ),
    # !!? Inventory
    path(
        "inventory/", views.HostelInventoryView.as_view(), name="hostel_inventory_list"
    ),
    path(
        "inventory/<int:inventory_id>/modify/",
        views.HostelInventoryUpdateView.as_view(),
        name="hostel_inventory_update",
    ),
    path(
        "inventory/<int:inventory_id>/delete/",
        views.HostelInventoryView.as_view(),
        name="hostel_inventory_delete",
    ),
    path(
        "inventory/<int:hall_id>/",
        views.HostelInventoryView.as_view(),
        name="hostel_inventory_by_hall",
    ),
    path("inventory/form/", views.get_inventory_form, name="get_inventory_form"),
    path(
        "inventory/edit_inventory/<int:inventory_id>/",
        views.edit_inventory,
        name="edit_inventory",
    ),
    path("allotted_rooms/", views.alloted_rooms_main, name="alloted_rooms"),
    path("all_staff/", views.all_staff, name="all_staff"),
    # guest room
    path("book_guest_room/", views.request_guest_room, name="book_guest_room"),
    # This th url for the fethcing the all the guestrooms booking..
    path("fetching_guest_room_request/", views.AllGuestRoomBookingData.as_view(), name="fetching_guest_room_request"),
    path("get_guest_room_request_students/", views.GetGuestRoomForStudents.as_view(), name="GetGuestRoomForStudents"),
    path("get_intender_id/",views.GetIntenderId.as_view(),name="get_intender_id"),
    path("update_guest_room/", views.update_guest_room_status, name="update_guest_room"),
    path(
        "available_guest_rooms/",
        views.available_guestrooms_api,
        name="available_guestrooms_api",
    ),
    # !!todo: Add Fine Functionality
    path("fine/", views.impose_fine_view, name="fine_form_show"),
    path('impose-fine/', views.ImposeFineView.as_view(), name='impose-fine'),
    path("fine/impose/", views.HostelFineView.as_view(), name="fine_form_show"),
    path("fine/impose/list/", views.hostel_fine_list, name="fine_list_show"),
    path(
        "fine/impose/edit/<int:fine_id>/",
        views.show_fine_edit_form,
        name="hostel_fine_edit",
    ),
    path(
        "fine/impose/update/<int:fine_id>/",
        views.update_student_fine,
        name="update_student_fine",
    ),
    path(
        "fine/impose/list/update/<int:fine_id>/",
        views.HostelFineUpdateView.as_view(),
        name="fine_update",
    ),
    path(
        "fine/delete/<int:fine_id>/",
        views.HostelFineUpdateView.as_view(),
        name="fine_delete",
    ),
    path("fine-show/", views.student_fine_details, name="fine_show"),
    path("student/<str:username>/name/", views.get_student_name, name="find_name"),
    path(
        "edit-student/<str:student_id>/",
        views.EditStudentView.as_view(),
        name="edit_student",
    ),
    path(
        "remove-student/<str:student_id>/",
        views.RemoveStudentView.as_view(),
        name="remove-student",
    ),
    path(
        "fetch-fine/",
        views.HostelFineListView.as_view(),
        name="fetch-fine",
    ),
    path(
        "update-fine-status/<int:fine_id>/",
        views.HostelFineUpdateView.as_view(),
        name="update-fine-status",
    ),
    path("download_hostel_allotment/", views.DownloadHostelAllotment.as_view(), name="download_hostel_allotment"),
]
