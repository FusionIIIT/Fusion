import json
import logging
from django.shortcuts import render, get_object_or_404
from .models import *
from applications.globals.models import ExtraInfo
from applications.globals.models import *
from django.db.models import Q
from django.http import Http404
# from .forms import EditDetailsForm, EditConfidentialDetailsForm, EditServiceBookForm, NewUserForm, AddExtraInfo
from django.contrib import messages
from applications.eis.models import *
from django.http import HttpResponse, JsonResponse
from applications.establishment.models import *
from applications.establishment.views import *
from applications.eis.models import *
from applications.globals.models import ExtraInfo, HoldsDesignation, DepartmentInfo, Designation, ModuleAccess
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
from .models import LeaveBalance, LeavePerYear, EmpConfidentialDetails , Employee, LeaveForm
from applications.globals.models import ExtraInfo
from applications.filetracking.sdk.methods import *

# Configure a logger for your module
logger = logging.getLogger(__name__)



def check_hr_access(request):
    """
    Check if the authenticated user has HR module access.
    Returns:
        - True if the user has HR access.
        - False if the user does not have HR access or an error occurs.
    """
    user = request.user

    # Check if the user is authenticated
    if not user.is_authenticated:
        return False

    # Get the user's current designation
    try:
        # Fetch the user's current designation from HoldsDesignation
        

        


        
        

        extra_info = get_object_or_404(ExtraInfo, user=user)
        last_selected_role=extra_info.last_selected_role
        if not last_selected_role:
            
            designations = HoldsDesignation.objects.filter(user=user)
            if designations.exists():
                last_selected_role = designations.last().designation.name
                print(last_selected_role)
                extra_info.last_selected_role = last_selected_role
                extra_info.save()
                last_selected_role=extra_info.last_selected_role
            else:
                return JsonResponse({'error': 'Designation not found'}, status=404)
        request.session['currentDesignationSelected'] = last_selected_role
        ##print(last_selected_role)
        # fetch designation of name last_selected_role
        designation = Designation.objects.filter(name=last_selected_role).first()
        
        
        
        if not designation:
            return False
        # find holdsdesignation of user and designation
        current_designation = HoldsDesignation.objects.filter(working=user, designation=designation).first()
        #print(f"Current Designation: {current_designation.designation.name if current_designation else None}")  # Debugging
        if not current_designation:
            return False
        
        
        # Fetch the ModuleAccess for the user's designation
        module_access = ModuleAccess.objects.filter(designation=current_designation.designation.name).first()
        #print(module_access.hr)
        if not module_access:
            return False

        # Check if HR module access is granted
        return module_access.hr

    except Exception as e:
        # Handle any unexpected errors
        #print(f"Error in check_hr_access: {str(e)}")  # Debugging
        return False
    


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def test(request):
    """
    Test view to check HR access and perform additional actions.
    """
    user = request.user

    # Check if the user is authenticated
    if not user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    # Check if the user has HR access
    if check_hr_access(request):
        # Perform additional actions if HR access is granted
        #print("User has HR access. Performing additional actions...")  # Debugging
        # Add your additional logic here
        return JsonResponse({'message': 'You have HR access. Additional actions performed.'}, status=200)
    else:
        # Return a response if HR access is not granted
        return JsonResponse({'error': 'HR access required'}, status=403)
    




@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_leave_balance(request):
    """
    API endpoint to retrieve the leave balance for the authenticated user.
    Returns:
        - A JSON response containing the leave balance for each leave type.
    """
    user = request.user

    # Check if the user is authenticated
    if not user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)



    # check if the user has HR access
    if not check_hr_access(request):
        return JsonResponse({'error': 'HR access required'}, status=403)
    
    try:
        # Fetch the ExtraInfo object for the user
        extra_info = ExtraInfo.objects.get(user=user)

        # Fetch the leave balance for the user
        #print("1")
        leave_balance = LeaveBalance.objects.filter(empid__id=user.id).first()
        leave_per_year = LeavePerYear.objects.filter(empid__id=user.id).first()
        #print("2")
        if not leave_balance or not leave_per_year:
            return JsonResponse({'error': 'Leave balance data not found'}, status=404)
        #print("3")

        # Prepare the response data
        leave_data = {
            'casual_leave': {
                'allotted': leave_per_year.casual_leave,
                'taken': leave_balance.casual_leave_taken,
                'balance': leave_per_year.casual_leave - leave_balance.casual_leave_taken,
            },
            'special_casual_leave': {
                'allotted': leave_per_year.special_casual_leave,
                'taken': leave_balance.special_casual_leave_taken,
                'balance': leave_per_year.special_casual_leave - leave_balance.special_casual_leave_taken,
            },
            'earned_leave': {
                'allotted': leave_per_year.earned_leave,
                'taken': leave_balance.earned_leave_taken,
                'balance': leave_per_year.earned_leave - leave_balance.earned_leave_taken,
            },
            'half_pay_leave': {
                'allotted': leave_per_year.half_pay_leave,
                'taken': leave_balance.half_pay_leave_taken,
                'balance': leave_per_year.half_pay_leave - leave_balance.half_pay_leave_taken,
            },
            'maternity_leave': {
                'allotted': leave_per_year.maternity_leave,
                'taken': leave_balance.maternity_leave_taken,
                'balance': leave_per_year.maternity_leave - leave_balance.maternity_leave_taken,
            },
            'child_care_leave': {
                'allotted': leave_per_year.child_care_leave,
                'taken': leave_balance.child_care_leave_taken,
                'balance': leave_per_year.child_care_leave - leave_balance.child_care_leave_taken,
            },
            'paternity_leave': {
                'allotted': leave_per_year.paternity_leave,
                'taken': leave_balance.paternity_leave_taken,
                'balance': leave_per_year.paternity_leave - leave_balance.paternity_leave_taken,
            },
            'leave_encashment': {
                'allotted': leave_per_year.leave_encashment,
                'taken': leave_balance.leave_encashment_taken,
                'balance': leave_per_year.leave_encashment - leave_balance.leave_encashment_taken,
            }
        }
        #print("4")
        # Return the leave balance data
        return JsonResponse({'leave_balance': leave_data}, status=200)

    except ExtraInfo.DoesNotExist:
        return JsonResponse({'error': 'User details not found'}, status=404)
    except Exception as e:
        # Handle any unexpected errors
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)    
    


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def search_employees(request):
    """
    API endpoint to search for employees based on the given search query.
    Returns:
        - A JSON response containing the list of employees matching the search query.
    """
    user = request.user
   

    # Check if the user has HR access
    if not check_hr_access(request):
        return JsonResponse({'error': 'HR access required'}, status=403)

    try:
        search_text = request.GET.get("search_text", "").strip()

        if not search_text:
            return JsonResponse({"error": "Search text is required"}, status=400)

        users = User.objects.filter(username__icontains=search_text)
        user_list = []
    

        for user in users:
        
            # Fetch designations from HoldsDesignation model
            designations = HoldsDesignation.objects.filter(user=user)

            if not designations.exists():
                continue  # Skip users without designations

            for hd in designations:
                
                user_list.append({
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "designation": hd.designation.name,  # Assuming designation has a 'name' field
                })

        return JsonResponse({"employees": user_list}, status=200)

    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)
    

# get my form initials name, last_selected_role, and department, pfno

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_form_initials(request):
    """
    API endpoint to get the form initials for the authenticated user.
    Returns:
        - A JSON response containing the form initials for the authenticated user.
    """
    user = request.user

    # Check if the user is authenticated
    if not user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        # fecth employee
        employee = Employee.objects.filter(id=user)
        if not employee.exists():
            return JsonResponse({'error': 'Employee not found'}, status=404)
        employee = employee.first()
        # fetch extra info
        extra_info = ExtraInfo.objects.filter(user=user)
        if not extra_info.exists():
            return JsonResponse({'error': 'ExtraInfo not found'}, status=404)
        extra_info = extra_info.first()

        Empconfidential=EmpConfidentialDetails.objects.filter(empid=employee)
        if not Empconfidential.exists():
            return JsonResponse({'error': 'EmpConfidentialDetails not found'}, status=404)
        Empconfidential=Empconfidential.first()
        dpt=extra_info.department

        
        return JsonResponse({
             
            'name': user.first_name+" "+user.last_name,
            'last_selected_role': extra_info.last_selected_role,
            'pfno': Empconfidential.personal_file_number,
            'department': dpt.name if dpt else None,


        }, status=200)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)










