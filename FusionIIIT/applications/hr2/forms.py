from django import forms
from .models import Employee


class editDetailsForm(forms.ModelForm):
    # body_text = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = Employee
        fields = ['extra_info', 'father_name', 'mother_name', 'religion', 'category',
                  'cast', 'home_state', 'home_district', 'height', 'date_of_joining', 'designation','blood_group']
