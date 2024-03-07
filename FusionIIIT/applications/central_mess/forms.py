from django import forms

from .models import Mess_minutes
from .models import Registration_Request


class MinuteForm(forms.ModelForm):
    class Meta:
        model = Mess_minutes
        fields = ('meeting_date', 'mess_minutes')

class MessInfoForm(forms.Form, ):
    MESS_CHOICES= [
        ('mess1', 'Veg Mess'),
        ('mess2', 'Non Veg Mess'),
        ]
    mess_option = forms.CharField(label='Mess Option', widget=forms.Select(
        choices=MESS_CHOICES, attrs={'style': 'border-radius:1rem;padding:7px;'}))
    

class RegistrationRequest(forms.ModelForm):
    class Meta:
        model = Registration_Request
        fields = ('Txn_no','amount','img')    
