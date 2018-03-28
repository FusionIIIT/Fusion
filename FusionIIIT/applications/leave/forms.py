from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from django.forms import ValidationError as VE
from django.forms.formsets import BaseFormSet
from django.utils import timezone

from applications.leave.models import LeavesCount, LeaveSegment, LeaveType

from .helpers import get_user_choices


class EmployeeCommonForm(forms.Form):

    purpose = forms.CharField(widget=forms.TextInput)
    is_station = forms.BooleanField(initial=False, required=False)
    station_leave_info = forms.CharField(widget=forms.Textarea, required=False)


class LeaveSegmentForm(forms.Form):

    try:
        LEAVE_TYPES = list((leave_type.id, leave_type.name)
                           for leave_type in LeaveType.objects.all())
    except:
        LEAVE_TYPES = []

    leave_type = forms.ChoiceField(label='Leave Type', choices=LEAVE_TYPES)
    start_date = forms.DateField(label='Leave From', required=True)
    end_date = forms.DateField(label='Leave To', required=True)
    document = forms.FileField(label='Related Document', required=False)
    start_half = forms.BooleanField(label='Half Day at start', required=False)
    end_half = forms.BooleanField(label='Half Day at end', required=False)

    def clean(self, *args, **kwargs):
        super(LeaveSegmentForm, self).clean(*args, **kwargs)
        data = self.cleaned_data
        errors = dict()
        if data['start_date'] < data['end_date']:
            pass
        elif data['start_date'] == data['end_date']:
            if data['start_half'] and data['end_half']:
                errors['start_half'] = ['Invalid Input']
                errors['end_half'] = ['Invalid Input']
        else:
            errors['start_date'] = ['Start date must not be more than End date.']

        now = timezone.localtime(timezone.now()).date()

        if data['start_date'] < now:
            error = 'You have inserted past date in Start Date Field'
            if 'start_date' in errors:
                errors['start_date'].append(error)
            else:
                errors['start_date'] = error

        if data['end_date'] < now:
            error = 'You have inserted past date in End Date Field'
            if 'end_date' in errors:
                errors['end_date'].append(error)
            else:
                errors['end_date'] = error

        leave_type = LeaveType.objects.filter(id=data['leave_type']).first()
        if leave_type and leave_type.requires_proof and not data.get('document'):
            errors['document'] = [f'{leave_type.name} requires a document for proof.']

        if errors.keys():
            raise VE(errors)

        return self.cleaned_data


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

    def clean(self):
        data = self.cleaned_data

        start_date, end_date = data['admin_start_date'], data['admin_end_date']

        if start_date > end_date:
            raise VE({'admin_start_date': ['Start Date must not be more than End Date']})

        rep_user = User.objects.get(username=data['admin_rep'])

        if LeaveSegment.objects.filter(Q(leave__applicant=rep_user),
                                       ~Q(leave__status='rejected'),
                                       Q(start_date__range=[start_date, end_date]) |
                                       Q(end_date__range=[start_date, end_date])).exists():

            raise VE({'admin_rep': ['User may be on leave in this period.']})

        return self.cleaned_data


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

    def clean(self):
        data = self.cleaned_data

        start_date, end_date = data['acad_start_date'], data['acad_end_date']

        if start_date > end_date:
            raise VE({'acad_start_date': ['Start Date must not be more than End Date']})

        rep_user = User.objects.get(username=data['acad_rep'])

        if LeaveSegment.objects.filter(Q(leave__applicant=rep_user),
                                       ~Q(leave__status='rejected'),
                                       Q(start_date__range=[start_date, end_date]) |
                                       Q(end_date__range=[start_date, end_date])).exists():

            raise VE({'acad_rep': ['User may be on leave in this period.']})

        return self.cleaned_data


class BaseLeaveFormSet(BaseFormSet):

    def __init__(self, *args, **kwargs):
        if 'user' in kwargs:
            self.user = kwargs.pop('user')

        super(BaseLeaveFormSet, self).__init__(*args, **kwargs)

    def clean(self):
        super(BaseLeaveFormSet, self).clean()
        curr_year = timezone.now().year
        leave_counts = LeavesCount.objects.filter(user=self.user, year=curr_year)
        mapping = dict()
        for form in self.forms:
            # if form.is_valid():
            try:
                data = form.cleaned_data
                leave_type = data.get('leave_type')
                count = (data.get('end_date') - data.get('start_date')).days + 1
                if data.get('start_half'):
                    count -= 0.5
                if data.get('end_half'):
                    count -= 0.5
                if leave_type in mapping.keys():
                    mapping[leave_type] += count
                else:
                    mapping[leave_type] = count
            except TypeError:
                pass

        for key, value in mapping.items():
            tp = leave_counts.get(leave_type__id=key)
            if tp.remaining_leaves < value:
                raise VE(f'There are only {tp.remaining_leaves} {tp.leave_type.name} '
                         f'Leaves remaining and you have filled {value}.')


class BaseAcadFormSet(BaseFormSet):
    def clean(self):
        pass


class BaseAdminFormSet(BaseFormSet):
    def clean(self):
        pass


class BaseCommonFormSet(BaseFormSet):
    def clean(self):
        pass
