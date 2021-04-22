from django import forms
from .models import Employee,EmpConfidentialDetails,ForeignService

class DateInput(forms.DateInput):
    input_type = 'date'


class EditDetailsForm(forms.ModelForm):

    class Meta:
        model = Employee
        fields = ['extra_info', 'father_name', 'mother_name', 'religion', 'category',
                  'cast', 'home_state', 'home_district', 'date_of_joining', 'designation','blood_group']
    
        widgets = {
            'date_of_joining':DateInput()
        }
    
    def __init__(self, *args, **kwargs):
        super(EditDetailsForm, self).__init__(*args, **kwargs)
     


class EditConfidentialDetailsForm(forms.ModelForm):

    class Meta:
        model = EmpConfidentialDetails
        fields = ['extra_info', 'aadhar_no', 
                  'maritial_status', 'bank_account_no', 'salary']

    def __init__(self, *args, **kwargs):
       super(EditConfidentialDetailsForm, self).__init__(*args, **kwargs)

                

class EditServiceBookForm(forms.ModelForm):

    class Meta:
        model = ForeignService
        fields = ['extra_info', 'start_date', 'end_date', 'job_title', 'organisation',
                  'description', 'salary_source', 'designation','service_type']
        widgets = {'start_date': DateInput(),'end_date':DateInput()}

    def __init__(self, *args, **kwargs):
       super(EditServiceBookForm, self).__init__(*args, **kwargs)
             