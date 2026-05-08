import datetime

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from applications.globals.models import ExtraInfo, HoldsDesignation
from decimal import Decimal
from ..models import LeaveApplicationNew, EmployeeLeaveBalance, AppraisalFormNew, LeaveType
from ..services import (
    approve_leave_application, reject_leave_application,
    handle_academic_responsibility, handle_administrative_responsibility,
    mark_attendance, calculate_faculty_workload,
    InsufficientLeaveBalanceError, DuplicateLeaveApplicationError, InvalidWorkflowTransitionError
)
from ..selectors import (
    get_employee_by_id, get_all_employees, get_leave_balance_for_employee,
    get_leave_applications, get_pending_responsibility_leaves,
    get_attendance_for_employee, get_appraisal_periods, get_appraisals_for_employee,
    get_available_training_programs, get_nominations_for_employee,
    get_promotion_applications, get_faculty_workload
)
from .serializers import (
    EmployeeDetailsSerializer, LeaveApplicationSerializer, LeaveBalanceSerializer,
    PerformanceAppraisalSerializer, TrainingProgramSerializer, TrainingNominationSerializer,
    PromotionApplicationSerializer, EmployeeAttendanceSerializer, FacultyWorkloadSerializer,
    AppraisalPeriodSerializer
)

# ==================== EMPLOYEE VIEWS ====================

class EmployeeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee_type = request.query_params.get('type')
        department_id = request.query_params.get('department')
        employees = get_all_employees(employee_type, department_id)
        serializer = EmployeeDetailsSerializer(employees, many=True)
        return Response(serializer.data)

class EmployeeDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id):
        employee = get_employee_by_id(employee_id)
        serializer = EmployeeDetailsSerializer(employee)
        return Response(serializer.data)

    def put(self, request, employee_id):
        employee = get_employee_by_id(employee_id)
        serializer = EmployeeDetailsSerializer(employee, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ==================== LEAVE VIEWS ====================

class LeaveApplicationListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        is_hr_staff = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='hr',
        ).exists() or (
            request.user.extrainfo.user_type == 'staff'
            and request.user.extrainfo.department
            and request.user.extrainfo.department.name == 'HR'
        )
        is_hod = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='hod',
        ).exists()
        is_director = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='director',
        ).exists()
        is_registrar = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='registrar',
        ).exists()

        if is_hr_staff:
            leaves = LeaveApplicationNew.objects.all()
        elif is_director:
            leaves = LeaveApplicationNew.objects.filter(
                Q(
                    approval_status='FORWARDED',
                    current_approver_role__iexact='Director',
                ) | Q(employee=request.user.extrainfo) | Q(
                    cancel_status='REQUESTED',
                    cancel_current_approver_role__iexact='Director',
                ) | Q(
                    extension_status='REQUESTED',
                    extension_current_approver_role__iexact='Director',
                )
            )
        elif is_registrar:
            leaves = LeaveApplicationNew.objects.filter(
                Q(
                    approval_status='FORWARDED',
                    current_approver_role__iexact='Registrar',
                ) | Q(employee=request.user.extrainfo) | Q(
                    cancel_status='REQUESTED',
                    cancel_current_approver_role__iexact='Registrar',
                ) | Q(
                    extension_status='REQUESTED',
                    extension_current_approver_role__iexact='Registrar',
                )
            )
        elif is_hod:
            leaves = LeaveApplicationNew.objects.filter(
                department=request.user.extrainfo.department.name
            )
        else:
            leaves = get_leave_applications(request.user.extrainfo)
        serializer = LeaveApplicationSerializer(leaves, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        serializer = LeaveApplicationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            employee = getattr(request.user, 'extrainfo', None)
            if employee is None:
                employee_id = request.data.get('employee_id')
                if employee_id:
                    employee = get_employee_by_id(employee_id)
            if employee is None:
                return Response(
                    {'error': 'Employee profile not found for this user.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            nominee_id = (request.data.get('nominee_employee_id') or '').strip()
            nominee_status = 'PENDING' if nominee_id else 'NOT_REQUIRED'
            is_director = HoldsDesignation.objects.filter(
                working=employee.user,
                designation__name__icontains='director',
            ).exists()
            is_hod = HoldsDesignation.objects.filter(
                working=employee.user,
                designation__name__icontains='hod',
            ).exists()
            is_registrar = HoldsDesignation.objects.filter(
                working=employee.user,
                designation__name__icontains='registrar',
            ).exists()
            is_hr_admin = HoldsDesignation.objects.filter(
                working=employee.user,
                designation__name__iregex=r'hr admin|hr administrator',
            ).exists()
            is_accountant = HoldsDesignation.objects.filter(
                working=employee.user,
                designation__name__icontains='accountant',
            ).exists()
            leave_type_name = (request.data.get('leave_type') or '').strip()
            is_cl_rh_leave = leave_type_name in ['Casual', 'Restricted']
            employee_name = employee.user.get_full_name() or employee.user.username
            department_name = employee.department.name if employee.department else (request.data.get('department') or '')
            designation_name = ''
            designation_record = HoldsDesignation.objects.filter(working=employee.user).select_related('designation').first()
            if designation_record:
                designation_name = designation_record.designation.full_name or designation_record.designation.name
            else:
                designation_name = request.data.get('designation') or ''
            approval_status = 'PENDING'
            approver_role = ''
            if is_director:
                approval_status = 'APPROVED'
                approver_role = 'Director'
            elif is_registrar:
                approval_status = 'FORWARDED'
                approver_role = 'Director'
            elif is_hod:
                if is_cl_rh_leave:
                    approval_status = 'PENDING'
                    approver_role = 'HOD'
                else:
                    approval_status = 'FORWARDED'
                    approver_role = 'Director'
            elif is_hr_admin or is_accountant:
                approval_status = 'FORWARDED'
                approver_role = 'Registrar'

            leave_app = serializer.save(
                employee=employee,
                employee_name=employee_name,
                department=department_name,
                designation=designation_name,
                handover_to=nominee_id,
                nominee_status=nominee_status,
                approval_status=approval_status,
                current_approver_role=approver_role,
            )
            if is_director:
                _apply_leave_balance_for_approval(leave_app)
                leave_app.save(update_fields=['leave_balance_before', 'leave_balance_after'])
            refreshed_serializer = LeaveApplicationSerializer(leave_app, context={'request': request})
            return Response(refreshed_serializer.data, status=status.HTTP_201_CREATED)
        # Log validation errors to server console for easier debugging without DevTools.
        print("LeaveApplication validation errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LeaveApplicationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        leave_app = get_object_or_404(LeaveApplicationNew, pk=pk)
        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)

    def put(self, request, pk):
        leave_app = get_object_or_404(LeaveApplicationNew, pk=pk)
        if leave_app.employee != request.user.extrainfo and not request.user.is_staff:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        serializer = LeaveApplicationSerializer(leave_app, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        leave_app = get_object_or_404(LeaveApplicationNew, pk=pk)
        if leave_app.status != 'PENDING':
            return Response({'error': 'Cannot delete non-pending application'}, status=status.HTTP_400_BAD_REQUEST)
        leave_app.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class LeaveApplicationDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        leave_app = get_object_or_404(LeaveApplicationNew, pk=pk)
        if leave_app.employee != request.user.extrainfo and not request.user.is_staff:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        lines = [
            f"Leave Application #{leave_app.id}",
            "",
            f"Employee: {leave_app.employee_name}",
            f"Employee ID: {leave_app.employee.id}",
            f"Department: {leave_app.department}",
            f"Designation: {leave_app.designation}",
            "",
            f"Leave Type: {leave_app.leave_type}",
            f"Station Leave: {leave_app.station_leave or 'N/A'}",
            f"Half-day: {'Yes' if leave_app.is_half_day else 'No'}",
            f"Half-day Slot: {leave_app.half_day_slot or 'N/A'}",
            f"Start Date: {leave_app.start_date}",
            f"End Date: {leave_app.end_date}",
            f"Total Days: {leave_app.total_days}",
            "",
            f"Reason: {leave_app.reason}",
            f"Contact During Leave: {leave_app.contact_during_leave}",
            f"Address During Leave: {leave_app.address_during_leave}",
            "",
            f"Nominee Employee ID: {leave_app.handover_to or 'N/A'}",
            f"Nominee Status: {leave_app.nominee_status}",
            "",
            f"Approval Status: {leave_app.approval_status}",
            f"Applied Date: {leave_app.applied_date}",
        ]

        content = "\n".join(lines)
        response = HttpResponse(content, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="leave-application-{leave_app.id}.txt"'
        return response

class LeaveApplicationWithdrawView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        leave_app = get_object_or_404(LeaveApplicationNew, pk=pk)
        if leave_app.employee != request.user.extrainfo:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        if leave_app.approval_status not in ['PENDING', 'FORWARDED']:
            return Response({'error': 'Only pending or forwarded requests can be withdrawn.'}, status=status.HTTP_400_BAD_REQUEST)

        is_registrar = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='registrar',
        ).exists()
        is_accountant = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='accountant',
        ).exists()
        is_hr_admin = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__iregex=r'hr admin|hr administrator',
        ).exists()

        if is_registrar or is_accountant or is_hr_admin:
            leave_app.approval_status = 'REJECTED'
            if is_registrar:
                leave_app.current_approver_role = 'Registrar'
            elif is_accountant:
                leave_app.current_approver_role = 'Accountant'
            else:
                leave_app.current_approver_role = 'HR Admin'
        else:
            leave_app.approval_status = 'WITHDRAWN'
            leave_app.current_approver_role = 'Employee'
        leave_app.remarks = (request.data.get('remarks') or '').strip()
        leave_app.save(update_fields=['approval_status', 'current_approver_role', 'remarks'])
        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)

class LeaveApplicationCancelRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        leave_app = get_object_or_404(LeaveApplicationNew, pk=pk)
        if leave_app.employee != request.user.extrainfo:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        if leave_app.approval_status != 'APPROVED':
            return Response({'error': 'Only approved requests can be cancelled.'}, status=status.HTTP_400_BAD_REQUEST)
        if leave_app.cancel_status != 'NOT_REQUESTED':
            return Response({'error': 'Cancellation already processed or pending.'}, status=status.HTTP_400_BAD_REQUEST)

        today = timezone.now().date()
        if today >= leave_app.start_date:
            return Response(
                {'error': 'Cancellation allowed only up to 1 day prior to start date.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_director = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='director',
        ).exists()
        is_hod = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='hod',
        ).exists()
        is_registrar = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='registrar',
        ).exists()
        is_accountant = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='accountant',
        ).exists()
        is_hr_admin = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__iregex=r'hr admin|hr administrator',
        ).exists()

        requester_role = 'Employee'
        if is_director:
            requester_role = 'Director'
        elif is_hod:
            requester_role = 'HOD'
        elif is_registrar:
            requester_role = 'Registrar'
        elif is_accountant:
            requester_role = 'Accountant'
        elif is_hr_admin:
            requester_role = 'HR Admin'

        cancel_approver_role = 'HOD'
        if requester_role in ['HOD', 'Director', 'Registrar']:
            cancel_approver_role = 'Director'
        elif requester_role in ['Accountant', 'HR Admin']:
            cancel_approver_role = 'Registrar'

        leave_app.cancel_status = 'REQUESTED'
        leave_app.cancel_requested_at = timezone.now()
        leave_app.cancel_requested_by_role = requester_role
        leave_app.cancel_current_approver_role = cancel_approver_role
        leave_app.cancel_reason = (request.data.get('reason') or '').strip()
        leave_app.save(update_fields=[
            'cancel_status',
            'cancel_requested_at',
            'cancel_requested_by_role',
            'cancel_current_approver_role',
            'cancel_reason',
        ])
        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)

class LeaveApplicationCancelDecisionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, decision):
        leave_app = get_object_or_404(LeaveApplicationNew, pk=pk)
        decision = (decision or '').lower()
        if decision not in ['approve', 'reject']:
            return Response({'error': 'Invalid decision'}, status=status.HTTP_400_BAD_REQUEST)
        if leave_app.cancel_status != 'REQUESTED':
            return Response({'error': 'No cancellation request pending.'}, status=status.HTTP_400_BAD_REQUEST)

        approver_role = (leave_app.cancel_current_approver_role or '').lower()
        if approver_role == 'hod':
            allowed = HoldsDesignation.objects.filter(
                working=request.user,
                designation__name__icontains='hod',
            ).exists()
        elif approver_role == 'director':
            allowed = HoldsDesignation.objects.filter(
                working=request.user,
                designation__name__icontains='director',
            ).exists()
        elif approver_role == 'registrar':
            allowed = HoldsDesignation.objects.filter(
                working=request.user,
                designation__name__icontains='registrar',
            ).exists()
        else:
            allowed = False

        if not allowed:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        remarks = (request.data.get('remarks') or '').strip()
        leave_app.cancel_decided_at = timezone.now()
        leave_app.cancel_decision_remarks = remarks

        if decision == 'approve':
            leave_app.cancel_status = 'APPROVED'
            leave_app.approval_status = 'CANCELLED'
            leave_app.current_approver_role = leave_app.cancel_current_approver_role
            _restore_leave_balance_for_cancellation(leave_app)
        else:
            leave_app.cancel_status = 'REJECTED'

        leave_app.save(update_fields=[
            'cancel_status',
            'cancel_decided_at',
            'cancel_decision_remarks',
            'approval_status',
            'current_approver_role',
            'leave_balance_before',
            'leave_balance_after',
        ])
        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)

class LeaveApplicationExtensionRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        leave_app = get_object_or_404(LeaveApplicationNew, pk=pk)
        if leave_app.employee != request.user.extrainfo:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        if leave_app.approval_status != 'APPROVED':
            return Response({'error': 'Only approved requests can be extended.'}, status=status.HTTP_400_BAD_REQUEST)
        if leave_app.extension_status != 'NOT_REQUESTED':
            return Response({'error': 'Extension already processed or pending.'}, status=status.HTTP_400_BAD_REQUEST)

        today = timezone.now().date()
        if today >= leave_app.end_date:
            return Response({'error': 'Extension allowed only before the original end date.'}, status=status.HTTP_400_BAD_REQUEST)

        new_end_date_raw = request.data.get('new_end_date')
        if not new_end_date_raw:
            return Response({'error': 'New end date is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            new_end_date = datetime.datetime.strptime(new_end_date_raw, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'New end date must be in YYYY-MM-DD format.'}, status=status.HTTP_400_BAD_REQUEST)
        if new_end_date <= leave_app.end_date:
            return Response({'error': 'New end date must be after the current end date.'}, status=status.HTTP_400_BAD_REQUEST)

        new_total_days = Decimal((new_end_date - leave_app.start_date).days + 1)

        is_director = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='director',
        ).exists()
        is_hod = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='hod',
        ).exists()
        is_registrar = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='registrar',
        ).exists()
        is_accountant = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='accountant',
        ).exists()
        is_hr_admin = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__iregex=r'hr admin|hr administrator',
        ).exists()

        requester_role = 'Employee'
        if is_director:
            requester_role = 'Director'
        elif is_hod:
            requester_role = 'HOD'
        elif is_registrar:
            requester_role = 'Registrar'
        elif is_accountant:
            requester_role = 'Accountant'
        elif is_hr_admin:
            requester_role = 'HR Admin'

        approver_role = 'HOD'
        if requester_role in ['HOD', 'Director', 'Registrar']:
            approver_role = 'Director'
        elif requester_role in ['Accountant', 'HR Admin']:
            approver_role = 'Registrar'

        leave_app.extension_status = 'REQUESTED'
        leave_app.extension_requested_at = timezone.now()
        leave_app.extension_requested_by_role = requester_role
        leave_app.extension_current_approver_role = approver_role
        leave_app.extension_reason = (request.data.get('reason') or '').strip()
        leave_app.extension_new_end_date = new_end_date
        leave_app.extension_new_total_days = new_total_days
        leave_app.save(update_fields=[
            'extension_status',
            'extension_requested_at',
            'extension_requested_by_role',
            'extension_current_approver_role',
            'extension_reason',
            'extension_new_end_date',
            'extension_new_total_days',
        ])
        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)

class LeaveApplicationExtensionDecisionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, decision):
        leave_app = get_object_or_404(LeaveApplicationNew, pk=pk)
        decision = (decision or '').lower()
        if decision not in ['approve', 'reject']:
            return Response({'error': 'Invalid decision'}, status=status.HTTP_400_BAD_REQUEST)
        if leave_app.extension_status != 'REQUESTED':
            return Response({'error': 'No extension request pending.'}, status=status.HTTP_400_BAD_REQUEST)

        approver_role = (leave_app.extension_current_approver_role or '').lower()
        if approver_role == 'hod':
            allowed = HoldsDesignation.objects.filter(
                working=request.user,
                designation__name__icontains='hod',
            ).exists()
        elif approver_role == 'director':
            allowed = HoldsDesignation.objects.filter(
                working=request.user,
                designation__name__icontains='director',
            ).exists()
        elif approver_role == 'registrar':
            allowed = HoldsDesignation.objects.filter(
                working=request.user,
                designation__name__icontains='registrar',
            ).exists()
        else:
            allowed = False

        if not allowed:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        remarks = (request.data.get('remarks') or '').strip()
        leave_app.extension_decided_at = timezone.now()
        leave_app.extension_decision_remarks = remarks

        if decision == 'approve':
            if not _apply_leave_balance_for_extension(leave_app):
                return Response({'error': 'Insufficient leave balance for extension.'}, status=status.HTTP_400_BAD_REQUEST)
            leave_app.extension_status = 'APPROVED'
            leave_app.current_approver_role = leave_app.extension_current_approver_role
            leave_app.end_date = leave_app.extension_new_end_date
            leave_app.total_days = leave_app.extension_new_total_days
        else:
            leave_app.extension_status = 'REJECTED'

        leave_app.save(update_fields=[
            'extension_status',
            'extension_decided_at',
            'extension_decision_remarks',
            'current_approver_role',
            'leave_balance_before',
            'leave_balance_after',
            'end_date',
            'total_days',
        ])
        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)

class LeaveResumptionSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        leave_app = get_object_or_404(LeaveApplicationNew, pk=pk)
        if leave_app.employee != request.user.extrainfo:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        if leave_app.approval_status != 'APPROVED':
            return Response({'error': 'Resumption allowed only for approved leaves.'}, status=status.HTTP_400_BAD_REQUEST)
        if leave_app.resumption_status != 'NOT_REQUESTED':
            return Response({'error': 'Resumption already submitted or processed.'}, status=status.HTTP_400_BAD_REQUEST)

        today = timezone.now().date()
        resumption_date_raw = (request.data.get('resumption_date') or '').strip()
        if resumption_date_raw:
            try:
                resumption_date = datetime.datetime.strptime(resumption_date_raw, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Resumption date must be in YYYY-MM-DD format.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            resumption_date = today

        if resumption_date <= leave_app.end_date:
            return Response({'error': 'Resumption date must be after the leave end date.'}, status=status.HTTP_400_BAD_REQUEST)

        leave_app.resumption_status = 'SUBMITTED'
        leave_app.resumption_date = resumption_date
        leave_app.resumption_reason = (request.data.get('reason') or '').strip()
        leave_app.resumption_submitted_at = timezone.now()
        leave_app.resumption_current_approver_role = 'HOD'
        leave_app.save(update_fields=[
            'resumption_status',
            'resumption_date',
            'resumption_reason',
            'resumption_submitted_at',
            'resumption_current_approver_role',
        ])
        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)

class LeaveResumptionDecisionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, decision):
        leave_app = get_object_or_404(LeaveApplicationNew, pk=pk)
        decision = (decision or '').lower()
        if decision not in ['approve', 'reject']:
            return Response({'error': 'Invalid decision'}, status=status.HTTP_400_BAD_REQUEST)
        if leave_app.resumption_status != 'SUBMITTED':
            return Response({'error': 'No resumption request pending.'}, status=status.HTTP_400_BAD_REQUEST)

        allowed = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='hod',
        ).exists()
        if not allowed:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        leave_app.resumption_decided_at = timezone.now()
        leave_app.resumption_decision_remarks = (request.data.get('remarks') or '').strip()
        if decision == 'approve':
            leave_app.resumption_status = 'APPROVED'
            leave_app.current_approver_role = 'HOD'
        else:
            leave_app.resumption_status = 'REJECTED'

        leave_app.save(update_fields=[
            'resumption_status',
            'resumption_decided_at',
            'resumption_decision_remarks',
            'current_approver_role',
        ])
        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)

class LeaveBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id=None):
        if employee_id:
            employee = get_object_or_404(ExtraInfo, id=employee_id)
        else:
            employee = request.user.extrainfo
        balances_qs = (
            EmployeeLeaveBalance.objects.filter(employee=employee)
            .select_related('leave_type')
            .order_by('leave_type_id', '-year', '-id')
        )
        # Collect the latest balance per leave type without relying on DISTINCT ON.
        balances = []
        seen_leave_types = set()
        for balance in balances_qs:
            if balance.leave_type_id in seen_leave_types:
                continue
            seen_leave_types.add(balance.leave_type_id)
            balances.append(balance)
        serializer = LeaveBalanceSerializer(balances, many=True)
        return Response(serializer.data)

class LeaveNomineeDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee = request.user.extrainfo
        leaves = LeaveApplicationNew.objects.filter(
            handover_to=employee.id,
            nominee_status='PENDING',
        ).order_by('-applied_date')
        serializer = LeaveApplicationSerializer(leaves, many=True)
        return Response(serializer.data)

class LeaveNomineeDecisionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        action = (request.data.get('action') or '').lower()
        if action not in ['accept', 'decline']:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

        leave_app = get_object_or_404(LeaveApplicationNew, pk=pk)
        employee = request.user.extrainfo
        if leave_app.handover_to != employee.id:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        leave_app.nominee_status = 'ACCEPTED' if action == 'accept' else 'DECLINED'
        leave_app.nominee_responded_at = datetime.datetime.utcnow()
        leave_app.save(update_fields=['nominee_status', 'nominee_responded_at'])
        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)

class LeaveDocumentRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        message = (request.data.get('message') or '').strip()
        if not message:
            return Response({'error': 'Document request message is required.'}, status=status.HTTP_400_BAD_REQUEST)

        is_hod = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='hod',
        ).exists()
        if not is_hod:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        leave_app = get_object_or_404(LeaveApplicationNew, pk=pk)
        if leave_app.document_request_status == 'REQUESTED':
            return Response({'error': 'Document already requested.'}, status=status.HTTP_400_BAD_REQUEST)
        leave_app.document_request_message = message
        leave_app.document_request_status = 'REQUESTED'
        leave_app.document_requested_at = datetime.datetime.utcnow()
        leave_app.save(update_fields=['document_request_message', 'document_request_status', 'document_requested_at'])
        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)

class LeaveDocumentSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        submission = (request.data.get('submission') or '').strip()
        if not submission:
            return Response({'error': 'Document submission is required.'}, status=status.HTTP_400_BAD_REQUEST)

        leave_app = get_object_or_404(LeaveApplicationNew, pk=pk)
        if leave_app.employee != request.user.extrainfo:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        if leave_app.document_request_status != 'REQUESTED':
            return Response({'error': 'No document requested for this leave.'}, status=status.HTTP_400_BAD_REQUEST)

        leave_app.document_submission = submission
        leave_app.document_request_status = 'SUBMITTED'
        leave_app.document_submitted_at = datetime.datetime.utcnow()
        leave_app.save(update_fields=['document_submission', 'document_request_status', 'document_submitted_at'])
        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)