@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def submit_leave_form(request):
    """
    API endpoint to submit a leave form for the authenticated user.
    """
    user = request.user

    if not user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        form_data = request.POST
        files = request.FILES

        # Validate required fields first
        required_fields = [
            'name', 'designation', 'pfno', 'department', 
            'leaveStartDate', 'leaveEndDate', 'purpose', 'forwardTo'
        ]
        missing_fields = [field for field in required_fields if not form_data.get(field)]
        if missing_fields:
            return JsonResponse(
                {'error': f'Missing required fields: {", ".join(missing_fields)}'},
                status=400
            )

        # Extract all form data
        data = {
            'name': form_data.get('name'),
            'designation': form_data.get('designation'),
            'pfno': form_data.get('pfno'),
            'submissionDate': form_data.get('date'),
            'department': form_data.get('department'),
            'leave_start_date': form_data.get('leaveStartDate'),
            'leave_end_date': form_data.get('leaveEndDate'),
            'purpose': form_data.get('purpose'),
            'casual_leave': int(form_data.get('casualLeave', 0)),
            'vacation_leave': int(form_data.get('vacationLeave', 0)),
            'earned_leave': int(form_data.get('earnedLeave', 0)),
            'commuted_leave': int(form_data.get('commutedLeave', 0)),
            'special_casual_leave': int(form_data.get('specialCasualLeave', 0)),
            'restricted_holiday': int(form_data.get('restrictedHoliday', 0)),
            'half_pay_leave': int(form_data.get('halfPayLeave', 0)),
            'maternity_leave': int(form_data.get('maternityLeave', 0)),
            'child_care_leave': int(form_data.get('childCareLeave', 0)),
            'paternity_leave': int(form_data.get('paternityLeave', 0)),
            'remarks': form_data.get('remarks', 'N/A'),
            'station_leave': form_data.get('stationLeave', 'false').lower() == 'true',
            'station_leave_start_date': form_data.get('stationLeaveStartDate'),
            'station_leave_end_date': form_data.get('stationLeaveEndDate'),
            'station_leave_address': form_data.get('stationLeaveAddress'),
            'academic_responsibility_id': form_data.get('academicResponsibility'),
            'academic_responsibility_designation': form_data.get('academicResponsibility_designation'),
            'administrative_responsibility_id': form_data.get('administrativeResponsibility'),
            'administrative_responsibility_designation': form_data.get('administrativeResponsibility_designation'),
            'first_received_by_id': form_data.get('forwardTo'),
            'first_received_designation': form_data.get('forwardTo_designation'),
            'attached_pdf': files.get('attached_pdf')
        }

        # Validate dates
        try:
            data['leave_start_date'] = datetime.strptime(data['leave_start_date'], "%Y-%m-%d").date()
            data['leave_end_date'] = datetime.strptime(data['leave_end_date'], '%Y-%m-%d').date()
            if data['leave_end_date'] < data['leave_start_date']:
                return JsonResponse(
                    {'error': 'Leave end date cannot be before start date'},
                    status=400
                )
        except ValueError:
            return JsonResponse(
                {'error': 'Invalid leave date format. Use YYYY-MM-DD'},
                status=400
            )

        # Validate station leave
        if data['station_leave']:
            if not all([data['station_leave_start_date'], data['station_leave_end_date'], data['station_leave_address']]):
                return JsonResponse(
                    {'error': 'Station leave details are required when station leave is checked'},
                    status=400
                )
            try:
                data['station_leave_start_date'] = datetime.strptime(data['station_leave_start_date'], '%Y-%m-%d').date()
                data['station_leave_end_date'] = datetime.strptime(data['station_leave_end_date'], '%Y-%m-%d').date()
                if data['station_leave_end_date'] < data['station_leave_start_date']:
                    return JsonResponse(
                        {'error': 'Station leave end date cannot be before start date'},
                        status=400
                    )
            except ValueError:
                return JsonResponse(
                    {'error': 'Invalid station leave date format. Use YYYY-MM-DD'},
                    status=400
                )
        else:
            data['station_leave_start_date'] = None
            data['station_leave_end_date'] = None
            data['station_leave_address'] = None

        # Get employee
        try:
            employee = Employee.objects.get(id=user.id)
        except Employee.DoesNotExist:
            return JsonResponse({'error': 'Employee not found'}, status=404)

        # Handle academic responsibility (optional)
        academic_responsibility = None
        if data['academic_responsibility_id']:
            try:
                academic_responsibility = {
                    'user': Employee.objects.get(id=data['academic_responsibility_id']),
                    'designation': Designation.objects.get(name=data['academic_responsibility_designation'])
                }
            except (Employee.DoesNotExist, Designation.DoesNotExist):
                return JsonResponse(
                    {'error': 'Academic Responsibility user or designation not found'},
                    status=404
                )

        # Handle administrative responsibility (optional)
        administrative_responsibility = None
        if data['administrative_responsibility_id']:
            try:
                administrative_responsibility = {
                    'user': Employee.objects.get(id=data['administrative_responsibility_id']),
                    'designation': Designation.objects.get(name=data['administrative_responsibility_designation'])
                }
            except (Employee.DoesNotExist, Designation.DoesNotExist):
                return JsonResponse(
                    {'error': 'Administrative Responsibility user or designation not found'},
                    status=404
                )

        # Get first received by (required)
        try:
            first_received_by = {
                'user': Employee.objects.get(id=data['first_received_by_id']),
                'designation': Designation.objects.get(name=data['first_received_designation'])
            }
        except (Employee.DoesNotExist, Designation.DoesNotExist):
            return JsonResponse(
                {'error': 'First Received By user or designation not found'},
                status=404
            )

        # Handle PDF attachment
        pdf_data = None
        if data['attached_pdf']:
            pdf_data = {
                'binary': data['attached_pdf'].read(),
                'name': data['attached_pdf'].name
            }

        # Create leave form first (without file_id)
        leave_form = LeaveForm(
            employee=employee,
            name=data['name'],
            designation=data['designation'],
            personalfileNo=data['pfno'],
            submissionDate=data['submissionDate'],
            departmentInfo=data['department'],
            leaveStartDate=data['leave_start_date'],
            leaveEndDate=data['leave_end_date'],
            Purpose_of_leave=data['purpose'],
            Noof_CasualLeave=data['casual_leave'],
            Noof_vacationLeave=data['vacation_leave'],
            Noof_earnedLeave=data['earned_leave'],
            Noof_commutedLeave=data['commuted_leave'],
            Noof_specialCasualLeave=data['special_casual_leave'],
            Noof_restrictedHoliday=data['restricted_holiday'],
            Noof_halfPayLeave=data['half_pay_leave'],
            Noof_maternityLeave=data['maternity_leave'],
            Noof_childCareLeave=data['child_care_leave'],
            Noof_paternityLeave=data['paternity_leave'],
            Remarks=data['remarks'],
            LeavingStation=data['station_leave'],
            StationLeave_startdate=data['station_leave_start_date'],
            StationLeave_enddate=data['station_leave_end_date'],
            Address_During_StationLeave=data['station_leave_address'],
            AcademicResponsibility_user=academic_responsibility['user'] if academic_responsibility else None,
            AcademicResponsibility_designation=academic_responsibility['designation'] if academic_responsibility else None,
            AcademicResponsibility_status='Pending' if academic_responsibility else 'Accepted',
            AdministrativeResponsibility_user=administrative_responsibility['user'] if administrative_responsibility else None,
            AdministrativeResponsibility_designation=administrative_responsibility['designation'] if administrative_responsibility else None,
            AdministrativeResponsibility_status='Pending' if administrative_responsibility else 'Accepted',
            first_recieved_by=first_received_by['user'],
            first_recieved_designation=first_received_by['designation'],
            status='Pending',
            attached_pdf=pdf_data['binary'] if pdf_data else None,
            attached_pdf_name=pdf_data['name'] if pdf_data else None,
            file_id=None  # Initialize as None, will be updated later
        )
        leave_form.save()

        # Create file tracking if no responsibilities assigned
        file_id = None
        if not academic_responsibility and not administrative_responsibility:
            try:
                file_id = create_file(
                    uploader=employee.id,
                    uploader_designation=data['designation'],
                    receiver=first_received_by['user'].id.username,
                    receiver_designation=first_received_by['designation'].name,
                    src_module="HR",
                    src_object_id=str(leave_form.id),
                    file_extra_JSON={"type": "Leave"},
                    attached_file=None
                )
                # Update the leave form with the file_id
                leave_form.file_id = file_id
                leave_form.save()
            except Exception as e:
                return JsonResponse(
                    {'error': f'Failed to create file tracking: {str(e)}'},
                    status=500
                )

        return JsonResponse(
            {
                'message': 'Leave form submitted successfully',
                'form_id': leave_form.id,
                'file_id': file_id
            },
            status=201
        )

    except ValidationError as e:
        return JsonResponse(
            {'error': f'Validation error: {str(e)}'},
            status=400
        )
    except Exception as e:
        return JsonResponse(
            {'error': f'An unexpected error occurred: {str(e)}'},
            status=500
        )

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_leave_requests(request):
    """
    API endpoint to get the leave requests for the authenticated user.
    """
    user = request.user

    if not user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        # Get the employee associated with the user
        employee = Employee.objects.filter(id=user)
        

        if not employee.exists():
            return JsonResponse({'error': 'Employee not found'}, status=404)
        employee = employee.first()
        query_date=request.GET.get('date')
        if not query_date:
            # set 1 year back date
            query_date = datetime.now().date() - timedelta(days=365)
        else:
            query_date = datetime.strptime(query_date, '%Y-%m-%d').date()
        # Get the leave forms for the employee
        leave_forms = LeaveForm.objects.filter(employee=employee, submissionDate__gte=query_date)

        # Prepare the response data
        leave_requests = []
        # send only id submissionDate, status, leaveStartDate, leaveEndDate,
        for form in leave_forms:
            leave_requests.append({
                'id': form.id,
                'name': form.name,
                'submissionDate': form.submissionDate,
                'status': form.status,
                'leaveStartDate': form.leaveStartDate,
                'leaveEndDate': form.leaveEndDate,
            })
        
        return JsonResponse({'leave_requests': leave_requests}, status=200)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)
    


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_leave_form_by_id(request, form_id):
    """
    API endpoint to get the leave form by ID.
    """
    user = request.user

    if not user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        # print("0")
        # Get the employee associated with the user
        
        

        # print("1")
        # Get the leave form by ID
        leave_form = LeaveForm.objects.filter(id=form_id)
        if not leave_form.exists():
            return JsonResponse({'error': 'Leave form not found'}, status=404)
        leave_form = leave_form.first()
        
        employee = leave_form.employee
        
        # get leave balance of employee
        leave_balance = LeaveBalance.objects.filter(empid=employee).first()
        if not leave_balance:
            return JsonResponse({'error': 'Leave balance not found'}, status=404)
        # get leave per year of employee
        leave_per_year = LeavePerYear.objects.filter(empid=employee).first()
        if not leave_per_year:
            return JsonResponse({'error': 'Leave per year not found'}, status=404)




        # print("2")
        academic_responsibility_employee=None
        academic_responsibility_user=None
        academic_responsibility_name=None
        academic_responsibility_designation=None
        if(leave_form.AcademicResponsibility_user):
            # Access the AcademicResponsibility_user (Employee object) only if is not null else set None
            academic_responsibility_employee = leave_form.AcademicResponsibility_user

            # Access the User object from the Employee object
            academic_responsibility_user = academic_responsibility_employee.id
            
            # access name of academic_responsibility_user
            academic_responsibility_name = academic_responsibility_user.first_name + " " + academic_responsibility_user.last_name
            #print(academic_responsibility_name)

            # Access designations of academic_responsibility_user
            academic_responsibility_designation = leave_form.AcademicResponsibility_designation.name
        
        # print("hi")

        administrative_responsibility_employee=None
        administrative_responsibility_user=None
        administrative_responsibility_name=None
        administrative_responsibility_designation=None,
        if(leave_form.AdministrativeResponsibility_user):
            # Access the AdministrativeResponsibility_user (Employee object)
            administrative_responsibility_employee = leave_form.AdministrativeResponsibility_user

            # Access the User object from the Employee object
            administrative_responsibility_user = administrative_responsibility_employee.id

            # access name of administrative_responsibility_user
            administrative_responsibility_name = administrative_responsibility_user.first_name + " " + administrative_responsibility_user.last_name

            # Access designations of administrative_responsibility_user
            administrative_responsibility_designation = leave_form.AdministrativeResponsibility_designation.name
        
        # print("hi2")

        # Access the first_recieved_by (Employee object)
        first_recieved_by_employee = leave_form.first_recieved_by
        first_recieved_by_user=None
        first_recieved_by_name=None
        first_recieved_by_designation=None

        if(leave_form.first_recieved_by):
             
            first_recieved_by_user = first_recieved_by_employee.id


            # access name of first_recieved_by_user
            first_recieved_by_name = first_recieved_by_user.first_name + " " + first_recieved_by_user.last_name

            # Access designations of first_recieved_by_user
            first_recieved_by_designation = leave_form.first_recieved_designation.name

        

        # print("2.5")


        # attcahed file name only
        attached_pdf_name = None
        if leave_form.attached_pdf:
            attached_pdf_name = leave_form.attached_pdf_name
        
    #     #  if status is accepeted send aproved date and and approve by and approved by designationapprovedDate = models.DateField(auto_now_add=True, null=True)
    # approved_by = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, related_name='leave_approved_by')
    # approved_by_designation=models.ForeignKey(Designation, on_delete=models.CASCADE, null=True, related_name='leave_approved_by_designation')

        if (leave_form.status=='Accepetd' and leave_form.approved_by):
            approved_by_employee = leave_form.approved_by
            approved_by_user = approved_by_employee.id
            approved_by_name = approved_by_user.first_name + " " + approved_by_user.last_name
            approved_by_designation = leave_form.approved_by_designation.name
            approved_date = leave_form.approvedDate
        else:
            approved_by_name = None
            approved_by_designation = None
            approved_date = None 

        # print("z")
        leave_form_data = {
            'id': leave_form.id,
            'name': leave_form.name,
            'designation': leave_form.designation,
            'pfno': leave_form.personalfileNo,
            'submissionDate': leave_form.submissionDate,
            'department': leave_form.departmentInfo,
            'leaveStartDate': leave_form.leaveStartDate,
            'leaveEndDate': leave_form.leaveEndDate,
            'purpose': leave_form.Purpose_of_leave,
            'casualLeave': leave_form.Noof_CasualLeave,
            'vacationLeave': leave_form.Noof_vacationLeave,
            'earnedLeave': leave_form.Noof_earnedLeave,
            'commutedLeave': leave_form.Noof_commutedLeave,
            'specialCasualLeave': leave_form.Noof_specialCasualLeave,
            'restrictedHoliday': leave_form.Noof_restrictedHoliday,
            'maternityLeave':leave_form.Noof_maternityLeave,
            'childCareLeave':leave_form.Noof_childCareLeave,
            'paternityLeave':leave_form.Noof_paternityLeave,
            'halfPayLeave':leave_form.Noof_halfPayLeave,
            'casualLeaveBalance':leave_per_year.casual_leave - leave_balance.casual_leave_taken,
            'special_casual_leaveBalance':leave_per_year.special_casual_leave - leave_balance.special_casual_leave_taken,
            'earned_leaveBalance':leave_per_year.earned_leave - leave_balance.earned_leave_taken,
            'half_pay_leaveBalance':leave_per_year.half_pay_leave - leave_balance.half_pay_leave_taken,
            'maternity_leaveBalance':leave_per_year.maternity_leave - leave_balance.maternity_leave_taken,
            'child_care_leaveBalance':leave_per_year.child_care_leave - leave_balance.child_care_leave_taken,
            'paternity_leaveBalance':leave_per_year.paternity_leave - leave_balance.paternity_leave_taken,
            'remarks': leave_form.Remarks,
            'stationLeave': leave_form.LeavingStation,
            'stationLeaveStartDate': leave_form.StationLeave_startdate,
            'stationLeaveEndDate': leave_form.StationLeave_enddate,
            'stationLeaveAddress': leave_form.Address_During_StationLeave,
            'academicResponsibility': academic_responsibility_name,
            'academicResponsibilityDesignation': academic_responsibility_designation,
            'academicResponsibilityStatus': leave_form.AcademicResponsibility_status,
            'administrativeResponsibility': administrative_responsibility_name,
            'administrativeResponsibilityDesignation': administrative_responsibility_designation,
            'administrativeResponsibilityStatus': leave_form.AdministrativeResponsibility_status,
            'firstRecievedBy': first_recieved_by_name,
            'firstRecievedByDesignation': first_recieved_by_designation,
            'status': leave_form.status,
            'attachedPdfName': attached_pdf_name,
            'approvedBy': approved_by_name,
            'approvedByDesignation': approved_by_designation,
            'approvedDate': approved_date,
            'file_id': leave_form.file_id,
            'application_type': leave_form.application_type,
        }
        # #print("3") 
        # #print(leave_form_data)
        return JsonResponse({'leave_form': leave_form_data}, status=200)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)
    
    

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def handle_leave_academic_responsibility(request, form_id):
    """
    API endpoint to handle the academic responsibility of a leave form.
    """
    user = request.user
    #print("0")
    if not user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        
        # get employee of user
        employee = Employee.objects.filter(id=user)
        if not employee.exists():
            return JsonResponse({'error': 'Employee not found'}, status=404)
        
        
        # get last selected role of user
        extra_info = ExtraInfo.objects.filter(user=user)
        if not extra_info.exists():
            return JsonResponse({'error': 'ExtraInfo not found'}, status=404)
        extra_info = extra_info.first()

        last_selected_role = extra_info.last_selected_role
        if not last_selected_role:
            
            designations = HoldsDesignation.objects.filter(user=user)
            if designations.exists():
                last_selected_role = designations.last().designation.name
                print(last_selected_role)
                extra_info.last_selected_role = last_selected_role
                extra_info.save()
                last_selected_role=extra_info.last_selected_role
            else:
                return JsonResponse({'error': 'Designation not found'}, status=404)

        # get leave form by id
        leave_form = LeaveForm.objects.filter(id=form_id)

        # check if leave form exists
        if not leave_form.exists():
            return JsonResponse({'error': 'Leave form not found'}, status=404)
        
        leave_form = leave_form.first()

        # check if user has access to handle academic responsibility
        

        if user != leave_form.AcademicResponsibility_user.id:
            return JsonResponse({'error': 'You do not have access to handle academic responsibility for this leave form'}, status=403)
        #print("2")
        #get designation of academic responsibility user
        academic_responsibility_designation = leave_form.AcademicResponsibility_designation

        # check if user has access to handle academic responsibility
        if last_selected_role!=academic_responsibility_designation.name:
            return JsonResponse({'error': 'You do not have access to handle academic responsibility for this leave form'}, status=403)
        
        # get action
        data = json.loads(request.body)
        action = data.get('action')
        #print(action)
        # check if action is valid
        if action not in ['accept', 'reject']:
            return JsonResponse({'error': 'Invalid action'}, status=400)
        
        # handle reject
        if action == 'reject':
            leave_form.AcademicResponsibility_status = 'Rejected'
            leave_form.status = 'Rejected'
            leave_form.save()
            return JsonResponse({'message': 'Academic responsibility rejected successfully'}, status=200)
        
        # handle accept
        leave_form.AcademicResponsibility_status = 'Accepted'
        # check if administrative responsibility is pending or rejected
        if leave_form.AdministrativeResponsibility_status == 'Pending' or leave_form.AdministrativeResponsibility_status == 'Rejected':
            leave_form.save()
            return JsonResponse({'message': 'Academic responsibility accepted successfully'}, status=200)
        
        # check if administrative responsibility is accepted
        if leave_form.AdministrativeResponsibility_status == 'Accepted':
            uploader_employee = leave_form.employee
            # get user of uploader employee
            uploader = uploader_employee.id
            uploader_designation=leave_form.designation

            first_recieved_by_employee = leave_form.first_recieved_by
            first_recieved_by_user = first_recieved_by_employee.id
            # get username of first_recieved_by_user
            receiver = first_recieved_by_user.username
            # get designation of first recieved by user
            receiver_designation = leave_form.first_recieved_designation
            src_module = "HR"
            src_object_id = str(leave_form.id)
            file_extra_JSON = {"type": "Leave"}

            file_id = create_file(
                uploader=uploader,
                uploader_designation=uploader_designation,
                receiver=receiver,
                receiver_designation=receiver_designation,
                src_module=src_module,
                src_object_id=src_object_id,
                file_extra_JSON=file_extra_JSON,
                attached_file=None  # Attach any file if necessary
            )
            leave_form.file_id = file_id
            leave_form.save()
            return JsonResponse({'message': 'Academic responsibility accepted successfully'}, status=200)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)
    



