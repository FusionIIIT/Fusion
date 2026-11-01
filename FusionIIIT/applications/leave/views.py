from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
import csv
from django.shortcuts import render
from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone

from applications.globals.models import HoldsDesignation, Designation

from .handlers import (handle_faculty_leave_application,
                       handle_staff_leave_application,
                       handle_student_leave_application,
                       handle_offline_leave_application,
                       process_staff_faculty_application,
                       process_student_application, send_faculty_leave_form,
                       send_staff_leave_form, send_student_leave_form, send_offline_leave_form,
                       delete_leave_application)

from .forms import (AcademicReplacementFormOffline, AdminReplacementFormOffline,
                    EmployeeCommonFormOffline, LeaveSegmentFormOffline )
from .models import ELMAccountTransaction, ELMWorkflowTask, Leave, LeaveAdministrators, LeavesCount
from .elm_services import (modify_pending, nominate_new_substitute,
                           record_offline_leave, respond_to_task, submit_change,
                           submit_leave, withdraw_pending)


class ELMApplicationForm(forms.Form):
    CATEGORY_CHOICES = (('CL', 'Casual Leave'), ('RH', 'Restricted Holiday'),
                        ('SCL', 'Special Casual Leave'), ('EL', 'Earned Leave'),
                        ('COL', 'Commuted Leave'), ('VL', 'Vacation Leave'))
    category = forms.ChoiceField(choices=CATEGORY_CHOICES)
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    start_half = forms.BooleanField(required=False)
    end_half = forms.BooleanField(required=False)
    purpose = forms.CharField(max_length=500, widget=forms.Textarea)
    station_leave = forms.BooleanField(required=False)
    station_details = forms.CharField(max_length=500, required=False)
    substitute = forms.ModelChoiceField(queryset=User.objects.filter(extrainfo__user_type__in=('faculty', 'staff'), is_active=True),
                                        required=False)
    medical_evidence = forms.FileField(required=False)

    def clean(self):
        data = super().clean()
        if data.get('station_leave') and not data.get('station_details'):
            self.add_error('station_details', 'Enter Station Leave details when selected.')
        return data


@login_required(login_url='/accounts/login')
def leave(request):

    user_type = request.user.extrainfo.user_type
    
    
    if request.method == 'POST':

        response = None

        if user_type == 'faculty':
            response = handle_faculty_leave_application(request)
        elif user_type == 'staff':
            response = handle_staff_leave_application(request)
        else:
            response = handle_student_leave_application(request)

        return response

    if user_type == 'faculty':
        response = send_faculty_leave_form(request)
    elif user_type == 'staff':
        response = send_staff_leave_form(request)
    else:
        response = send_student_leave_form(request)

    #response = send_offline_leave_form(request)

    return response

@login_required(login_url='/accounts/login')
def leavemanager(request):

    #user_designation = request.user.holds_designations.get(designation__name='Assistant Registrar')
    #user_designation = str(user_designation).split(' - ')
    desig = list(HoldsDesignation.objects.select_related('user','working','designation').all().filter(working = request.user).values_list('designation'))
    b = [i for sub in desig for i in sub]
    c=False
    for i in b:
        if str(Designation.objects.get(id=i))=='Assistant Registrar':
            c=True
            break

    
    if request.method == 'POST':
        response = None

        if c:
            response = handle_offline_leave_application(request)
        return response

    if c:
        return send_offline_leave_form(request)
    
    """form1 = LeaveSegmentFormOffline()
    form2 = AcademicReplacementFormOffline()
    form3 = AdminReplacementFormOffline()
    form4 = EmployeeCommonFormOffline()

    return render(request, 'leaveModule/test.html', {'leave':form1,
        'acad':form2,'admin':form3,'common':form4})"""
    
    

    

    

@login_required(login_url='/accounts/login')
def process_request(request):
    if request.is_ajax():
        if request.POST.get('stud'):
            return process_student_application(request)

        return process_staff_faculty_application(request)
    return JsonResponse({'status': 'Failed'}, status=400)


@login_required(login_url='/accounts/login')
def get_leave_requests(request):
    return HttpResponse('Hey Works')


@login_required(login_url='/accounts/login')
def delete_leave(request):

    if request.method == 'POST':
        return delete_leave_application(request)
    else:
        response = JsonResponse({'message': 'Failed'}, status=400)

    return response


