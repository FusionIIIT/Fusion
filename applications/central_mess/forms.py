from django import forms

from .models import Mess_minutes


class MinuteForm(forms.ModelForm):
    class Meta:
        model = Mess_minutes
        fields = ('meeting_date', 'mess_minutes')