@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def handle_leave_administrative_responsibility(request, form_id):
    """
    API endpoint to handle the administrative responsibility of a leave form.
    """
    user = request.user

    if not user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        # get employee of user
        employee = Employee.objects.filter(id=user)
        if not employee.exists():
            return JsonResponse({'error': 'Employee not found'}, status=404)
        
        # get last selected role of user
        extra_info = ExtraInfo.objects.filter(user=user)
        if not extra_info.exists():
            return JsonResponse({'error': 'ExtraInfo not found'}, status=404)
        extra_info = extra_info.first()

        last_selected_role = extra_info.last_selected_role
        if not last_selected_role:
            
            designations = HoldsDesignation.objects.filter(user=user)
            if designations.exists():
                last_selected_role = designations.last().designation.name
                print(last_selected_role)
                extra_info.last_selected_role = last_selected_role
                extra_info.save()
                last_selected_role=extra_info.last_selected_role
            else:
                return JsonResponse({'error': 'Designation not found'}, status=404)

        # get leave form by id
        leave_form = LeaveForm.objects.filter(id=form_id)

        # check if leave form exists
        if not leave_form.exists():
            return JsonResponse({'error': 'Leave form not found'}, status=404)
        
        leave_form = leave_form.first()

        # check if user has access to handle administrative responsibility
        if user != leave_form.AdministrativeResponsibility_user.id:
            return JsonResponse({'error': 'You do not have access to handle administrative responsibility for this leave form'}, status=403)
        #get designation of administrative responsibility user
        administrative_responsibility_designation = leave_form.AdministrativeResponsibility_designation

        # check if user has access to handle administrative responsibility
        if last_selected_role!=administrative_responsibility_designation.name:
            return JsonResponse({'error': 'You do not have access to handle administrative responsibility for this leave form'}, status=403)
        
        # get action
        data = json.loads(request.body)
        action = data.get('action')
        #print(action)

        # check if action is valid
        if action not in ['accept', 'reject']:
            return JsonResponse({'error': 'Invalid action'}, status=400)
        
        # handle reject
        if action == 'reject':
            leave_form.AdministrativeResponsibility_status = 'Rejected'
            leave_form.status = 'Rejected'
            leave_form.save()
            return JsonResponse({'message': 'Administrative responsibility rejected successfully'}, status=200)
        
        # handle accept
        leave_form.AdministrativeResponsibility_status = 'Accepted'
        # check if academic responsibility is pending or rejected
        if leave_form.AcademicResponsibility_status == 'Pending' or leave_form.AcademicResponsibility_status == 'Rejected':
            leave_form.save()
            return JsonResponse({'message': 'Administrative responsibility accepted successfully'}, status=200)

        
        # check if academic responsibility is accepted
        if leave_form.AcademicResponsibility_status == 'Accepted':
            uploader_employee = leave_form.employee
            # get user of uploader employee
            uploader = uploader_employee.id
            uploader_designation=leave_form.designation
            
            first_recieved_by_employee = leave_form.first_recieved_by
            first_recieved_by_user = first_recieved_by_employee.id
            
            # get username of first_recieved_by_user
            receiver = first_recieved_by_user.username
            # get designation of first recieved by user
            
            receiver_designation = leave_form.first_recieved_designation 
            
            src_module = "HR"
            src_object_id = str(leave_form.id)
            file_extra_JSON = {"type": "Leave"}
            
            file_id = create_file(
                uploader=uploader,
                uploader_designation=uploader_designation,
                receiver=receiver,
                receiver_designation=receiver_designation,
                src_module=src_module,
                src_object_id=src_object_id,
                file_extra_JSON=file_extra_JSON,
                attached_file=None  # Attach any file if necessary
            )
            #print(file_id)
            leave_form.file_id = file_id
            
            leave_form.save()
            return JsonResponse({'message': 'Administrative responsibility accepted successfully'}, status=200)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


