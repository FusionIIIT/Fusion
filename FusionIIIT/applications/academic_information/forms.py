from django import forms

from .models import Meeting


class MinuteForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ('date', 'minutes_file', )