class LeaveResponsibilityView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, responsibility_type):
        leave_app = get_object_or_404(LeaveApplicationNew, pk=pk)
        action = request.data.get('action')
        remarks = request.data.get('remarks', '')
        try:
            if responsibility_type == 'academic':
                leave_app = handle_academic_responsibility(leave_app, request.user.extrainfo, action, remarks)
            else:
                leave_app = handle_administrative_responsibility(leave_app, request.user.extrainfo, action, remarks)
            serializer = LeaveApplicationSerializer(leave_app)
            return Response(serializer.data)
        except (PermissionError, InvalidWorkflowTransitionError) as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

class LeaveApproveRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, decision):
        leave_app = get_object_or_404(LeaveApplicationNew, pk=pk)
        remarks = request.data.get('remarks', '')
        decision = (decision or '').lower()
        if decision not in ['approve', 'reject', 'forward']:
            return Response({'error': 'Invalid decision'}, status=status.HTTP_400_BAD_REQUEST)

        is_registrar = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='registrar',
        ).exists()
        is_director = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='director',
        ).exists()
        approver_role = 'HOD'
        if is_registrar:
            approver_role = 'Registrar'
        elif is_director:
            approver_role = 'Director'

        leave_type_name = (leave_app.leave_type or '').strip()
        is_cl_rh_leave = leave_type_name in ['Casual', 'Restricted']
        if decision == 'approve' and not is_cl_rh_leave and approver_role == 'HOD':
            return Response(
                {'error': 'Only CL/RH leaves can be approved by HOD. Please forward to Director.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if decision == 'forward' and is_cl_rh_leave:
            decision = 'approve'

        if decision == 'approve':
            leave_app.approval_status = 'APPROVED'
            leave_app.current_approver_role = approver_role
            _apply_leave_balance_for_approval(leave_app)
        elif decision == 'forward':
            leave_app.approval_status = 'FORWARDED'
            leave_app.current_approver_role = 'Director'
        else:
            leave_app.approval_status = 'REJECTED'
            leave_app.current_approver_role = approver_role

        leave_app.remarks = remarks
        leave_app.save(update_fields=[
            'approval_status',
            'remarks',
            'current_approver_role',
            'leave_balance_before',
            'leave_balance_after',
        ])

        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)


def _apply_leave_balance_for_approval(leave_app):
    leave_type = LeaveType.objects.filter(name__iexact=leave_app.leave_type).first()
    if not leave_type:
        return
    year = leave_app.start_date.year
    balance = EmployeeLeaveBalance.objects.filter(
        employee=leave_app.employee,
        leave_type=leave_type,
        year=year,
    ).first()
    if balance is None:
        balance = EmployeeLeaveBalance.objects.filter(
            employee=leave_app.employee,
            leave_type=leave_type,
        ).order_by('-year').first()
    if balance is None or balance.year != year:
        balance = EmployeeLeaveBalance.objects.create(
            employee=leave_app.employee,
            leave_type=leave_type,
            year=year,
            opening_balance=Decimal('0'),
            accrued=Decimal('0'),
            availed=Decimal('0'),
            current_balance=Decimal('0'),
        )
    total_days = Decimal(str(leave_app.total_days or 0))
    before_balance = balance.current_balance
    balance.availed = (balance.availed or 0) + total_days
    balance.current_balance = (balance.current_balance or 0) - total_days
    balance.save(update_fields=['availed', 'current_balance'])

    if leave_app.leave_balance_before is None:
        leave_app.leave_balance_before = before_balance
    leave_app.leave_balance_after = balance.current_balance

def _restore_leave_balance_for_cancellation(leave_app):
    leave_type = LeaveType.objects.filter(name__iexact=leave_app.leave_type).first()
    if not leave_type:
        return
    year = leave_app.start_date.year
    balance = EmployeeLeaveBalance.objects.filter(
        employee=leave_app.employee,
        leave_type=leave_type,
        year=year,
    ).first()
    if balance is None:
        balance = EmployeeLeaveBalance.objects.filter(
            employee=leave_app.employee,
            leave_type=leave_type,
        ).order_by('-year').first()
    if balance is None:
        return

    total_days = Decimal(str(leave_app.total_days or 0))
    before_balance = balance.current_balance
    balance.availed = (balance.availed or 0) - total_days
    balance.current_balance = (balance.current_balance or 0) + total_days
    balance.save(update_fields=['availed', 'current_balance'])

    if leave_app.leave_balance_before is None:
        leave_app.leave_balance_before = before_balance
    leave_app.leave_balance_after = balance.current_balance

def _apply_leave_balance_for_extension(leave_app):
    if not leave_app.extension_new_total_days:
        return False
    delta_days = Decimal(str(leave_app.extension_new_total_days)) - Decimal(str(leave_app.total_days or 0))
    if delta_days <= 0:
        return False

    leave_type = LeaveType.objects.filter(name__iexact=leave_app.leave_type).first()
    if not leave_type:
        return False
    year = leave_app.start_date.year
    balance = EmployeeLeaveBalance.objects.filter(
        employee=leave_app.employee,
        leave_type=leave_type,
        year=year,
    ).first()
    if balance is None:
        balance = EmployeeLeaveBalance.objects.filter(
            employee=leave_app.employee,
            leave_type=leave_type,
        ).order_by('-year').first()
    if balance is None:
        return False

    if (balance.current_balance or 0) < delta_days:
        return False

    before_balance = balance.current_balance
    balance.availed = (balance.availed or 0) + delta_days
    balance.current_balance = (balance.current_balance or 0) - delta_days
    balance.save(update_fields=['availed', 'current_balance'])

    if leave_app.leave_balance_before is None:
        leave_app.leave_balance_before = before_balance
    leave_app.leave_balance_after = balance.current_balance
    return True

# ==================== ATTENDANCE VIEWS ====================

class AttendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        attendance = get_attendance_for_employee(request.user.extrainfo, from_date, to_date)
        serializer = EmployeeAttendanceSerializer(attendance, many=True)
        return Response(serializer.data)

    def post(self, request):
        attendance = mark_attendance(
            employee_extra_info=request.user.extrainfo,
            date=request.data.get('date'),
            status=request.data.get('status'),
            in_time=request.data.get('in_time'),
            out_time=request.data.get('out_time'),
            remarks=request.data.get('remarks', '')
        )
        serializer = EmployeeAttendanceSerializer(attendance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# ==================== APPRAISAL VIEWS ====================

class AppraisalPeriodListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        is_active = request.query_params.get('is_active')
        periods = get_appraisal_periods(is_active)
        serializer = AppraisalPeriodSerializer(periods, many=True)
        return Response(serializer.data)

class AppraisalListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        period_id = request.query_params.get('period')
        appraisals = get_appraisals_for_employee(request.user.extrainfo, period_id)
        serializer = PerformanceAppraisalSerializer(appraisals, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PerformanceAppraisalSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(employee=request.user.extrainfo)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ==================== TRAINING VIEWS ====================

class TrainingProgramListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        programs = get_available_training_programs()
        serializer = TrainingProgramSerializer(programs, many=True)
        return Response(serializer.data)

class TrainingNominationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        nominations = get_nominations_for_employee(request.user.extrainfo)
        serializer = TrainingNominationSerializer(nominations, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = TrainingNominationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(employee=request.user.extrainfo, nominated_by=request.user.extrainfo)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ==================== PROMOTION VIEWS ====================

class PromotionApplicationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        applications = get_promotion_applications(request.user.extrainfo)
        serializer = PromotionApplicationSerializer(applications, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PromotionApplicationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(employee=request.user.extrainfo)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ==================== FACULTY WORKLOAD VIEWS ====================

class FacultyWorkloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        semester = request.query_params.get('semester')
        year = request.query_params.get('year')
        workloads = get_faculty_workload(request.user.extrainfo, semester, year)
        serializer = FacultyWorkloadSerializer(workloads, many=True)
        return Response(serializer.data)

    def post(self, request):
        workload = calculate_faculty_workload(
            request.user.extra_info,
            request.data.get('semester'),
            request.data.get('year')
        )
        serializer = FacultyWorkloadSerializer(workload)
        return Response(serializer.data)
    
from ..models import LTCApplicationNew, CPDAAdvanceNew, CPDAReimbursementNew, AppraisalFormNew
from ..services import apply_ltc, approve_ltc, reject_ltc, apply_cpda_advance, approve_cpda_advance, reject_cpda_advance, apply_cpda_reimbursement, approve_cpda_reimbursement, reject_cpda_reimbursement, submit_appraisal, review_appraisal
from ..selectors import get_ltc_applications, get_cpda_advances, get_cpda_reimbursements, get_appraisal_forms
from .serializers import LTCApplicationSerializer, CPDAAdvanceSerializer, CPDAReimbursementSerializer, AppraisalFormSerializer

# ==================== LTC VIEWS ====================

class LTCApplicationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        is_hr_staff = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='hr',
        ).exists() or (
            request.user.extrainfo.user_type == 'staff'
            and request.user.extrainfo.department
            and request.user.extrainfo.department.name == 'HR'
        )
        is_accountant = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='accountant',
        ).exists()

        if is_hr_staff:
            ltcs = LTCApplicationNew.objects.filter(approval_status__in=['PENDING', 'FORWARDED'])
        elif is_accountant:
            ltcs = LTCApplicationNew.objects.filter(
                approval_status='FORWARDED',
                accountant_status__iexact='PENDING',
            )
        else:
            ltcs = get_ltc_applications(request.user.extrainfo)
        serializer = LTCApplicationSerializer(ltcs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = LTCApplicationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(employee=request.user.extrainfo)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LTCApplicationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        ltc = get_object_or_404(LTCApplicationNew, pk=pk)
        serializer = LTCApplicationSerializer(ltc)
        return Response(serializer.data)

    def put(self, request, pk):
        ltc = get_object_or_404(LTCApplicationNew, pk=pk)
        if ltc.employee != request.user.extrainfo:
            return Response({'error': 'Not authorized'}, status=403)
        serializer = LTCApplicationSerializer(ltc, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

class LTCApplicationDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        ltc = get_object_or_404(LTCApplicationNew, pk=pk)
        if ltc.employee != request.user.extrainfo and not request.user.is_staff:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        lines = [
            f"LTC Application #{ltc.id}",
            "",
            f"Employee: {ltc.employee_name}",
            f"Employee ID: {ltc.employee.id}",
            f"Department: {ltc.department}",
            f"Designation: {ltc.designation}",
            "",
            f"Block Year: {ltc.ltc_block_year}",
            f"Travel Start: {ltc.travel_start_date}",
            f"Travel End: {ltc.travel_end_date}",
            f"Destination: {ltc.destination}",
            f"Purpose: {ltc.purpose_of_travel}",
            "",
            f"Approval Status: {ltc.approval_status}",
            f"Applied Date: {ltc.applied_date}",
        ]

        content = "\n".join(lines)
        response = HttpResponse(content, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="ltc-application-{ltc.id}.txt"'
        return response

class LTCApplicationWithdrawView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        ltc = get_object_or_404(LTCApplicationNew, pk=pk)
        if ltc.employee != request.user.extrainfo:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        if ltc.approval_status != 'PENDING':
            return Response({'error': 'Only pending requests can be withdrawn.'}, status=status.HTTP_400_BAD_REQUEST)

        ltc.approval_status = 'WITHDRAWN'
        ltc.remarks = (request.data.get('remarks') or '').strip()
        ltc.save(update_fields=['approval_status', 'remarks'])
        serializer = LTCApplicationSerializer(ltc)
        return Response(serializer.data)

class LTCApproveRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, decision):
        ltc = get_object_or_404(LTCApplicationNew, pk=pk)
        remarks = request.data.get('remarks', '')
        decision = (decision or '').lower()
        if decision not in ['approve', 'reject', 'forward']:
            return Response({'error': 'Invalid decision'}, status=status.HTTP_400_BAD_REQUEST)

        if decision == 'approve':
            ltc.approval_status = 'APPROVED'
            ltc.accountant_status = 'APPROVED'
        elif decision == 'forward':
            ltc.approval_status = 'FORWARDED'
            ltc.verified_by_hr = True
            ltc.accountant_status = 'PENDING'
        else:
            ltc.approval_status = 'REJECTED'
            ltc.accountant_status = 'REJECTED'

        ltc.remarks = remarks
        ltc.save(update_fields=['approval_status', 'remarks', 'verified_by_hr', 'accountant_status'])

        serializer = LTCApplicationSerializer(ltc)
        return Response(serializer.data)

# ==================== CPDA ADVANCE VIEWS ====================

class CPDAAdvanceListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        is_hr_staff = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='hr',
        ).exists() or (
            request.user.extrainfo.user_type == 'staff'
            and request.user.extrainfo.department
            and request.user.extrainfo.department.name == 'HR'
        )
        is_accountant = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='accountant',
        ).exists()
        is_director = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='director',
        ).exists()

        if is_director:
            advances = CPDAAdvanceNew.objects.filter(
                approval_status='FORWARDED',
                accountant_processing_status__iexact='DIRECTOR_REVIEW',
            )
        elif is_hr_staff:
            advances = CPDAAdvanceNew.objects.filter(approval_status='PENDING')
        elif is_accountant:
            advances = CPDAAdvanceNew.objects.filter(
                approval_status='FORWARDED',
                accountant_processing_status__in=['PENDING', 'DIRECTOR_APPROVED'],
            )
        else:
            advances = get_cpda_advances(request.user.extrainfo)
        serializer = CPDAAdvanceSerializer(advances, many=True)
        return Response(serializer.data)
    def post(self, request):
        serializer = CPDAAdvanceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(employee=request.user.extrainfo)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CPDAAdvanceDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        cpda = get_object_or_404(CPDAAdvanceNew, pk=pk)
        serializer = CPDAAdvanceSerializer(cpda)
        return Response(serializer.data)

class CPDAAdvanceDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        cpda = get_object_or_404(CPDAAdvanceNew, pk=pk)
        if cpda.employee != request.user.extrainfo and not request.user.is_staff:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        lines = [
            f"CPDA Advance #{cpda.id}",
            "",
            f"Employee: {cpda.employee_name}",
            f"Employee ID: {cpda.employee.id}",
            f"Department: {cpda.department}",
            f"Designation: {cpda.designation}",
            "",
            f"Event Name: {cpda.event_name}",
            f"Event Type: {cpda.event_type}",
            f"Start Date: {cpda.start_date}",
            f"End Date: {cpda.end_date}",
            f"Total Amount: {cpda.total_amount}",
            "",
            f"Approval Status: {cpda.approval_status}",
            f"Applied Date: {cpda.applied_date}",
        ]

        content = "\n".join(lines)
        response = HttpResponse(content, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="cpda-advance-{cpda.id}.txt"'
        return response

class CPDAAdvanceWithdrawView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        cpda = get_object_or_404(CPDAAdvanceNew, pk=pk)
        if cpda.employee != request.user.extrainfo:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        if cpda.approval_status != 'PENDING':
            return Response({'error': 'Only pending requests can be withdrawn.'}, status=status.HTTP_400_BAD_REQUEST)

        cpda.approval_status = 'WITHDRAWN'
        cpda.remarks = (request.data.get('remarks') or '').strip()
        cpda.save(update_fields=['approval_status', 'remarks'])
        serializer = CPDAAdvanceSerializer(cpda)
        return Response(serializer.data)

class CPDAAdvanceApproveRejectView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk, decision):
        cpda = get_object_or_404(CPDAAdvanceNew, pk=pk)
        remarks = request.data.get('remarks', '')
        decision = (decision or '').lower()
        if decision not in ['approve', 'reject', 'forward-accountant', 'forward-director']:
            return Response({'error': 'Invalid decision'}, status=status.HTTP_400_BAD_REQUEST)

        if decision == 'forward-accountant':
            cpda.approval_status = 'FORWARDED'
            cpda.verified_by_hr = True
            cpda.accountant_processing_status = 'PENDING'
        elif decision == 'forward-director':
            cpda.approval_status = 'FORWARDED'
            cpda.accountant_processing_status = 'DIRECTOR_REVIEW'
        elif decision == 'approve':
            if cpda.accountant_processing_status == 'DIRECTOR_REVIEW':
                cpda.accountant_processing_status = 'DIRECTOR_APPROVED'
                cpda.approval_status = 'FORWARDED'
            else:
                cpda.approval_status = 'APPROVED'
                cpda.accountant_processing_status = 'APPROVED'
        else:
            cpda.approval_status = 'REJECTED'
            cpda.accountant_processing_status = 'REJECTED'
        cpda.remarks = remarks
        cpda.save(update_fields=['approval_status', 'remarks', 'verified_by_hr', 'accountant_processing_status'])
        serializer = CPDAAdvanceSerializer(cpda)
        return Response(serializer.data)

# ==================== CPDA REIMBURSEMENT VIEWS ====================

class CPDAReimbursementListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        reims = get_cpda_reimbursements(request.user.extrainfo)
        serializer = CPDAReimbursementSerializer(reims, many=True)
        return Response(serializer.data)
    def post(self, request):
        serializer = CPDAReimbursementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(employee=request.user.extrainfo)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CPDAReimbursementDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        reim = get_object_or_404(CPDAReimbursementNew, pk=pk)
        serializer = CPDAReimbursementSerializer(reim)
        return Response(serializer.data)

class CPDAReimbursementApproveRejectView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk, decision):
        reim = get_object_or_404(CPDAReimbursementNew, pk=pk)
        remarks = request.data.get('remarks', '')
        if decision == 'approve':
            reim = approve_cpda_reimbursement(reim, request.user.extrainfo, remarks)
        else:
            reim = reject_cpda_reimbursement(reim, request.user.extrainfo, remarks)
        serializer = CPDAReimbursementSerializer(reim)
        return Response(serializer.data)

# ==================== APPRAISAL FORM VIEWS ====================

class AppraisalFormListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        is_hr_staff = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='hr',
        ).exists() or (
            request.user.extrainfo.user_type == 'staff'
            and request.user.extrainfo.department
            and request.user.extrainfo.department.name == 'HR'
        )
        is_hod = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='hod',
        ).exists()
        is_director = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='director',
        ).exists()

        if is_hr_staff:
            appraisals = AppraisalFormNew.objects.all().order_by('-submitted_at')
        elif is_director:
            appraisals = AppraisalFormNew.objects.filter(
                assigned_reviewer_role__iexact='DIRECTOR',
            ).filter(
                Q(assigned_reviewer__isnull=True)
                | Q(assigned_reviewer=request.user.extrainfo)
            ).filter(
                status__in=['PENDING', 'REVIEWED']
            ).order_by('-submitted_at')
        elif is_hod:
            appraisals = AppraisalFormNew.objects.filter(
                assigned_reviewer_role__iexact='HOD',
                department=request.user.extrainfo.department.name,
            ).filter(
                Q(assigned_reviewer__isnull=True)
                | Q(assigned_reviewer=request.user.extrainfo)
            ).filter(
                status='PENDING'
            ).order_by('-submitted_at')
        else:
            appraisals = get_appraisal_forms(request.user.extrainfo)
        serializer = AppraisalFormSerializer(appraisals, many=True)
        return Response(serializer.data)
    def post(self, request):
        serializer = AppraisalFormSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(employee=request.user.extrainfo)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AppraisalFormDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        appraisal = get_object_or_404(AppraisalFormNew, pk=pk)
        serializer = AppraisalFormSerializer(appraisal)
        return Response(serializer.data)

class AppraisalFormDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        appraisal = get_object_or_404(AppraisalFormNew, pk=pk)
        if appraisal.employee != request.user.extrainfo and not request.user.is_staff:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        lines = [
            f"Appraisal Form #{appraisal.id}",
            "",
            f"Employee: {appraisal.employee_name}",
            f"Employee ID: {appraisal.employee.id}",
            f"Department: {appraisal.department}",
            f"Designation: {appraisal.designation}",
            "",
            f"Appraisal Year: {appraisal.appraisal_year}",
            f"Status: {appraisal.status}",
            f"Submitted At: {appraisal.submitted_at}",
        ]

        content = "\n".join(lines)
        response = HttpResponse(content, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="appraisal-{appraisal.id}.txt"'
        return response

class AppraisalReviewView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        appraisal = get_object_or_404(AppraisalFormNew, pk=pk)
        action = (request.data.get('action') or 'review').lower()
        remarks = request.data.get('remarks', '')
        rating = request.data.get('rating', '')

        is_hod = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='hod',
        ).exists()
        is_director = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='director',
        ).exists()
        if is_hod and appraisal.assigned_reviewer_role.upper() != 'HOD':
            return Response({'error': 'Not assigned to HOD review.'}, status=status.HTTP_403_FORBIDDEN)
        if is_director and appraisal.assigned_reviewer_role.upper() != 'DIRECTOR':
            return Response({'error': 'Not assigned to Director review.'}, status=status.HTTP_403_FORBIDDEN)
        if not (is_hod or is_director):
            return Response({'error': 'Not authorized to review.'}, status=status.HTTP_403_FORBIDDEN)

        appraisal.reviewer_id = str(request.user.extrainfo.id)
        appraisal.reviewer_comments = remarks
        if rating:
            appraisal.rating = str(rating)

        if action == 'approve':
            appraisal.status = 'APPROVED'
            appraisal.assigned_reviewer_role = ''
            appraisal.assigned_reviewer = None
        elif action == 'forward':
            appraisal.status = 'REVIEWED'
            appraisal.assigned_reviewer_role = 'DIRECTOR'
            appraisal.assigned_reviewer = None
        else:
            appraisal.status = 'REVIEWED'

        appraisal.save(update_fields=[
            'reviewer_id',
            'reviewer_comments',
            'rating',
            'status',
            'assigned_reviewer_role',
            'assigned_reviewer',
        ])
        serializer = AppraisalFormSerializer(appraisal)
        return Response(serializer.data)