# def get_leave_inbox get leave forms where acdemic responsibility or administrative responsibility

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_leave_inbox(request):
    """
    API endpoint to get the leave inbox for the authenticated user.
    """
    user = request.user

    if not user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        # Get the employee associated with the user
        employee = Employee.objects.filter(id=user)
        if not employee.exists():
            return JsonResponse({'error': 'Employee not found'}, status=404)
        employee = employee.first()
        # get last selected role of user
        query_date=request.GET.get('date')
        
        # if date in not set date is 1 year back
        if not query_date:
            # set 1 year back date
            query_date = datetime.now().date() - timedelta(days=365)
        else:
            query_date = datetime.strptime(query_date, '%Y-%m-%d').date()
        extra_info = ExtraInfo.objects.filter(user=user)
        if not extra_info.exists():
            return JsonResponse({'error': 'ExtraInfo not found'}, status=404)
        extra_info = extra_info.first()

        last_selected_role = extra_info.last_selected_role
        
        # print(type(last_selected_role))

        # if last selected role is none then set it to employee designation

        if not last_selected_role:
            
            designations = HoldsDesignation.objects.filter(user=user)
            if designations.exists():
                last_selected_role = designations.last().designation.name
                print(last_selected_role)
                extra_info.last_selected_role = last_selected_role
                extra_info.save()
                last_selected_role=extra_info.last_selected_role
            else:
                return JsonResponse({'error': 'Designation not found'}, status=404)

        

        # print(1)
        # get academic responsibility forms till query date
        academic_responsibility_forms = LeaveForm.objects.filter(AcademicResponsibility_user=employee, submissionDate__gte=query_date)
        # filter by last selected role
        # print(2)
        academic_responsibility_forms = [form for form in academic_responsibility_forms if form.AcademicResponsibility_designation.name == last_selected_role]

        # get administrative responsibility forms
        administrative_responsibility_forms = LeaveForm.objects.filter(AdministrativeResponsibility_user=employee, submissionDate__gte=query_date)
        # filter by last selected role
        administrative_responsibility_forms = [form for form in administrative_responsibility_forms if form.AdministrativeResponsibility_designation.name == last_selected_role]

        # Prepare the academic res response data
        academic_res_inbox = []
        # send only id submissionDate, status, leaveStartDate, leaveEndDate,
        for form in academic_responsibility_forms:
            academic_res_inbox.append({
                'id': form.id,
                'name': form.name,
                'designation': form.designation,
                'submissionDate': form.submissionDate,
                'status': form.AcademicResponsibility_status,
                'leaveStartDate': form.leaveStartDate,
                'leaveEndDate': form.leaveEndDate,
            })
        
        # Prepare the administrative res response data
        administrative_res_inbox = []
        # send only id submissionDate, status, leaveStartDate, leaveEndDate,
        for form in administrative_responsibility_forms:
            administrative_res_inbox.append({
                'id': form.id,
                'name': form.name,
                'designation': form.designation,
                'submissionDate': form.submissionDate,
                'status': form.AdministrativeResponsibility_status,
                'leaveStartDate': form.leaveStartDate,
                'leaveEndDate': form.leaveEndDate,
            })

        

        # get leave file 
        user_id = ExtraInfo.objects.get(user=user).user_id
        ext= ExtraInfo.objects.get(user__id=user_id)
        username = ext.user
        designation = ext.last_selected_role
        if not last_selected_role:
            
            designations = HoldsDesignation.objects.filter(user=user)
            if designations.exists():
                last_selected_role = designations.last().designation.name
                print(last_selected_role)
                ext.last_selected_role = last_selected_role
                ext.save()
                ext=extra_info.last_selected_role
            else:
                return JsonResponse({'error': 'Designation not found'}, status=404)
        reciever_designation = None
        if designation:
            reciever_designation = designation
        #print("9")
        #print(username,designation)
        
        inbox = view_inbox(username=str(username), designation=reciever_designation, src_module="HR")
        #print("inbox",inbox)
        
        # type== leave and upload_date> query date
        filtered_inbox = [
            i for i in inbox
            if i['file_extra_JSON']['type'] == "Leave" and
            datetime.strptime(i['upload_date'], "%Y-%m-%dT%H:%M:%S.%f").date() >= query_date ]

        # in fileterd_inbox  get designation name by designatetion id and fetch status of each leave form by src_object_id
        #print("x")
        for i in filtered_inbox:
            if i['designation']:
                designation = Designation.objects.get(id=i['designation'])
                i['designation'] = designation.name
                #print(i['designation'])
            src_object_id = i['src_object_id']
            leave_form = LeaveForm.objects.get(id=src_object_id)
            i['status'] = leave_form.status
        
        #print("10")
        

        return JsonResponse({
            'leave_inbox': filtered_inbox,
            'academic_res_inbox': academic_res_inbox,
            'administrative_res_inbox': administrative_res_inbox
        }, status=200)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

