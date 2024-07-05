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


class AddNewHallForm(forms.ModelForm):
    single_seater = forms.IntegerField(min_value=0, label='Single Seater Rooms')
    double_seater = forms.IntegerField(min_value=0, label='Double Seater Rooms')
    triple_seater = forms.IntegerField(min_value=0, label='Triple Seater Rooms')

    class Meta:
        model = Hall
        fields = ['hall_id', 'hall_name','single_seater', 'double_seater', 'triple_seater']
        help_texts = {
            'hall_id': 'Hall ID should be like hall1, hall2, hall3, etc.',
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['hall_id'].help_text = '<span style="color: red;">Hall ID should be like hall1, hall2, hall3, etc.</span>'