from django import forms

from .models import Mess_minutes


class MinuteForm(forms.ModelForm):
    class Meta:
        model = Mess_minutes
        fields = ('meeting_date', 'mess_minutes')

class MessInfoForm(forms.Form, ):
    MESS_CHOICES= [
        ('mess1', 'Veg Mess'),
        ('mess2', 'Non Veg Mess'),
        ]
    mess_option = forms.CharField(label='Mess Option', widget=forms.Select(choices=MESS_CHOICES))