# download attached pdf for leave form

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def download_leave_form_pdf(request, form_id):
    """
    API endpoint to download the attached PDF for a leave form.
    """
    user = request.user

    if not user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        # Get the leave form by ID
        leave_form = LeaveForm.objects.filter(id=form_id)
        if not leave_form.exists():
            return JsonResponse({'error': 'Leave form not found'}, status=404)
        leave_form = leave_form.first()



        # Check if the leave form has an attached PDF
        if not leave_form.attached_pdf:
            return JsonResponse({'error': 'No attached PDF found for this leave form'}, status=404)

        # convert binary to file
        attached_pdf = leave_form.attached_pdf
        attached_pdf_name = leave_form.attached_pdf_name
        response = HttpResponse(attached_pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{attached_pdf_name}"'
        return response
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)
    

# {'file_history': [OrderedDict([('id', 490), ('receive_date', '2025-03-11T16:53:15.057424'), ('forward_date', '2025-03-11T16:53:15.057424'), ('remarks', 'File with id:635 created by vkjain and sent to vkjain'), ('upload_file', None), ('is_read', False), ('tracking_extra_JSON', {'type': 'Leave'}), ('file_id', 635), ('current_id', 'vkjain'), ('current_design', 4354), ('receiver_id', 5350), ('receive_design', 15)])]}

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def track_file_react(request, id):
    # Fetching the file history as a list of dictionaries
    user=request.user
    file_history = view_history(file_id=id)
    #print(user.id)
    # Create a JSON response for React
    response_data = {
        'file_history': file_history
    }
    # for each designation id get designation name
    for i in response_data['file_history']:
        
        

        if i['receiver_id']:
            user = User.objects.get(id=i['receiver_id'])
            if user:
                i['receiver_id'] = user.first_name + " " + user.last_name 
        if i['receive_design']:
            designation = Designation.objects.get(id=i['receive_design'])
            if designation:
                i['receive_design'] = designation.name

    
    return JsonResponse(response_data)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def handle_leave_file(request, form_id):
    user=request.user
    data = json.loads(request.body)
    action = data.get('action')
    remarks = data.get('fileRemarks')
    forwardtouser=data.get('forwardTo')
    forwardToDesignation=data.get('forwardToDesignation')
    
    
    if not user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    try:
        # get employee of user
        employee = Employee.objects.filter(id=user)
        if not employee.exists():
            return JsonResponse({'error': 'Employee not found'}, status=404)
        
        # get last selected role of user
        extra_info = ExtraInfo.objects.filter(user=user)
        if not extra_info.exists():
            return JsonResponse({'error': 'ExtraInfo not found'}, status=404)
        extra_info = extra_info.first()

        last_selected_role = extra_info.last_selected_role
        if not last_selected_role:
            
            designations = HoldsDesignation.objects.filter(user=user)
            if designations.exists():
                last_selected_role = designations.last().designation.name
                print(last_selected_role)
                extra_info.last_selected_role = last_selected_role
                extra_info.save()
                last_selected_role=extra_info.last_selected_role
            else:
                return JsonResponse({'error': 'Designation not found'}, status=404)

        # get leave form by form id
        leave_form = LeaveForm.objects.filter(id=form_id)
        if not leave_form.exists():
            return JsonResponse({'error': 'Leave form not found'}, status=404)
        
        file_id=leave_form.first().file_id

       
        current_owner = get_current_file_owner(file_id)
        current_owner_designation=get_current_file_owner_designation(file_id)

        
        #print(current_owner)
        #print(current_owner_designation)
        # match user's username with current owner
        

        if user.username != current_owner.username:
            return JsonResponse({'error': 'You do not have access to handle this file'}, status=403)
        
        if last_selected_role != current_owner_designation.name:
            return JsonResponse({'error': 'You do not have access to handle this file'}, status=403)
        # get action
        if action not in ['forward', 'reject', 'accept']:
            return JsonResponse({'error': 'Invalid action'}, status=400)
        
        if action == 'reject':
            # reject the file
            remarks = f"Rejected by {current_owner} with remarks: {remarks}"
            # get uploader of form
            uploader_employee = leave_form.first().employee
            uploader = uploader_employee.id
            uploader_designation=leave_form.first().designation
            #print(uploader)
            #print(uploader_designation)
            
            track_id = forward_file(
                file_id=file_id,
                receiver=uploader,
                receiver_designation=uploader_designation,
                remarks=remarks,
                file_extra_JSON=None
            )
            # change status of leave form
            #print(leave_form.first().status)
            leave_instance = leave_form.first()
            leave_instance.status = 'Rejected'
            leave_instance.save()
            return JsonResponse({'message': 'File rejected successfully'}, status=200)
        
        if action =='forward':
            # forward the file
            remarks = f"Forwarded by {current_owner} with remarks: {remarks}"
            # get forward to user
            
            #print(forwardtouser)
            # get username with user id
            forwardtouser = User.objects.get(id=forwardtouser).username
           
            
            forward_to_designation = Designation.objects.get(name=forwardToDesignation)
            track_id = forward_file(
                file_id=file_id,
                receiver=forwardtouser,
                receiver_designation=forward_to_designation,
                remarks=remarks,
                file_extra_JSON=None
            )
            return JsonResponse({'message': 'File forwarded successfully'}, status=200)
        
        if action == 'accept':
            # accept the file
            remarks = f"Accepted by {current_owner} with remarks: {remarks}"
            
            # get employee of leave form
            leave_instance = leave_form.first()
            leave_instance.status = 'Accepted'
            approvedDate = datetime.now().date()
            approved_by_employee = Employee.objects.get(id=user)
            # get approved_by_designation
            approved_by_designation = Designation.objects.get(name=last_selected_role)
            leave_instance.approved_by = approved_by_employee
            leave_instance.approved_by_designation = approved_by_designation
            leave_instance.approvedDate = approvedDate
           
            uploader_employee = leave_instance.employee
            # get leave balance of employee
            leave_balance = LeaveBalance.objects.filter(empid=uploader_employee).first()
            if not leave_balance:
                return JsonResponse({'error': 'Leave balance not found'}, status=404)
            # update the leave taken in leave balance
            #print("hi  1 ")
            
            leave_balance.casual_leave_taken += leave_instance.Noof_CasualLeave
            leave_balance.special_casual_leave_taken += leave_instance.Noof_specialCasualLeave
            leave_balance.earned_leave_taken += (leave_instance.Noof_earnedLeave+2*leave_instance.Noof_vacationLeave)
            leave_balance.half_pay_leave_taken += (leave_instance.Noof_halfPayLeave +2*leave_instance.Noof_commutedLeave)
            leave_balance.maternity_leave_taken += leave_instance.Noof_maternityLeave
            leave_balance.child_care_leave_taken += leave_instance.Noof_childCareLeave
            leave_balance.paternity_leave_taken += leave_instance.Noof_paternityLeave
            leave_balance.restricted_holiday_taken += leave_instance.Noof_restrictedHoliday
            



            
            # return JsonResponse({'message': 'File accepted successfully'}, status=200)
            # verify leave form save
            leave_balance.save()
            #print(leave_balance.casual_leave_taken)
            leave_instance.save() 
            track_id = forward_file(
                file_id=file_id,
                receiver=current_owner,
                receiver_designation=current_owner_designation,
                remarks=remarks,
                file_extra_JSON=None
            )
            return JsonResponse({'message': 'File accepted successfully'}, status=200)

        return JsonResponse({'error': 'Invalid action'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)






@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def admin_get_leave_balance(request, empid):
    try:
        user = request.user

        # Validate user authentication
        if not user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)

        # Get the user's last selected role
        extra_info = ExtraInfo.objects.filter(user=user)
        if not extra_info.exists():
            return JsonResponse({'error': 'ExtraInfo not found'}, status=404)
        extra_info = extra_info.first()

        
        
        if extra_info.last_selected_role != 'SectionHead_HR':
            return JsonResponse({'error': 'You do not have access to get leave balance'}, status=403)

        
        # Fetch the employee data based on empid
        try:
            emp_user = User.objects.get(id=empid)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        
        try:
            employee = Employee.objects.get(id=emp_user)
        except Employee.DoesNotExist:
            return JsonResponse({'error': 'Employee not found'}, status=404)
        
        # Retrieve leave balance and leave per year for the employee
        try:
            leave_balance = LeaveBalance.objects.get(empid=employee)
        except LeaveBalance.DoesNotExist:
            return JsonResponse({'error': 'Leave balance not found'}, status=404)
        
        try:
            leave_per_year = LeavePerYear.objects.get(empid=employee)
        except LeavePerYear.DoesNotExist:
            return JsonResponse({'error': 'Leave per year not found'}, status=404)

        
        # Prepare leave balance data
        leave_balance_data = {
            'casual_leave_allotted': leave_per_year.casual_leave,
            'casual_leave_taken': leave_balance.casual_leave_taken,
            
            'earned_leave_allotted': leave_per_year.earned_leave,
            'earned_leave_taken': leave_balance.earned_leave_taken,
            
            'special_casual_leave_allotted': leave_per_year.special_casual_leave,
            'special_casual_leave_taken': leave_balance.special_casual_leave_taken,
            'restricted_holiday_allotted': leave_per_year.restricted_holiday,
            'restricted_holiday_taken': leave_balance.restricted_holiday_taken,

            'half_pay_leave_allotted': leave_per_year.half_pay_leave,
            'half_pay_leave_taken': leave_balance.half_pay_leave_taken,

            'maternity_leave_allotted': leave_per_year.maternity_leave,
            'maternity_leave_taken': leave_balance.maternity_leave_taken,

            'child_care_leave_allotted': leave_per_year.child_care_leave,
            'child_care_leave_taken': leave_balance.child_care_leave_taken,

            'paternity_leave_allotted': leave_per_year.paternity_leave,
            'paternity_leave_taken': leave_balance.paternity_leave_taken,

            'leave_encashment_allotted': leave_per_year.leave_encashment,
            'leave_encashment_taken': leave_balance.leave_encashment_taken,
            
        }

        return JsonResponse({'leave_balance': leave_balance_data}, status=200)
    except Exception as e:
        # Log the error message (consider using logging here for production)
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)



