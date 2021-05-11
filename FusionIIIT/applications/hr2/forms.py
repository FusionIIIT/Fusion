from django import forms
from .models import Employee, EmpConfidentialDetails, ForeignService
from applications.globals.models import ExtraInfo
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class DateInput(forms.DateInput):
    input_type = 'date'


class EditDetailsForm(forms.ModelForm):

    class Meta:
        model = Employee
        fields = ['extra_info', 'father_name', 'mother_name', 'religion', 'category',
                  'cast', 'home_state', 'home_district', 'date_of_joining', 'designation', 'blood_group']

        widgets = {
            'date_of_joining': DateInput()
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
                  'description', 'salary_source', 'designation', 'service_type']
        widgets = {'start_date': DateInput(), 'end_date': DateInput()}

    def __init__(self, *args, **kwargs):
        super(EditServiceBookForm, self).__init__(*args, **kwargs)


class NewUserForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1",
                  "password2", 'first_name', 'last_name')

    def save(self, commit=True):
        user = super(NewUserForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class AddExtraInfo(forms.ModelForm):
    class Meta:
        model = ExtraInfo
        fields = ['id', 'user', 'title', 'sex', 'date_of_birth', 'title', 'phone_no',
                  'address', 'user_type', 'about_me', 'user_status']
        widgets = {'date_of_birth': DateInput()}

    def __init__(self, *args, **kwargs):
        super(AddExtraInfo, self).__init__(*args, **kwargs)
