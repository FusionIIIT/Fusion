from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.shortcuts import render

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
