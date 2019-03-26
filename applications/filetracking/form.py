from django import forms
from .models import post

class PostForm(forms.ModelForm):
    class Meta:
        file = file_uploaded
        fields=('subject', 'sender', 'receiver',
            'sender deishgnation', 'receiver_designation',
             'title', 'post')

