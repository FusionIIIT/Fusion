from django import forms

from .models import MessMinutes


class MinuteForm(forms.ModelForm):
    class Meta:
        model = MessMinutes
        fields = ('meeting_date', 'mess_minutes')
