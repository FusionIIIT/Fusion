from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from django.forms import ValidationError as VE
from django.forms.formsets import BaseFormSet
from django.utils import timezone

from applications.leave.models import LeavesCount, LeaveSegment, LeaveType

from .helpers import get_leave_days, get_special_leave_count, get_user_choices


class StudentApplicationForm(forms.Form):

    STUDENT_LEAVE_CHOICES = (
        ('Casual', 'Casual'),
        ('Medical', 'Medical')
    )

    leave_type = forms.ChoiceField(label='Leave Type', choices=STUDENT_LEAVE_CHOICES)
    start_date = forms.DateField(label='From')
    end_date = forms.DateField(label='To')
    purpose = forms.CharField(label='Purpose', widget=forms.TextInput)
    address = forms.CharField(label='Address')
    document = forms.FileField(label='Related Document', required=False)

    def __init__(self, *args, **kwargs):
        if 'user' in kwargs:
            self.user = kwargs.pop('user')
        super(StudentApplicationForm, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        super(StudentApplicationForm, self).clean(*args, **kwargs)
        data = self.cleaned_data
        errors = dict()
        today = timezone.now().date()
        """if data.get('start_date') < today:
            errors['start_date'] = ['Past Dates are not allowed']
        if data.get('end_date') < today:
            errors['end_date'] = ['Past Dates are not allowed']
"""
        lt = LeaveType.objects.filter(name=data.get('leave_type')).first()

        if lt.requires_proof and not data.get('document'):
            errors['document'] = [f'{lt.name} Leave requires document proof']

        if data.get('start_date') > data.get('end_date'):
            if 'start_date' in errors:
                errors['start_date'].append('Start Date must be less than End Date')
            else:
                errors['start_date'] = ['Start Date must be less than End Date']

        leave_type = LeaveType.objects.get(name=data.get('leave_type'))
        count = get_leave_days(data.get('start_date'), data.get('end_date'),
                               leave_type, False, False)

        remaining_leaves = LeavesCount.objects.get(user=self.user, leave_type=leave_type) \
                                              .remaining_leaves
        if remaining_leaves < count:
            errors['leave_type'] = f'You have only {remaining_leaves} {leave_type.name} leaves' \
                                    ' remaining.'

        raise VE(errors)


class EmployeeCommonForm(forms.Form):

    purpose = forms.CharField(widget=forms.TextInput)
    #is_station = forms.BooleanField(initial=False, required=False)
    leave_info = forms.CharField(label='Information', widget=forms.Textarea, required=False)

    def clean(self):
        super(EmployeeCommonForm, self).clean()
        data = self.cleaned_data

        #if data.get('is_station') and not data.get('leave_info'):
        if not data.get('leave_info'):
            raise VE({'leave_info': ['If there is a station leave, provide details about it.']})

        return self.cleaned_data


class LeaveSegmentForm(forms.Form):

    try:
        LEAVE_TYPES = list((leave_type.id, leave_type.name)
                           for leave_type in LeaveType.objects.all())
    except:
        LEAVE_TYPES = []

    #Changed by Abhay Gupta
    l_type_fac=list((leave_type.id, leave_type.name) for leave_type in LeaveType.objects.all())
    l_type_staff=list((leave_type.id, leave_type.name) for leave_type in LeaveType.objects.filter(for_staff=1))
    #l_type=list(leave_type.name for leave_type in LeaveType.objects.all())

    leave_type = forms.ChoiceField(label='Leave Type', choices=LEAVE_TYPES)
    start_date = forms.DateField(label='Leave From', required=True)
    end_date = forms.DateField(label='Leave To', required=True)
    document = forms.FileField(label='Related Document', required=False)
    start_half = forms.BooleanField(label='Half Day at start', required=False)
    end_half = forms.BooleanField(label='Half Day at end', required=False)
    address = forms.CharField(label='Out of Station Address', required=False)

    def clean(self, *args, **kwargs):
        super(LeaveSegmentForm, self).clean(*args, **kwargs)
        data = self.cleaned_data
        errors = dict()

        def check_special_leave_overlap(start_date, end_date, leave_type_id):
            leave_type = LeaveType.objects.get(id=leave_type_id)
            if leave_type.name.lower() in ['restricted', 'vacation']:
                count = get_special_leave_count(start_date, end_date, leave_type.name.lower())
                if count < 0:
                    return 'The period for this leave doesn\'t match with holiday calendar' \
                           '. Check Academic Calendar.'

            return ''

        if data['start_date'] < data['end_date']:
            error = check_special_leave_overlap(data.get('start_date'), data.get('end_date'),
                                                data.get('leave_type'))

            if error:
                if 'leave_type' in errors:
                    errors['leave_type'].append(error)
                else:
                    errors['leave_type'] = [error, ]

        elif data['start_date'] == data['end_date']:
            #if data.get('leave_type')==2:
            #    restricted_holidays=list(res.date for res in RestrictedHoliday.objects.all())
            #    print(restricted_holidays)
            #    print(data.get('start_date'))

            if data['start_half'] and data['end_half']:
                errors['start_half'] = ['Invalid Input']
                errors['end_half'] = ['Invalid Input']

            else:
                error = check_special_leave_overlap(data.get('start_date'), data.get('end_date'),
                                                    data.get('leave_type'))
                if error:
                    if 'leave_type' in errors:
                        errors['leave_type'].append(error)
                    else:
                        errors['leave_type'] = [error, ]
        else:
            errors['start_date'] = ['Start date must not be more than End date.']





        #now = timezone.now().date()

        """if data['start_date'] < now:
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
                """

        leave_type = LeaveType.objects.filter(id=data['leave_type']).first()
        if leave_type and leave_type.requires_proof and not data.get('document'):
            errors['document'] = [f'{leave_type.name} requires a document for proof.']

        leave_type = LeaveType.objects.filter(id=data['leave_type']).first()
        if leave_type and leave_type.requires_address and not data.get('address'):
            errors['document'] = [f'{leave_type.name} requires Out of Station address.']

        
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
        # print(USER_CHOICES)
        self.fields['admin_rep'] = forms.ChoiceField(label='Administrative Responsibility To: ',
                                                     choices=USER_CHOICES)

    def clean(self):
        super(AdminReplacementForm, self).clean()
        data = self.cleaned_data

        start_date, end_date = data['admin_start_date'], data['admin_end_date']

        errors = dict()

        if start_date > end_date:
            errors['admin_start_date'] = ['Start Date must not be more than End Date']

        now = timezone.now().date()
        if data['admin_start_date'] < now:
            error = 'You have inserted past date.'
            if 'admin_start_date' in errors:
                errors['admin_start_date'].append(error)
            else:
                errors['admin_start_date'] = error

        if data['admin_end_date'] < now:
            error = 'You have inserted past date.'
            if 'admin_end_date' in errors:
                errors['admin_end_date'].append(error)
            else:
                errors['admin_end_date'] = error

        rep_user = User.objects.get(username=data['admin_rep'])

        if LeaveSegment.objects.filter(Q(leave__applicant=rep_user),
                                       ~Q(leave__status='rejected'),
                                       Q(start_date__range=[start_date, end_date]) |
                                       Q(end_date__range=[start_date, end_date])).exists():

            errors['admin_rep'] = [f'{rep_user.get_full_name()} may be on leave in this period.']

        if errors.keys():
            raise VE(errors)

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
        super(AcademicReplacementForm, self).clean()
        data = self.cleaned_data
        errors = dict()
        start_date, end_date = data['acad_start_date'], data['acad_end_date']

        if start_date > end_date:
            errors['acad_start_date'] = ['Start Date must not be more than End Date']

        now = timezone.now().date()
        if data['acad_start_date'] < now:
            error = 'You have inserted past date.'
            if 'acad_start_date' in errors:
                errors['acad_start_date'].append(error)
            else:
                errors['acad_start_date'] = error

        if data['acad_end_date'] < now:
            error = 'You have inserted past date.'
            if 'acad_end_date' in errors:
                errors['acad_end_date'].append(error)
            else:
                errors['acad_end_date'] = error

        rep_user = User.objects.get(username=data['acad_rep'])

        if LeaveSegment.objects.filter(Q(leave__applicant=rep_user),
                                       ~Q(leave__status='rejected'),
                                       Q(start_date__range=[start_date, end_date]) |
                                       Q(end_date__range=[start_date, end_date])).exists():

            errors['acad_rep'] = [f'{rep_user.get_full_name()} may be on leave in this period.']

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
            try:
                data = form.cleaned_data
                leave_type = LeaveType.objects.get(id=data.get('leave_type'))
                #if leave_type.is_station:
                #    continue

                count = get_leave_days(data.get('start_date'), data.get('end_date'),
                                       leave_type, data.get('start_half'), data.get('end_half'))

                if leave_type in mapping.keys():
                    mapping[leave_type] += count
                else:
                    mapping[leave_type] = count
            except:
                raise VE('Some error occured, please contact admin.')

        for key, value in mapping.items():
            tp = leave_counts.get(leave_type=key)
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