# create a function to get department of employee
def get_department(emp):
    department = None
    # get userid then get extrainfo then get department
    user_id = emp.id
    ext= ExtraInfo.objects.get(user__id=user_id)
    department = ext.department
    return department







# @api_view(['GET'])
# @authentication_classes([TokenAuthentication])
# @permission_classes([IsAuthenticated])
# def admin_get_all_leave_balances(request):
#     try:
#         user = request.user

#         if not user.is_authenticated:
#             return JsonResponse({'error': 'Authentication required'}, status=401)

#         # Get the user's ExtraInfo record
#         extra_info = ExtraInfo.objects.filter(user=user).first()
#         if not extra_info:
#             return JsonResponse({'error': 'ExtraInfo not found'}, status=404)

#         # Validate the HR role
#         if extra_info.last_selected_role != 'SectionHead_HR':
#             return JsonResponse({'error': 'You do not have access to get leave balance'}, status=403)

#         # Accumulate leave balance data for all employees
#         employee_leave_list = []
#         employees = Employee.objects.all()  # Adjust this query if HR should only access certain employees

#         for employee in employees:
#             # Since the 'id' field in Employee is a OneToOneField with User, use it to extract user info
#             employee_data = {
#                 'employee_id': employee.id.pk,  # primary key of the related User
#                 'employee_username': employee.id.username,
#                 'employee_fullname': employee.id.get_full_name(),  # if defined; otherwise, adjust as needed
#             }

#             # Fetch related leave data based on employee instance
#             leave_balance = LeaveBalance.objects.filter(empid=employee).first()
#             leave_per_year = LeavePerYear.objects.filter(empid=employee).first()

#             if not leave_balance or not leave_per_year:
#                 missing_fields = []
#                 if not leave_balance:
#                     missing_fields.append('LeaveBalance')
#                 if not leave_per_year:
#                     missing_fields.append('LeavePerYear')
#                 employee_data['error'] = f"Missing record(s): {', '.join(missing_fields)}."
#             else:
#                 employee_data.update({
#                     'casual_leave_allotted': leave_per_year.casual_leave_allotted,
#                     'casual_leave_taken': leave_balance.casual_leave_taken,
#                     'vacation_leave_allotted': leave_per_year.vacation_leave_allotted,
#                     'vacation_leave_taken': leave_balance.vacation_leave_taken,
#                     'earned_leave_allotted': leave_per_year.earned_leave_allotted,
#                     'earned_leave_taken': leave_balance.earned_leave_taken,
#                     'commuted_leave_allotted': leave_per_year.commuted_leave_allotted,
#                     'commuted_leave_taken': leave_balance.commuted_leave_taken,
#                     'special_casual_leave_allotted': leave_per_year.special_casual_leave_allotted,
#                     'special_casual_leave_taken': leave_balance.special_casual_leave_taken,
#                     'restricted_holiday_allotted': leave_per_year.restricted_holiday_allotted,
#                     'restricted_holiday_taken': leave_balance.restricted_holiday_taken,
#                 })

#             employee_leave_list.append(employee_data)

#         return JsonResponse({'leave_balances': employee_leave_list}, status=200)
    
#     except Exception as e:
#         logger.exception("Unexpected error in admin_get_all_leave_balances view")
#         return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)













@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def admin_get_all_leave_balances(request):
    try:
        user = request.user

        if not user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)

        # Get the user's ExtraInfo record
        extra_info = ExtraInfo.objects.filter(user=user).first()
        if not extra_info:
            return JsonResponse({'error': 'ExtraInfo not found'}, status=404)

        # Validate the HR role
        if extra_info.last_selected_role != 'SectionHead_HR':
            return JsonResponse({'error': 'You do not have access to get leave balance'}, status=403)

        # Accumulate leave balance data for all employees
        employee_leave_list = []
        employees = Employee.objects.all()  # Adjust this query if HR should only access certain employees

        for employee in employees:
            # Employee.id is a OneToOneField linking to the related User instance
            user_inst = employee.id

            # Fetch related ExtraInfo for department details (like in get_hr_employees)
            emp_extra_info = ExtraInfo.objects.filter(user=user_inst).first()
            department = emp_extra_info.department.name if emp_extra_info and emp_extra_info.department else None

            # Prepare base employee data including department
            employee_data = {
                'employee_id': user_inst.id,  # primary key of the User model
                'employee_username': user_inst.username,
                'employee_fullname': user_inst.get_full_name(),  # if defined; otherwise, adjust as needed
                'department': department,
            }

            # Fetch related leave data based on employee instance
            leave_balance = LeaveBalance.objects.filter(empid=employee).first()
            leave_per_year = LeavePerYear.objects.filter(empid=employee).first()

            if not leave_balance or not leave_per_year:
                missing_fields = []
                if not leave_balance:
                    missing_fields.append('LeaveBalance')
                if not leave_per_year: 
                    missing_fields.append('LeavePerYear')
                employee_data['error'] = f"Missing record(s): {', '.join(missing_fields)}."
            else:
                employee_data.update({
                    
                    'casual_leave_allotted': leave_per_year.casual_leave,
                    'casual_leave_taken': leave_balance.casual_leave_taken,
                    
                    'earned_leave_allotted': leave_per_year.earned_leave,
                    'earned_leave_taken': leave_balance.earned_leave_taken,
                    
                    'special_casual_leave_allotted': leave_per_year.special_casual_leave,
                    'special_casual_leave_taken': leave_balance.special_casual_leave_taken,
                    'restricted_holiday_allotted': leave_per_year.restricted_holiday,
                    'restricted_holiday_taken': leave_balance.restricted_holiday_taken,

                    'half_pay_leave_allotted': leave_per_year.half_pay_leave,
                    'half_pay_leave_taken': leave_balance.half_pay_leave_taken,

                    'maternity_leave_allotted': leave_per_year.maternity_leave,
                    'maternity_leave_taken': leave_balance.maternity_leave_taken,

                    'child_care_leave_allotted': leave_per_year.child_care_leave,
                    'child_care_leave_taken': leave_balance.child_care_leave_taken,

                    'paternity_leave_allotted': leave_per_year.paternity_leave,
                    'paternity_leave_taken': leave_balance.paternity_leave_taken,

                    'leave_encashment_allotted': leave_per_year.leave_encashment,
                    'leave_encashment_taken': leave_balance.leave_encashment_taken,
                    
                
                })

            employee_leave_list.append(employee_data)

        return JsonResponse({'leave_balances': employee_leave_list}, status=200)

    except Exception as e:
        logger.exception("Unexpected error in admin_get_all_leave_balances view")
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)





