@login_required(login_url='/accounts/login')
def generate_form(request):
    id = request.GET.get('id')
    leave = request.user.all_leaves.filter(id=id)
    if leave:
        response = render(request, 'leaveModule/generate_form.html', {'leave': leave.first()})
    else:
        response = HttpResponseForbidden()

    return response

@login_required(login_url='/accounts/login')
def generate_form_offline(request):
    id = request.GET.get('id')
    leave = request.user.all_leaves_offline.filter(id=id)
    if leave:
        response = render(request, 'leaveModule/generate_form_offline.html', {'leave': leave.first()})
    else:
        response = HttpResponseForbidden()

    return response


@login_required(login_url='/accounts/login')
def elm_dashboard(request):
    """ELM screen within the existing legacy leave application."""
    if request.method == 'POST':
        form = ELMApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                data = form.cleaned_data
                leave = submit_leave(request.user, data['category'], data['start_date'],
                    data['end_date'], data['purpose'], data['start_half'], data['end_half'],
                    data['substitute'], data['station_leave'], data['station_details'],
                    data['medical_evidence'])
                messages.success(request, 'Leave request {} was submitted.'.format(leave.pk))
                return redirect(reverse('leave:elm-dashboard'))
            except ValidationError as exc:
                form.add_error(None, exc.messages)
    else:
        form = ELMApplicationForm()
    user_type = getattr(getattr(request.user, 'extrainfo', None), 'user_type', '')
    balances = LeavesCount.objects.filter(user=request.user, year=timezone.now().year) \
        .select_related('leave_type')
    applications = Leave.objects.filter(applicant=request.user).exclude(elm_state='').prefetch_related('segments') \
        .order_by('-timestamp')[:50]
    substitutes = User.objects.filter(extrainfo__user_type__in=('faculty', 'staff'), is_active=True) \
        .exclude(pk=request.user.pk).order_by('first_name', 'last_name')
    tasks = ELMWorkflowTask.objects.filter(assignee=request.user, status='pending') \
        .select_related('leave', 'leave__applicant').order_by('created_at')
    transactions = ELMAccountTransaction.objects.filter(user=request.user).order_by('-created_at')[:100]
    is_leave_admin = request.user.is_superuser or LeaveAdministrators.objects.filter(user=request.user).exists()
    return render(request, 'leaveModule/elm_dashboard.html', {
        'form': form, 'balances': balances, 'applications': applications,
        'tasks': tasks, 'substitutes': substitutes,
        'transactions': transactions,
        'is_leave_admin': is_leave_admin,
        'is_employee': user_type in ('faculty', 'staff')})


@login_required(login_url='/accounts/login')
def elm_task_action(request, task_id):
    if request.method != 'POST':
        return redirect('leave:elm-dashboard')
    task = get_object_or_404(ELMWorkflowTask, pk=task_id, assignee=request.user, status='pending')
    try:
        respond_to_task(task, request.user, request.POST.get('decision', ''),
                        request.POST.get('remark', ''))
        messages.success(request, 'Workflow response recorded.')
    except ValidationError as exc:
        messages.error(request, ' '.join(exc.messages))
    return redirect('leave:elm-dashboard')


@login_required(login_url='/accounts/login')
def elm_withdraw(request, leave_id):
    if request.method == 'POST':
        leave = get_object_or_404(Leave, pk=leave_id, applicant=request.user)
        try:
            withdraw_pending(leave, request.user)
            messages.success(request, 'Pending leave request withdrawn.')
        except ValidationError as exc:
            messages.error(request, ' '.join(exc.messages))
    return redirect('leave:elm-dashboard')


@login_required(login_url='/accounts/login')
def elm_change(request, leave_id):
    if request.method == 'POST':
        leave = get_object_or_404(Leave, pk=leave_id, applicant=request.user)
        kind = request.POST.get('change_type')
        try:
            values = {'details': request.POST.get('details', '')}
            if kind == 'extension':
                values['end_date'] = forms.DateField().clean(request.POST.get('end_date'))
                if request.POST.get('substitute'):
                    values['substitute'] = get_object_or_404(User, pk=request.POST.get('substitute'),
                        extrainfo__user_type__in=('faculty', 'staff'), is_active=True)
            elif kind == 'resumption':
                values['actual_return_date'] = forms.DateField().clean(request.POST.get('actual_return_date'))
            submit_change(leave, request.user, kind, **values)
            messages.success(request, 'Leave lifecycle request recorded for review.')
        except (ValidationError, ValueError) as exc:
            messages.error(request, ' '.join(getattr(exc, 'messages', [str(exc)])))
    return redirect('leave:elm-dashboard')


