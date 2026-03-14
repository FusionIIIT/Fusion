from django import forms
from .models import HostelNoticeBoard, Hall, GuestRoomBooking


class HostelNoticeBoardForm(forms.ModelForm):
    class Meta:
        model = HostelNoticeBoard
        fields = ('hall', 'head_line', 'content', 'description')

class HallForm(forms.ModelForm):
    class Meta:
        model = Hall
        fields = ['hall_id', 'hall_name', 'max_accomodation', 'assigned_batch','type_of_seater']

class GuestRoomBookingForm(forms.ModelForm):
    class Meta:
        model = GuestRoomBooking 
        fields = (
            'hall',
            'guest_name',
            'guest_phone',
            'guest_email',
            'guest_address',
            'rooms_required',
            'total_guest',
            'purpose',
            'arrival_date',
            'arrival_time',
            'departure_date',
            'departure_time',
            'nationality',
            'room_type'
        )