@api_view(['PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def admin_update_leave_balance(request, empid):
    """
    Update leave balance and leave per year for a specified employee.
    The request JSON may include any of the following numeric fields:
    
    For LeaveBalance:
      - casual_leave_taken
      - vacation_leave_taken
      - earned_leave_taken
      - commuted_leave_taken
      - special_casual_leave_taken
      - restricted_holiday_taken
      
    For LeavePerYear:
      - casual_leave_allotted
      - vacation_leave_allotted
      - earned_leave_allotted
      - commuted_leave_allotted
      - special_casual_leave_allotted
      - restricted_holiday_allotted
      
    Only users with the "SectionHead_HR" role can perform this update.
    """
    try:
        user = request.user

        # Validate user authentication (redundant if using IsAuthenticated but explicit check adds clarity)
        if not user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)

        # Get the user's ExtraInfo record to verify role
        extra_info_qs = ExtraInfo.objects.filter(user=user)
        if not extra_info_qs.exists():
            return JsonResponse({'error': 'ExtraInfo not found'}, status=404)
        extra_info = extra_info_qs.first()

        # Permission check based on last selected role
        if extra_info.last_selected_role != 'SectionHead_HR':
            return JsonResponse({'error': 'You do not have access to update leave balances'}, status=403)

        # Fetch the employee using the provided empid
        try:
            emp_user = User.objects.get(id=empid)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

        try:
            employee = Employee.objects.get(id=emp_user)
        except Employee.DoesNotExist:
            return JsonResponse({'error': 'Employee not found'}, status=404)

        # Retrieve existing records for leave balance and leave per year for the employee
        try:
            leave_balance = LeaveBalance.objects.get(empid=employee)
        except LeaveBalance.DoesNotExist:
            return JsonResponse({'error': 'Leave balance not found'}, status=404)

        try:
            leave_per_year = LeavePerYear.objects.get(empid=employee)
        except LeavePerYear.DoesNotExist:
            return JsonResponse({'error': 'Leave per year record not found'}, status=404)

        # Define the fields for each model that can be updated.
        leave_balance_fields = [
            'casual_leave_taken',
            'vacation_leave_taken',
            'earned_leave_taken',
            'commuted_leave_taken',
            'special_casual_leave_taken',
            'restricted_holiday_taken'
        ]

        leave_per_year_fields = [
            'casual_leave_allotted',
            'vacation_leave_allotted',
            'earned_leave_allotted',
            'commuted_leave_allotted',
            'special_casual_leave_allotted',
            'restricted_holiday_allotted'
        ]

        input_data = request.data  # expect JSON payload

        # Update LeaveBalance fields if provided in the payload.
        for field in leave_balance_fields:
            if field in input_data:
                try:
                    # It's a good idea to cast to float (or int) based on your model definition.
                    setattr(leave_balance, field, float(input_data[field]))
                except (ValueError, TypeError):
                    return JsonResponse({'error': f'Invalid value for {field}'}, status=400)

        # Update LeavePerYear fields if provided.
        for field in leave_per_year_fields:
            if field in input_data:
                try:
                    setattr(leave_per_year, field, float(input_data[field]))
                except (ValueError, TypeError):
                    return JsonResponse({'error': f'Invalid value for {field}'}, status=400)

        # Save changes to both models.
        leave_balance.save()
        leave_per_year.save()

        return JsonResponse({'message': 'Leave balance and leave per year updated successfully!'}, status=200)

    except Exception as e:
        # Consider logging the error in a production environment.
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)




# create an api to get leave_requests of employee with empid with date filter if none then 1 year back
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def admin_get_leave_requests(request, empid):
    """
    API endpoint to get all leave requests for a specified employee.
    """
    user = request.user

    if not user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        # Get the user's ExtraInfo record to verify role
        extra_info_qs = ExtraInfo.objects.filter(user=user)
        if not extra_info_qs.exists():
            return JsonResponse({'error': 'ExtraInfo not found'}, status=404)
        extra_info = extra_info_qs.first()

        # Permission check based on last selected role
        if extra_info.last_selected_role != 'SectionHead_HR':
            return JsonResponse({'error': 'You do not have access to get leave requests'}, status=403)

        # Fetch the employee using the provided empid
        try:
            emp_user = User.objects.get(id=empid)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

        try:
            employee = Employee.objects.get(id=emp_user)
        except Employee.DoesNotExist:
            return JsonResponse({'error': 'Employee not found'}, status=404)

        # Fetch leave requests for the employee
        query_date = request.GET.get('date')
        if not query_date:
            query_date = datetime.now().date() - timedelta(days=365)
        else:
            query_date = datetime.strptime(query_date, '%Y-%m-%d').date()

        leave_requests = LeaveForm.objects.filter(employee=employee, submissionDate__gte=query_date)

        # Prepare the response data
        leave_requests_data = []
        for leave_request in leave_requests:
            leave_requests_data.append({
                'id': leave_request.id,
                'submissionDate': leave_request.submissionDate,
                'status': leave_request.status,
                'leaveStartDate': leave_request.leaveStartDate,
                'leaveEndDate': leave_request.leaveEndDate,
            })

        return JsonResponse({'leave_requests': leave_requests_data}, status=200)

    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)



# @api_view(['GET'])
# @authentication_classes([TokenAuthentication])
# @permission_classes([IsAuthenticated])
# def get_hr_employees(request):
#     """
#     API endpoint to retrieve all HR-access employees (faculty + staff).

#     For each employee (from the Employee model):
#       - Fetch the related user (a OneToOne relation via the `id` field).
#       - Using ExtraInfo, get the department (if available), else keep it null.
#       - Using HoldsDesignation, return one entry per designation.
#         If no designation exists for the employee, a single entry with designation as null is returned.

#     Returns:
#         A JSON response (list) of entries with the following keys:
#         - id
#         - name (concatenated first and last name)
#         - username
#         - designation
#         - department
#     """
#     # Check if the user has HR access
#     if not check_hr_access(request):
#         return JsonResponse({'error': 'HR access required'}, status=403)

#     try:
#         # Get all employees (this table already contains only HR-access employees)
#         employees = Employee.objects.all()
#         results = []

#         for emp in employees:
#             # Employee.id is a OneToOneField to the User model.
#             user_inst = emp.id

#             # Fetch extra info similar to get_form_initials.
#             # If no ExtraInfo exists (or no department is set), department is kept as None.
#             extra_info = ExtraInfo.objects.filter(user=user_inst).first()
#             department = extra_info.department.name if extra_info and extra_info.department else None

#             # Fetch designations from HoldsDesignation model
#             designations_qs = HoldsDesignation.objects.filter(user=user_inst)
#             if designations_qs.exists():
#                 # Return one record per designation.
#                 for hd in designations_qs:
#                     results.append({
#                         "id": user_inst.id,
#                         "name": f"{user_inst.first_name} {user_inst.last_name}",
#                         "username": user_inst.username,
#                         "designation": hd.designation.name,  # Assuming the designation has a 'name' field.
#                         "department": department,
#                     })
#             else:
#                 # If no designation exists, include the employee with designation set to None.
#                 results.append({
#                     "id": user_inst.id,
#                     "name": f"{user_inst.first_name} {user_inst.last_name}",
#                     "username": user_inst.username,
#                     "designation": None,
#                     "department": department,
#                 })

#         return JsonResponse(results, safe=False, status=200)

#     except Exception as e:
#         return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)






@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_hr_employees(request):
    """
    API endpoint to retrieve all HR-access employees (faculty + staff)
    with a single entry per employee. For each employee (from the Employee model):
      - Fetch the related user (a OneToOne relation via the `id` field).
      - Using ExtraInfo, get the department (if available), else keep it null.
    
    Returns:
        A JSON response (list) of entries with the following keys:
        - id
        - name (concatenated first and last name)
        - username
        - department
    """

    # Check if the user has HR access.
    if not check_hr_access(request):
        return JsonResponse({'error': 'HR access required'}, status=403)

    try:
        # Get all employees (the Employee model already includes only those with HR access).
        employees = Employee.objects.all()
        results = []

        for emp in employees:
            # Employee.id is a OneToOneField to the User model.
            user_inst = emp.id

            # Fetch extra info (for department information) similar to get_form_initials.
            extra_info = ExtraInfo.objects.filter(user=user_inst).first()
            department = extra_info.department.name if extra_info and extra_info.department else None

            # Append a single entry per employee.
            results.append({
                "id": user_inst.id,
                "name": f"{user_inst.first_name} {user_inst.last_name}",
                "username": user_inst.username,
                "department": department,
            })

        return JsonResponse(results, safe=False, status=200)

    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)



