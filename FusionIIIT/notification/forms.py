from django import forms
from .models import Announcements, AnnouncementRecipients
from applications.globals.models import ExtraInfo
from django.contrib.auth.models import User


class AnnouncementForm(forms.ModelForm):
    specific_users = forms.CharField(
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'ui fluid multiple search selection dropdown'})
    )

    class Meta:
        model = Announcements
        fields = ['message', 'target_group', 'department', 'batch', 'specific_users']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        target_group = cleaned_data.get('target_group')

        # Validation based on target group
        if target_group == 'faculty' and not cleaned_data.get('department'):
            self.add_error('department', 'Department is required for faculty announcements.')
        elif target_group == 'students':
            if not cleaned_data.get('department') or not cleaned_data.get('batch'):
                self.add_error('department', 'Department is required for student announcements.')
                self.add_error('batch', 'Batch is required for student announcements.')

        return cleaned_data