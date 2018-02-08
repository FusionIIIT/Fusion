from django import forms
from django.forms.formsets import BaseFormSet
from applications.leave.models import LeaveType
from django.contrib.auth.models import User


LEAVE_TYPES = (
    ((leave_type.id, leave_type.name) for leave_type in LeaveType.objects.all())
)


class EmployeeCommonForm(forms.Form):
    leave_type = forms.CharField(widget=forms.Select(choices=LEAVE_TYPES))
    purpose = forms.CharField(widget=forms.TextInput)
    is_station = forms.BooleanField(initial=False, required=False)
    station_start_date = forms.DateField(label='From')
    station_end_date = forms.DateField(label='To')


class LeaveSegmentForm(forms.Form):
    start_date = forms.DateField(label='From')
    end_date = forms.DateField(label='To')


class AdminReplacementForm(forms.Form):
    admin_start_date = forms.DateField(label='From')
    admin_end_date = forms.DateField(label='To')

    def __init__(self, *args, **kwargs):
        if 'user' in kwargs:
            self.user = kwargs.pop('user')

        super(AdminReplacementForm, self).__init__(*args, **kwargs)

        try:
            user_type = self.user.extrainfo.user_type
            ALL_USERS = User.objects.all()
            # TODO: Add code for userchoices
            USET_CHOICES = []
            # USER_CHOICES = list((user.username, '{} {}'.format(user.first_name, user.last_name) \
            #                   for user in ALL_USERS if user.extrainfo.user_type==user_type \
            #                   and user != self.user))
        except:
            USER_CHOICES = []

        self.fields['admin_rep'] = forms.CharField(label='Administrative Responsibility To: ',
                                                   widget=forms.Select(choices=USER_CHOICES))


class AcademicReplacementForm(forms.Form):
    acad_start_date = forms.DateField(label='From')
    acad_end_date = forms.DateField(label='To')

    def __init__(self, *args, **kwargs):
        if 'user' in kwargs:
            self.user = kwargs.pop('user')

        super(AcademicReplacementForm, self).__init__(*args, **kwargs)

        try:
            user_type = self.user.extrainfo.user_type
            ALL_USERS = User.objects.all()
            # USER_CHOICES = list((user.username, '{} {}'.format(user.first_name, user.last_name) \
            #                   for user in ALL_USERS if user.extrainfo.user_type==user_type \
            #                   and user != self.user))
        except:
            USER_CHOICES = []

        self.fields['acad_rep'] = forms.CharField(label='Academic Responsibility To: ',
                                                   widget=forms.Select(choices=USER_CHOICES))


class BaseLeaveFormSet(BaseFormSet):

    def clean(self):
        pass