@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def offline_leave_form(request):
    """
    API endpoint to handle offline leave form submission.
    Automatically approves the leave and updates the leave balance.
    """
    user = request.user

    if not user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    # checking hr access
    if not check_hr_access(request):
        return JsonResponse({'error': 'HR access required'}, status=403)
    
    # checking if user is admin or not
    try:
        extra_info = ExtraInfo.objects.get(user=user)
        if extra_info.last_selected_role != 'SectionHead_HR':
            return JsonResponse({'error': 'You do not have access to this API'}, status=403)
    except ExtraInfo.DoesNotExist:
        return JsonResponse({'error': 'ExtraInfo not found'}, status=404)
    


    try:
        form_data = request.POST
        files = request.FILES
        print("Form Data:", form_data)  # Debugging
        print(1)

        # Parse and validate complex fields
        try:
            employee_details = json.loads(form_data.get('employeeDetails', '{}'))
            leave_details = json.loads(form_data.get('leaveDetails', '{}'))
            station_leave = json.loads(form_data.get('stationLeave', '{}'))
            responsibility_transfer = json.loads(form_data.get('responsibilityTransfer', '{}'))
            forward_to = json.loads(form_data.get('forwardTo', '{}'))
        except json.JSONDecodeError as e:
            return JsonResponse({'error': f'Invalid JSON format in one of the fields: {str(e)}'}, status=400)

        print(2)

        print("Parsed Employee Details:", employee_details)
        print("Parsed Leave Details:", leave_details)
        print("Parsed Station Leave:", station_leave)
        print("Parsed Responsibility Transfer:", responsibility_transfer)
        print("Parsed Forward To:", forward_to)

        # Validate required fields
        required_fields = [
            'leaveStartDate', 'leaveEndDate', 'purpose'
        ]
        missing_fields = [field for field in required_fields if field not in leave_details]
        if missing_fields:
            return JsonResponse(
                {'error': f"Missing required fields: {', '.join(missing_fields)}"},
                status=400
            )

        # Validate forwardTo field
        if 'id' not in forward_to:
            return JsonResponse(
                {'error': "Missing required field: forwardTo"},
                status=400
            )

        print(3)

        # Validate dates
        try:
            leave_start_date = datetime.strptime(leave_details.get('leaveStartDate'), "%Y-%m-%d").date()
            leave_end_date = datetime.strptime(leave_details.get('leaveEndDate'), "%Y-%m-%d").date()
            if leave_end_date < leave_start_date:
                return JsonResponse(
                    {'error': 'Leave end date cannot be before start date'},
                    status=400
                )
        except ValueError:
            return JsonResponse(
                {'error': 'Invalid leave date format. Use YYYY-MM-DD'},
                status=400
            )

        print(4)

        # Use employee details from the parsed data
        employee_id = employee_details.get('id')
        if not employee_id:
            return JsonResponse({'error': 'Employee ID is required in employeeDetails'}, status=400)

        employee_name = employee_details.get('name')
        if not employee_name:
            return JsonResponse({'error': 'Employee name is required in employeeDetails'}, status=400)

        employee_designation = employee_details.get('designation')
        if not employee_designation:
            return JsonResponse({'error': 'Employee designation is required in employeeDetails'}, status=400)

        employee_pfno = employee_details.get('pfno')
        if not employee_pfno:
            return JsonResponse({'error': 'Employee PF number is required in employeeDetails'}, status=400)

        print(5)

        # Validate and fetch academic responsibility
        academic_responsibility_user = None
        academic_responsibility_designation = None
        if responsibility_transfer.get('academicResponsibility'):
            try:
                academic_responsibility_user = Employee.objects.get(id=responsibility_transfer['academicResponsibility']['id'])
                academic_responsibility_designation = Designation.objects.get(name=responsibility_transfer['academicResponsibility']['designation'])
                
            except (Employee.DoesNotExist, Designation.DoesNotExist):
                return JsonResponse({'error': 'Invalid academic responsibility details'}, status=400)

        # Validate and fetch administrative responsibility
        administrative_responsibility_user = None
        administrative_responsibility_designation = None
        if responsibility_transfer.get('administrativeResponsibility'):
            try:
                administrative_responsibility_user = Employee.objects.get(id=responsibility_transfer['administrativeResponsibility']['id'])
                administrative_responsibility_designation = Designation.objects.get(name=responsibility_transfer['administrativeResponsibility']['designation'])
            except (Employee.DoesNotExist, Designation.DoesNotExist):
                return JsonResponse({'error': 'Invalid administrative responsibility details'}, status=400)

        print(6)
        
        # get forward_designation Designation object by name

        try:
            forward_designation = Designation.objects.get(name=forward_to['designation'])
        except Designation.DoesNotExist:
            return JsonResponse({'error': 'Invalid forwardTo designation'}, status=400)
        
        print(7)
        print(forward_to['id'])
        print(forward_designation)
    

        # Create leave form
        leave_form = LeaveForm(
            employee=Employee.objects.get(id=employee_id),  # Use employee ID from parsed data
            name=employee_name,  # Use name from employeeDetails
            designation=employee_designation,
            personalfileNo=employee_pfno,
            submissionDate=datetime.now().date(),
            departmentInfo=employee_details.get('department', 'N/A'),
            leaveStartDate=leave_start_date,
            leaveEndDate=leave_end_date,
            Purpose_of_leave=leave_details.get('purpose'),
            Noof_CasualLeave=int(leave_details.get('casualLeave', 0)),
            Noof_vacationLeave=int(leave_details.get('vacationLeave', 0)),
            Noof_earnedLeave=int(leave_details.get('earnedLeave', 0)),
            Noof_commutedLeave=int(leave_details.get('commutedLeave', 0)),
            Noof_specialCasualLeave=int(leave_details.get('specialCasualLeave', 0)),
            Noof_restrictedHoliday=int(leave_details.get('restrictedHoliday', 0)),
            Noof_halfPayLeave=int(leave_details.get('halfPayLeave', 0)),
            Noof_maternityLeave=int(leave_details.get('maternityLeave', 0)),
            Noof_childCareLeave=int(leave_details.get('childCareLeave', 0)),
            Noof_paternityLeave=int(leave_details.get('paternityLeave', 0)),
            Remarks=leave_details.get('remarks', 'N/A'),
            LeavingStation=station_leave.get('isStationLeave', False),
            StationLeave_startdate=station_leave.get('stationLeaveStartDate'),
            StationLeave_enddate=station_leave.get('stationLeaveEndDate'),
            Address_During_StationLeave=station_leave.get('stationLeaveAddress'),
            status='Accepted',
            AcademicResponsibility_user=academic_responsibility_user,
            AcademicResponsibility_designation=academic_responsibility_designation,
            AcademicResponsibility_status='Accepted',
            AdministrativeResponsibility_user=administrative_responsibility_user,
            AdministrativeResponsibility_designation=administrative_responsibility_designation,
            AdministrativeResponsibility_status='Accepted',
            approved_by=Employee.objects.get(id=forward_to['id']),
            approved_by_designation=forward_designation,
            approvedDate=datetime.now().date(),
            first_recieved_by=Employee.objects.get(id=forward_to['id']),
            first_recieved_designation=forward_designation,
            
            attached_pdf=files.get('attachedPdf').read() if files.get('attachedPdf') else None,
            attached_pdf_name=files.get('attachedPdf').name if files.get('attachedPdf') else None,
            application_type='Offline'  # Explicitly set to Offline
        )
        print(86977)
        
        leave_form.save()

        print(8)



        # Create file tracking
        try:
            # Fetch the Employee object using employee_id
            print("emp_id", employee_id)  # Debugging
            uploader_employee = Employee.objects.get(id=employee_id)
            print("uploader_employee", uploader_employee)  # Debugging

            # Fetch the receiver's username
            receiver_employee = Employee.objects.get(id=forward_to['id'])
            receiver_username = receiver_employee.id.username  # Get the username of the receiver

            # Log inputs to create_file
            print("uploader:", uploader_employee.id.username)
            print("uploader_designation:", employee_designation)
            print("receiver:", receiver_username)  # Use the username of the receiver
            print("receiver_designation:", forward_to['designation'])
            print("src_module:", "HR")
            print("src_object_id:", str(leave_form.id))

            # Call create_file
            file_id = create_file(
                uploader=uploader_employee.id.username,
                uploader_designation=employee_designation,
                receiver=receiver_username,  # Pass the username of the receiver
                receiver_designation=forward_to['designation'],
                src_module="HR",
                src_object_id=str(leave_form.id),
                file_extra_JSON={"type": "Leave"},
                attached_file=None
            )
             # Update the leave form with the file_id
            leave_form.file_id = file_id
            leave_form.save()
            print(file_id)
            current_owner = get_current_file_owner(file_id)
            current_owner_designation=get_current_file_owner_designation(file_id)
            remarks = f"Accepted by {current_owner} "
            track_id=forward_file(
                file_id=file_id,
                receiver=current_owner,
                receiver_designation=current_owner_designation,
                remarks=remarks,
                file_extra_JSON=None
            )

            # Approve the file
            

            print(9)  # Debugging
           
        except Exception as e:
            print(f"Error in create_file: {str(e)}")  # Debugging
            return JsonResponse(
                {'error': f'Failed to create file tracking: {str(e)}'},
                status=500
            )

        # Update leave balance
        leave_balance = LeaveBalance.objects.get(empid=Employee.objects.get(id=employee_id))
        leave_balance.casual_leave_taken += leave_form.Noof_CasualLeave
        leave_balance.special_casual_leave_taken += leave_form.Noof_specialCasualLeave
        leave_balance.earned_leave_taken += (leave_form.Noof_earnedLeave + 2 * leave_form.Noof_vacationLeave)
        leave_balance.half_pay_leave_taken += (leave_form.Noof_halfPayLeave + 2 * leave_form.Noof_commutedLeave)
        leave_balance.maternity_leave_taken += leave_form.Noof_maternityLeave
        leave_balance.child_care_leave_taken += leave_form.Noof_childCareLeave
        leave_balance.paternity_leave_taken += leave_form.Noof_paternityLeave
        leave_balance.restricted_holiday_taken += leave_form.Noof_restrictedHoliday
        leave_balance.save()

        return JsonResponse(
            {
                'message': 'Offline leave form submitted and approved successfully',
                'form_id': leave_form.id,
                'file_id': file_id
            },
            status=201
        )

    except Exception as e:
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)
    

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_employee_initials(request,empid):
    """
    API endpoint to get the details for an employee.
    If a query parameter "id" is provided, it fetches data for that employee.
    Otherwise, it returns the details for the logged-in user.
    """
    # Check if an employee id is provided in the query parameters
    employee_id = empid
    print(employee_id)
    try:
        if employee_id:
            # Fetch the employee based on the provided id
            employee = Employee.objects.get(id=employee_id)
        else:
            # Fall back to the logged-in user
            employee = Employee.objects.get(id=request.user.id)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee not found'}, status=404)
    print(0)
    try:
        # Fetch extra info associated with the employee (adjust if Employee and User differ)
        extra_info = ExtraInfo.objects.filter(user=employee.id).first()
        if not extra_info:
            return JsonResponse({'error': 'ExtraInfo not found'}, status=404)
        print(1)
        # get user of employee
        user = User.objects.filter(id=employee_id).first()
        print(user)
        emp_confidential = EmpConfidentialDetails.objects.filter(empid=employee).first()
        if not emp_confidential:
            return JsonResponse({'error': 'EmpConfidentialDetails not found'}, status=404)
        print(2)
        department_name = extra_info.department.name if extra_info.department else None
        print(3)
        print(user)
        print(emp_confidential.personal_file_number)
        print(department_name)
        return JsonResponse({
            'name': user.first_name + " " + user.last_name,
            
            'pfno': emp_confidential.personal_file_number,
            'department': department_name,
        }, status=200)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)
