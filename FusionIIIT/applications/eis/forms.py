from django import forms

from.models import *

class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=5000)
    fileUpload = forms.FileField()

class UserForm(forms.ModelForm):
    class Meta:
        model = emp_achievement
        fields = ['a_type', 'details', 'a_day', 'a_month', 'a_year']

class ConfrenceForm(forms.ModelForm):

    class Meta:
        model = emp_confrence_organised
        fields = ['role1', 'name', 'venue', 'start_date', 'end_date', 'k_year']
        widgets = {
            'start_date': forms.DateInput(attrs={'class':'datepicker'}),
            'end_date': forms.DateInput(attrs={'class': 'datepicker'}),
        }
