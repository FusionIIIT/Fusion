from django import forms
from .models import HostelNoticeBoard, Hall, GuestRoomBooking
import re
from django.core.exceptions import ValidationError

class HostelNoticeBoardForm(forms.ModelForm):
    class Meta:
        model = HostelNoticeBoard
        fields = ('hall', 'head_line', 'content', 'description')
    
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
            'nationality'
        )

    # def clean_guest_phone(self):
    #     guest_phone = self.cleaned_data['guest_phone']
    #     valid = re.fullmatch('^[6-9]\d{9}$', guest_phone)
    #     if valid:
    #         return guest_phone
    #     else:
    #         raise ValidationError(
    #             'Please enter a valid 10-digit mobile number.'
    #         )

    # def clean_guest_email(self):
    #     guest_email = self.cleaned_data['guest_email']
    #     valid = re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', guest_email)
        # if valid:
        #     return guest_email
        # else:
        #     raise ValidationError(
        #         'Please enter a valid email address.'
        #     )
     