@login_required(login_url='/accounts/login')
def elm_substitute(request, leave_id):
    if request.method == 'POST':
        leave = get_object_or_404(Leave, pk=leave_id, applicant=request.user)
        substitute = get_object_or_404(User, pk=request.POST.get('substitute'),
                                       extrainfo__user_type__in=('faculty', 'staff'), is_active=True)
        try:
            nominate_new_substitute(leave, request.user, substitute)
            messages.success(request, 'The new substitute has been asked to respond.')
        except ValidationError as exc:
            messages.error(request, ' '.join(exc.messages))
    return redirect('leave:elm-dashboard')


@login_required(login_url='/accounts/login')
def elm_modify(request, leave_id):
    if request.method == 'POST':
        leave = get_object_or_404(Leave, pk=leave_id, applicant=request.user)
        form = ELMApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                data = form.cleaned_data
                modify_pending(leave, request.user, data['category'], data['start_date'],
                    data['end_date'], data['purpose'], data['start_half'], data['end_half'],
                    data['substitute'], data['station_leave'], data['station_details'],
                    data['medical_evidence'])
                messages.success(request, 'Pending request updated and sent through revalidation.')
            except ValidationError as exc:
                messages.error(request, ' '.join(exc.messages))
        else:
            messages.error(request, 'Please provide valid replacement request details.')
    return redirect('leave:elm-dashboard')


@login_required(login_url='/accounts/login')
def elm_offline_entry(request):
    if not (request.user.is_superuser or LeaveAdministrators.objects.filter(user=request.user).exists()):
        return HttpResponseForbidden()
    employee = forms.ModelChoiceField(queryset=User.objects.filter(
        extrainfo__user_type__in=('faculty', 'staff'), is_active=True), label='Employee')
    form = forms.Form(request.POST or None, request.FILES or None)
    form.fields['employee'] = employee
    form.fields['category'] = forms.ChoiceField(choices=ELMApplicationForm.CATEGORY_CHOICES)
    form.fields['start_date'] = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    form.fields['end_date'] = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    form.fields['purpose'] = forms.CharField(max_length=500)
    form.fields['sanction_reference'] = forms.CharField(max_length=200)
    form.fields['start_half'] = forms.BooleanField(required=False)
    form.fields['end_half'] = forms.BooleanField(required=False)
    form.fields['station_leave'] = forms.BooleanField(required=False)
    form.fields['station_details'] = forms.CharField(max_length=500, required=False)
    form.fields['medical_evidence'] = forms.FileField(required=False)
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        try:
            leave = record_offline_leave(data['employee'], request.user, data['category'],
                data['start_date'], data['end_date'], data['purpose'], data['sanction_reference'],
                data['start_half'], data['end_half'], data['station_leave'], data['station_details'],
                data['medical_evidence'])
            messages.success(request, 'Offline-sanctioned leave {} was synchronized.'.format(leave.pk))
            return redirect('leave:elm-dashboard')
        except ValidationError as exc:
            form.add_error(None, exc.messages)
    return render(request, 'leaveModule/elm_offline.html', {'form': form})


@login_required(login_url='/accounts/login')
def elm_export(request, leave_id):
    leave = get_object_or_404(Leave, pk=leave_id, applicant=request.user)
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="leave-{}.csv"'.format(leave.pk)
    writer = csv.writer(response)
    writer.writerow(('Request', 'Category', 'Start', 'End', 'Purpose', 'Status', 'Station Leave'))
    for segment in leave.segments.select_related('leave_type').all():
        writer.writerow((leave.pk, segment.leave_type.name if segment.leave_type else '',
            segment.start_date, segment.end_date, leave.purpose, leave.elm_state,
            leave.station_details if leave.station_leave else 'No'))
    return response
