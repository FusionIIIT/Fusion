from django import forms
from django.forms.formsets import BaseFormSet
from applications.leave.models import LeaveType
from django.contrib.auth.models import User
from .helpers import get_user_choices
from django.db.models import Q


class EmployeeCommonForm(forms.Form):

    purpose = forms.CharField(widget=forms.TextInput)
    is_station = forms.BooleanField(initial=False, required=False)
    station_leave_info = forms.CharField(widget=forms.Textarea)


class LeaveSegmentForm(forms.Form):

    LEAVE_TYPES = list((leave_type.id, leave_type.name) for leave_type in LeaveType.objects.all())

    leave_type = forms.ChoiceField(label='Leave Type', choices=LEAVE_TYPES)
    start_date = forms.DateField(label='From')
    end_date = forms.DateField(label='To')
    document = forms.FileField(label='Related Document', required=False)


class AdminReplacementForm(forms.Form):
    admin_start_date = forms.DateField(label='From')
    admin_end_date = forms.DateField(label='To')

    def __init__(self, *args, **kwargs):
        if 'user' in kwargs:
            self.user = kwargs.pop('user')

        super(AdminReplacementForm, self).__init__(*args, **kwargs)

        USER_CHOICES = get_user_choices(self.user)

        self.fields['admin_rep'] = forms.ChoiceField(label='Administrative Responsibility To: ',
                                                     choices=USER_CHOICES)


class AcademicReplacementForm(forms.Form):
    acad_start_date = forms.DateField(label='From')
    acad_end_date = forms.DateField(label='To')

    def __init__(self, *args, **kwargs):
        if 'user' in kwargs:
            self.user = kwargs.pop('user')

        super(AcademicReplacementForm, self).__init__(*args, **kwargs)

        USER_CHOICES = get_user_choices(self.user)

        self.fields['acad_rep'] = forms.ChoiceField(label='Academic Responsibility To: ',
                                                    choices=USER_CHOICES)


class BaseLeaveFormSet(BaseFormSet):

    def clean(self):
        pass


class BaseAcadFormSet(BaseFormSet):
    def clean(self):
        pass


class BaseAdminFormSet(BaseFormSet):
    def clean(self):
        pass


class BaseCommonFormSet(BaseFormSet):
    def clean(self):
        pass
