import datetime

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.http import HttpResponse
from django.utils import timezone
from django.core.exceptions import ValidationError
from applications.hr2 import selectors as hr2_selectors
from applications.hr2 import services as hr2_services
from ..services import (
    InsufficientLeaveBalanceError,
    InvalidWorkflowTransitionError,
)
from ..selectors import (
    get_all_employees,
    get_attendance_for_employee,
    get_available_training_programs,
    get_faculty_workload,
    get_nominations_for_employee,
    get_promotion_applications,
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
        employee = hr2_selectors.get_employee_by_id_or_404(employee_id)
        serializer = EmployeeDetailsSerializer(employee)
        return Response(serializer.data)

    def put(self, request, employee_id):
        employee = hr2_selectors.get_employee_by_id_or_404(employee_id)
        serializer = EmployeeDetailsSerializer(employee, data=request.data, partial=True)
        if serializer.is_valid():
            updated = hr2_services.update_instance(employee, serializer.validated_data)
            return Response(EmployeeDetailsSerializer(updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ==================== LEAVE VIEWS ====================

class LeaveApplicationListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        role_flags = hr2_selectors.get_role_flags(request.user)
        leaves = hr2_selectors.get_leave_applications_for_role_view(request.user, role_flags)
        serializer = LeaveApplicationSerializer(leaves, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        serializer = LeaveApplicationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                leave_app = hr2_services.create_leave_application(request.user, serializer.validated_data)
            except ValidationError as exc:
                return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)
            refreshed_serializer = LeaveApplicationSerializer(leave_app, context={'request': request})
            return Response(refreshed_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LeaveApplicationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        leave_app = hr2_selectors.get_leave_application_by_id_or_404(pk)
        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)

    def put(self, request, pk):
        leave_app = hr2_selectors.get_leave_application_by_id_or_404(pk)
        if leave_app.employee != request.user.extrainfo and not request.user.is_staff:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        serializer = LeaveApplicationSerializer(leave_app, data=request.data, partial=True)
        if serializer.is_valid():
            updated = hr2_services.update_leave_application(leave_app, serializer.validated_data)
            return Response(LeaveApplicationSerializer(updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        leave_app = hr2_selectors.get_leave_application_by_id_or_404(pk)
        if leave_app.status != 'PENDING':
            return Response({'error': 'Cannot delete non-pending application'}, status=status.HTTP_400_BAD_REQUEST)
        leave_app.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class LeaveApplicationDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        leave_app = hr2_selectors.get_leave_application_by_id_or_404(pk)
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
        leave_app = hr2_selectors.get_leave_application_by_id_or_404(pk)
        try:
            leave_app = hr2_services.withdraw_leave_application(
                leave_app,
                request.user,
                request.data.get('remarks'),
            )
        except (ValidationError, PermissionError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)

class LeaveApplicationCancelRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        leave_app = hr2_selectors.get_leave_application_by_id_or_404(pk)
        try:
            leave_app = hr2_services.request_leave_cancellation(
                leave_app,
                request.user,
                request.data.get('reason'),
            )
        except (ValidationError, PermissionError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)

class LeaveApplicationCancelDecisionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, decision):
        leave_app = hr2_selectors.get_leave_application_by_id_or_404(pk)
        try:
            leave_app = hr2_services.decide_leave_cancellation(
                leave_app,
                request.user,
                decision,
                request.data.get('remarks'),
            )
        except (ValidationError, PermissionError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)

class LeaveApplicationExtensionRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        leave_app = hr2_selectors.get_leave_application_by_id_or_404(pk)
        new_end_date_raw = request.data.get('new_end_date')
        if not new_end_date_raw:
            return Response({'error': 'New end date is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            new_end_date = datetime.datetime.strptime(new_end_date_raw, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'New end date must be in YYYY-MM-DD format.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            leave_app = hr2_services.request_leave_extension(
                leave_app,
                request.user,
                new_end_date,
                request.data.get('reason'),
            )
        except (ValidationError, PermissionError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)

class LeaveApplicationExtensionDecisionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, decision):
        leave_app = hr2_selectors.get_leave_application_by_id_or_404(pk)
        try:
            leave_app = hr2_services.decide_leave_extension(
                leave_app,
                request.user,
                decision,
                request.data.get('remarks'),
            )
        except InsufficientLeaveBalanceError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except (ValidationError, PermissionError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)

class LeaveResumptionSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        leave_app = hr2_selectors.get_leave_application_by_id_or_404(pk)
        today = timezone.now().date()
        resumption_date_raw = (request.data.get('resumption_date') or '').strip()
        if resumption_date_raw:
            try:
                resumption_date = datetime.datetime.strptime(resumption_date_raw, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Resumption date must be in YYYY-MM-DD format.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            resumption_date = today
        try:
            leave_app = hr2_services.submit_leave_resumption(
                leave_app,
                request.user,
                resumption_date,
                request.data.get('reason'),
            )
        except (ValidationError, PermissionError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)

class LeaveResumptionDecisionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, decision):
        leave_app = hr2_selectors.get_leave_application_by_id_or_404(pk)
        try:
            leave_app = hr2_services.decide_leave_resumption(
                leave_app,
                request.user,
                decision,
                request.data.get('remarks'),
            )
        except (ValidationError, PermissionError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)

class LeaveBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, employee_id=None):
        if employee_id:
            employee = hr2_selectors.get_employee_by_id_or_404(employee_id)
        else:
            employee = request.user.extrainfo
        balances = hr2_selectors.get_latest_leave_balances_for_employee(employee)
        serializer = LeaveBalanceSerializer(balances, many=True)
        return Response(serializer.data)

class LeaveNomineeDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee = request.user.extrainfo
        leaves = hr2_selectors.get_leave_applications_for_nominee(employee.id)
        serializer = LeaveApplicationSerializer(leaves, many=True)
        return Response(serializer.data)

class LeaveNomineeDecisionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        leave_app = hr2_selectors.get_leave_application_by_id_or_404(pk)
        try:
            leave_app = hr2_services.respond_leave_nominee(
                leave_app,
                request.user,
                request.data.get('action'),
            )
        except (ValidationError, PermissionError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)

class LeaveDocumentRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        leave_app = hr2_selectors.get_leave_application_by_id_or_404(pk)
        try:
            leave_app = hr2_services.request_leave_document(
                leave_app,
                request.user,
                (request.data.get('message') or '').strip(),
            )
        except (ValidationError, PermissionError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)

class LeaveDocumentSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        leave_app = hr2_selectors.get_leave_application_by_id_or_404(pk)
        try:
            leave_app = hr2_services.submit_leave_document(
                leave_app,
                request.user,
                (request.data.get('submission') or '').strip(),
            )
        except (ValidationError, PermissionError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)

class LeaveResponsibilityView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, responsibility_type):
        leave_app = hr2_selectors.get_leave_application_by_id_or_404(pk)
        action = request.data.get('action')
        remarks = request.data.get('remarks', '')
        try:
            if responsibility_type == 'academic':
                leave_app = hr2_services.handle_academic_responsibility(leave_app, request.user.extrainfo, action, remarks)
            else:
                leave_app = hr2_services.handle_administrative_responsibility(leave_app, request.user.extrainfo, action, remarks)
            serializer = LeaveApplicationSerializer(leave_app)
            return Response(serializer.data)
        except (PermissionError, InvalidWorkflowTransitionError) as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

class LeaveApproveRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, decision):
        leave_app = hr2_selectors.get_leave_application_by_id_or_404(pk)
        try:
            leave_app = hr2_services.decide_leave_application(
                leave_app,
                request.user,
                decision,
                request.data.get('remarks', ''),
            )
        except ValidationError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = LeaveApplicationSerializer(leave_app)
        return Response(serializer.data)

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
        serializer = EmployeeAttendanceSerializer(data=request.data)
        if serializer.is_valid():
            attendance = hr2_services.create_attendance(
                request.user.extrainfo,
                serializer.validated_data,
            )
            return Response(EmployeeAttendanceSerializer(attendance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ==================== APPRAISAL VIEWS ====================

class AppraisalPeriodListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        is_active = request.query_params.get('is_active')
        periods = hr2_selectors.get_appraisal_periods(is_active)
        serializer = AppraisalPeriodSerializer(periods, many=True)
        return Response(serializer.data)

class AppraisalListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        period_id = request.query_params.get('period')
        appraisals = hr2_selectors.get_appraisals_for_employee(request.user.extrainfo, period_id)
        serializer = PerformanceAppraisalSerializer(appraisals, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PerformanceAppraisalSerializer(data=request.data)
        if serializer.is_valid():
            appraisal = hr2_services.create_performance_appraisal(
                request.user.extrainfo,
                serializer.validated_data,
            )
            return Response(PerformanceAppraisalSerializer(appraisal).data, status=status.HTTP_201_CREATED)
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
            nomination = hr2_services.create_training_nomination(
                request.user.extrainfo,
                request.user.extrainfo,
                serializer.validated_data,
            )
            return Response(TrainingNominationSerializer(nomination).data, status=status.HTTP_201_CREATED)
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
            promotion = hr2_services.create_promotion_application(
                request.user.extrainfo,
                serializer.validated_data,
            )
            return Response(PromotionApplicationSerializer(promotion).data, status=status.HTTP_201_CREATED)
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
        workload = hr2_services.calculate_faculty_workload(
            request.user.extra_info,
            request.data.get('semester'),
            request.data.get('year')
        )
        serializer = FacultyWorkloadSerializer(workload)
        return Response(serializer.data)
    
from ..selectors import get_cpda_reimbursements
from .serializers import LTCApplicationSerializer, CPDAAdvanceSerializer, CPDAReimbursementSerializer, AppraisalFormSerializer

# ==================== LTC VIEWS ====================

class LTCApplicationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role_flags = hr2_selectors.get_role_flags(request.user)
        ltcs = hr2_selectors.get_ltc_applications_for_role_view(request.user, role_flags)
        serializer = LTCApplicationSerializer(ltcs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = LTCApplicationSerializer(data=request.data)
        if serializer.is_valid():
            ltc = hr2_services.create_ltc_application(
                request.user.extrainfo,
                serializer.validated_data,
            )
            return Response(LTCApplicationSerializer(ltc).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LTCApplicationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        ltc = hr2_selectors.get_ltc_application_by_id_or_404(pk)
        serializer = LTCApplicationSerializer(ltc)
        return Response(serializer.data)

    def put(self, request, pk):
        ltc = hr2_selectors.get_ltc_application_by_id_or_404(pk)
        if ltc.employee != request.user.extrainfo:
            return Response({'error': 'Not authorized'}, status=403)
        serializer = LTCApplicationSerializer(ltc, data=request.data, partial=True)
        if serializer.is_valid():
            updated = hr2_services.update_ltc_application(ltc, serializer.validated_data)
            return Response(LTCApplicationSerializer(updated).data)
        return Response(serializer.errors, status=400)

class LTCApplicationDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        ltc = hr2_selectors.get_ltc_application_by_id_or_404(pk)
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
        ltc = hr2_selectors.get_ltc_application_by_id_or_404(pk)
        try:
            ltc = hr2_services.withdraw_ltc_application(
                ltc,
                request.user,
                request.data.get('remarks'),
            )
        except (ValidationError, PermissionError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = LTCApplicationSerializer(ltc)
        return Response(serializer.data)

class LTCApproveRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, decision):
        ltc = hr2_selectors.get_ltc_application_by_id_or_404(pk)
        try:
            ltc = hr2_services.decide_ltc_application(
                ltc,
                decision,
                request.data.get('remarks', ''),
            )
        except ValidationError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = LTCApplicationSerializer(ltc)
        return Response(serializer.data)

# ==================== CPDA ADVANCE VIEWS ====================

class CPDAAdvanceListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        role_flags = hr2_selectors.get_role_flags(request.user)
        advances = hr2_selectors.get_cpda_advances_for_role_view(request.user, role_flags)
        serializer = CPDAAdvanceSerializer(advances, many=True)
        return Response(serializer.data)
    def post(self, request):
        serializer = CPDAAdvanceSerializer(data=request.data)
        if serializer.is_valid():
            cpda = hr2_services.create_cpda_advance(
                request.user.extrainfo,
                serializer.validated_data,
            )
            return Response(CPDAAdvanceSerializer(cpda).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CPDAAdvanceDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        cpda = hr2_selectors.get_cpda_advance_by_id_or_404(pk)
        serializer = CPDAAdvanceSerializer(cpda)
        return Response(serializer.data)

class CPDAAdvanceDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        cpda = hr2_selectors.get_cpda_advance_by_id_or_404(pk)
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
        cpda = hr2_selectors.get_cpda_advance_by_id_or_404(pk)
        try:
            cpda = hr2_services.withdraw_cpda_advance(
                cpda,
                request.user,
                request.data.get('remarks'),
            )
        except (ValidationError, PermissionError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = CPDAAdvanceSerializer(cpda)
        return Response(serializer.data)

class CPDAAdvanceApproveRejectView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk, decision):
        cpda = hr2_selectors.get_cpda_advance_by_id_or_404(pk)
        try:
            cpda = hr2_services.decide_cpda_advance(
                cpda,
                request.user,
                decision,
                request.data.get('remarks', ''),
            )
        except (ValidationError, PermissionError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
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
            reimbursement = hr2_services.create_cpda_reimbursement(
                request.user.extrainfo,
                serializer.validated_data,
            )
            return Response(CPDAReimbursementSerializer(reimbursement).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CPDAReimbursementDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        reim = hr2_selectors.get_cpda_reimbursement_by_id_or_404(pk)
        serializer = CPDAReimbursementSerializer(reim)
        return Response(serializer.data)

class CPDAReimbursementApproveRejectView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk, decision):
        reim = hr2_selectors.get_cpda_reimbursement_by_id_or_404(pk)
        try:
            reim = hr2_services.decide_cpda_reimbursement(
                reim,
                decision,
                request.user.extrainfo,
                request.data.get('remarks', ''),
            )
        except ValidationError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = CPDAReimbursementSerializer(reim)
        return Response(serializer.data)

# ==================== APPRAISAL FORM VIEWS ====================

class AppraisalFormListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        role_flags = hr2_selectors.get_role_flags(request.user)
        appraisals = hr2_selectors.get_appraisal_forms_for_role_view(request.user, role_flags)
        serializer = AppraisalFormSerializer(appraisals, many=True)
        return Response(serializer.data)
    def post(self, request):
        serializer = AppraisalFormSerializer(data=request.data)
        if serializer.is_valid():
            appraisal = hr2_services.create_appraisal_form(
                request.user.extrainfo,
                serializer.validated_data,
            )
            return Response(AppraisalFormSerializer(appraisal).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AppraisalFormDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        appraisal = hr2_selectors.get_appraisal_form_by_id_or_404(pk)
        serializer = AppraisalFormSerializer(appraisal)
        return Response(serializer.data)

class AppraisalFormDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        appraisal = hr2_selectors.get_appraisal_form_by_id_or_404(pk)
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
        appraisal = hr2_selectors.get_appraisal_form_by_id_or_404(pk)
        action = (request.data.get('action') or 'review').lower()
        try:
            appraisal = hr2_services.review_appraisal_form(
                appraisal,
                request.user,
                action,
                request.data.get('remarks', ''),
                request.data.get('rating', ''),
            )
        except (ValidationError, PermissionError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = AppraisalFormSerializer(appraisal)
        return Response(serializer.data)

class AppraisalAssignView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        appraisal = hr2_selectors.get_appraisal_form_by_id_or_404(pk)
        role = (request.data.get('role') or '').upper()
        reviewer_id = (request.data.get('reviewer_id') or '').strip()
        try:
            appraisal = hr2_services.assign_appraisal_reviewer(
                appraisal,
                request.user,
                role,
                reviewer_id,
            )
        except (ValidationError, PermissionError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = AppraisalFormSerializer(appraisal)
        return Response(serializer.data)

