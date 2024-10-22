from django.conf.urls import url
from applications.visitor_hostel.api.views  import AddToInventory, InventoryListView

from . import views

app_name = 'visitorhostel'

urlpatterns = [

    url(r'^$', views.visitorhostel, name='visitorhostel'),
    url(r'^get-booking-requests/', views.get_booking_requests, name='get_booking_requests'),
    url(r'^get-active-bookings/', views.get_active_bookings, name='get_active_bookings'),
    url(r'^get-inactive-bookings/', views.get_inactive_bookings, name='get_inactive_bookings'),
    url(r'^get-completed-bookings/', views.get_completed_bookings, name='get_completed_bookings'),
    url(r'^get-booking-form/', views.get_booking_form, name='get_booking_form'),
    url(r'^request-booking/' , views.request_booking , name ='request_booking'),
    url(r'^confirm-booking/' , views.confirm_booking , name ='confirm_booking'),
    url(r'^cancel-booking/', views.cancel_booking, name='cancel_booking'),
    url(r'^cancel-booking-request/', views.cancel_booking_request,name='cancel_booking_request'),
    url(r'^reject-booking/', views.reject_booking, name='reject_booking'),
    url(r'^check-in/', views.check_in, name = 'check_in'),
    url(r'^check-out/', views.check_out, name = 'check_out'),
    url(r'^record-meal/', views.record_meal, name = 'record_meal'),
    url(r'^bill/', views.bill_generation, name = 'bill_generation'),
    url(r'^update-booking/', views.update_booking, name = 'update_booking'),

    url(r'^bill_between_date_range/', views.bill_between_dates, name = 'generate_records'),
    url(r'^room-availability/', views.room_availabity, name = 'room_availabity'),
    url(r'^add-to-inventory/', views.add_to_inventory, name = 'add_to_inventory'),
    url(r'^update-inventory/', views.update_inventory, name = 'update_inventory'),
    url(r'^edit-room-status/', views.edit_room_status, name = 'edit_room_status'),
    url(r'^booking-details/', views.booking_details, name = 'booking_details'),
    url(r'^forward-booking/', views.forward_booking, name = 'forward_booking'),
    #api
    url('api/inventory_add/', AddToInventory.as_view(), name='add-to-inventory'),
    url('api/inventory_list/', InventoryListView.as_view(), name='inventory-list'),
]