class AppraisalAssignView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        appraisal = get_object_or_404(AppraisalFormNew, pk=pk)
        is_hr_staff = HoldsDesignation.objects.filter(
            working=request.user,
            designation__name__icontains='hr',
        ).exists() or (
            request.user.extrainfo.user_type == 'staff'
            and request.user.extrainfo.department
            and request.user.extrainfo.department.name == 'HR'
        )
        if not is_hr_staff:
            return Response({'error': 'Not authorized to assign.'}, status=status.HTTP_403_FORBIDDEN)

        role = (request.data.get('role') or '').upper()
        reviewer_id = (request.data.get('reviewer_id') or '').strip()
        if role not in ['HOD', 'DIRECTOR']:
            return Response({'error': 'Role must be HOD or DIRECTOR.'}, status=status.HTTP_400_BAD_REQUEST)
        if appraisal.status != 'PENDING':
            return Response({'error': 'Only pending appraisals can be assigned.'}, status=status.HTTP_400_BAD_REQUEST)

        assigned_reviewer = None
        if reviewer_id:
            assigned_reviewer = ExtraInfo.objects.filter(id=reviewer_id).first()
            if not assigned_reviewer:
                return Response({'error': 'Reviewer not found.'}, status=status.HTTP_400_BAD_REQUEST)

        appraisal.assigned_reviewer_role = role
        appraisal.assigned_reviewer = assigned_reviewer
        appraisal.assigned_by = request.user.extrainfo
        appraisal.assigned_at = timezone.now()
        appraisal.save(update_fields=[
            'assigned_reviewer_role',
            'assigned_reviewer',
            'assigned_by',
            'assigned_at',
        ])
        serializer = AppraisalFormSerializer(appraisal)
        return Response(serializer.data)

