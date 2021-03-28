from django import forms
from .models import Employee,EmpConfidentialDetails


class editDetailsForm(forms.ModelForm):

    class Meta:
        model = Employee
        fields = ['extra_info', 'father_name', 'mother_name', 'religion', 'category',
                  'cast', 'home_state', 'home_district', 'height', 'date_of_joining', 'designation','blood_group']
    
    def __init__(self, *args, **kwargs):
       super(editDetailsForm, self).__init__(*args, **kwargs)
       self.fields['extra_info'].widget.attrs['disabled'] = True


class editConfidentialDetailsForm(forms.ModelForm):

    class Meta:
        model = EmpConfidentialDetails
        fields = ['extra_info', 'aadhar_no', 'medical_certificate', 'age_certificate', 'cast_certificate',
                  'maritial_status', 'bank_account_no', 'salary']

    def __init__(self, *args, **kwargs):
       super(editConfidentialDetailsForm, self).__init__(*args, **kwargs)
       self.fields['extra_info'].widget.attrs['disabled'] = True
                


