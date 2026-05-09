from django.http import Http404
"""
Health Center API Views
=======================
API endpoints for PHC module.

Architecture:
  - Thin endpoints: delegate to selectors (reads) and services (writes)
  - RBAC permissions checked for each endpoint
  - Proper HTTP status codes and error handling
"""

from datetime import date, timedelta
import logging
from django.shortcuts import get_object_or_404
from django.db import transaction

logger = logging.getLogger(__name__)
from django.utils import timezone
from django.contrib.auth.models import User
from django.http import FileResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000

from applications.globals.models import ExtraInfo
from .. import selectors, services
from ..decorators import (
    require_patient, require_compounder, require_employee, require_accounts_staff,
    require_doctor, require_patient_or_compounder, require_any_role,
    is_patient, is_compounder, is_employee, is_accounts_staff, is_doctor, is_phc_staff, is_auditor, check_permission
)
from ..models import (
    Doctor, Appointment, Prescription, ReimbursementClaim, 
    InventoryRequisition, Medicine, DoctorAttendance, Stock, Expiry,
    Consultation, PrescribedMedicine, ComplaintV2, HospitalAdmit,
    AmbulanceRecordsV2, AmbulanceLog, HealthAnnouncement,
)
from applications.globals.models import ExtraInfo
from .serializers import (
    DoctorAvailabilitySerializer, AppointmentSerializer, AppointmentCreateSerializer,
    PrescriptionSerializer, PrescriptionCreateSerializer, PrescriptionUpdateSerializer,
    ConsultationSerializer,
    ComplaintSerializer, ComplaintCreateSerializer, ComplaintUpdateSerializer,
    ComplaintRespondSerializer,
    HospitalAdmitSerializer, HospitalAdmitCreateSerializer, HospitalAdmitUpdateSerializer,
    AmbulanceRecordsSerializer, AmbulanceRecordsCreateSerializer, AmbulanceRecordsUpdateSerializer,
    AmbulanceLogSerializer, AmbulanceLogCreateSerializer,
    ReimbursementClaimSerializer, ReimbursementClaimCreateSerializer, ReimbursementClaimUpdateSerializer,
    ReimbursementClaimForwardSerializer, ReimbursementClaimApproveSerializer, ReimbursementClaimRejectSerializer,
    ClaimDocumentUploadSerializer, DashboardStatsSerializer, PatientSummarySerializer,
    InventoryRequisitionSerializer, InventoryRequisitionCreateSerializer, FulfillRequisitionSerializer,
    LowStockAlertSerializer, AuditLogSerializer, ProcessClaimSerializer,
    HealthProfileSerializer, MedicineSerializer, DoctorSerializer,
    DoctorScheduleSerializer, DoctorAttendanceSerializer, ExpirySerializer, StockSerializer,
    StockCreateSerializer,
    ExpiryCreateSerializer, ExpiryUpdateSerializer, ExpiryReturnSerializer,
    HealthAnnouncementSerializer, HealthAnnouncementCreateSerializer,
)


# ===========================================================================
# ── PERMISSIONS ──────────────────────────────────────────────────────────
# ===========================================================================
# Permission check functions are imported from decorators.py
# Task 21: All RBAC and permission decorators centralized in decorators.py
# 
# Available permission checks:
#   - is_patient(user): Check if user is STUDENT/FACULTY/STAFF
#   - is_compounder(user): Check if user is PHC staff (ADMIN)
#   - is_employee(user): Check if user is FACULTY/STAFF
#   - is_accounts_staff(user): Check if user is accounts staff (ADMIN)
#   - is_doctor(user): Check if user is a doctor
#
# Available decorators:
#   @require_patient: Ensure patient role
#   @require_compounder: Ensure compounder role
#   @require_employee: Ensure employee role
#   @require_accounts_staff: Ensure accounts staff role
#   @require_doctor: Ensure doctor role
#   @require_patient_or_compounder: Either patient or compounder
#   @require_any_role('patient', 'compounder', ...): Any of multiple roles


# ===========================================================================
# ── DOCTOR AVAILABILITY VIEW ─ PHC-UC-01 ──────────────────────────────────
# ===========================================================================

class DoctorAvailabilityView(APIView):
    """
    View doctor schedule and real-time availability.
    PHC-UC-01: View Doctor Schedule & Availability
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, doctor_id=None):
        """Get doctor availability (optionally specific doctor)"""
        try:
            if doctor_id:
                # Specific doctor
                doctor = Doctor.objects.get(id=doctor_id, is_active=True)
                schedule = selectors.get_doctor_schedule(doctor_id)
                doctor_obj = doctor
                doctor_obj.schedules = schedule
                doctor_obj.todays_attendance = selectors.get_doctor_availability_for_today(doctor_id)
                
                serializer = DoctorAvailabilitySerializer(doctor_obj)
                return Response(serializer.data)
            else:
                # All doctors
                doctors = selectors.get_all_doctors_with_availability()
                serializer = DoctorAvailabilitySerializer(doctors, many=True)
                return Response(serializer.data)
        except Doctor.DoesNotExist:
            return Response({'detail': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ===========================================================================
# ── APPOINTMENT VIEW ─ PHC-UC-04 ─────────────────────────────────────────
# ===========================================================================

class AppointmentView(APIView):
    """
    List, create, and manage appointments.
    PHC-UC-04: Book appointments
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get patient's appointments"""
        if not is_patient(request.user):
            return Response(
                {'detail': 'Only patients can view their appointments'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        patient_id = ExtraInfo.objects.get(user=request.user).id
        status_filter = request.query_params.get('status', None)
        
        appointments = selectors.get_patient_appointments(patient_id, status=status_filter)
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create new appointment"""
        if not is_patient(request.user):
            return Response(
                {'detail': 'Only patients can book appointments'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            patient_id = ExtraInfo.objects.get(user=request.user).id
            serializer = AppointmentCreateSerializer(data=request.data)
            
            if serializer.is_valid():
                appointment = services.create_appointment(
                    patient_id=patient_id,
                    doctor_id=serializer.validated_data['doctor'].id,
                    appointment_date=serializer.validated_data['appointment_date'],
                    appointment_time=serializer.validated_data['appointment_time'],
                    appointment_type=serializer.validated_data['appointment_type'],
                    chief_complaint=serializer.validated_data.get('chief_complaint', ''),
                )
                return Response(
                    AppointmentSerializer(appointment).data,
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    def patch(self, request, pk=None):
        """Cancel appointment"""
        if not is_patient(request.user):
            return Response(
                {'detail': 'Only patients can cancel their appointments'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            patient_id = ExtraInfo.objects.get(user=request.user).id
            appointment = Appointment.objects.get(id=pk, patient_id=patient_id)
            
            serializer = ProcessClaimSerializer(data=request.data)
            if serializer.is_valid():
                reason = serializer.validated_data.get('remarks', 'No reason provided')
                appointment = services.cancel_appointment(pk, reason)
                return Response(AppointmentSerializer(appointment).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Appointment.DoesNotExist:
            return Response({'detail': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ===========================================================================
# ── MEDICAL HISTORY VIEW ─ PHC-UC-02 ─────────────────────────────────────
# ===========================================================================

class MedicalHistoryView(APIView):
    """
    View patient's medical history and prescriptions.
    PHC-UC-02: View Medical History & Prescriptions
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get patient's medical history"""
        if not is_patient(request.user):
            return Response(
                {'detail': 'Only patients can view their medical history'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        patient_id = ExtraInfo.objects.get(user=request.user).id
        
        # Get consultations (medical visits)
        consultations = selectors.get_patient_medical_history(patient_id)
        
        # Paginate consultations to avoid timeouts
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(consultations, request, view=self)
        
        data = {
            'consultations': [],
            'prescriptions': [],
        }
        
        iterable = page if page is not None else consultations
        for consultation in iterable:
            consultation_data = {
                'id': consultation.id,
                'date': consultation.consultation_date,
                'doctor': f"Dr. {consultation.doctor.doctor_name if consultation.doctor else 'N/A'}",
                'diagnosis': consultation.final_diagnosis,
            }
            if hasattr(consultation, 'prescription') and consultation.prescription:
                consultation_data['prescription'] = PrescriptionSerializer(
                    consultation.prescription
                ).data
            data['consultations'].append(consultation_data)
        
        # Get all prescriptions
        prescriptions = selectors.get_patient_prescriptions(patient_id)
        data['prescriptions'] = PrescriptionSerializer(prescriptions, many=True).data
        
        if page is not None:
            return paginator.get_paginated_response(data)
            
        return Response(data)


# ===========================================================================
# ── REIMBURSEMENT CLAIM VIEW ─ PHC-UC-04, PHC-UC-05 ──────────────────────
# ===========================================================================

class ReimbursementClaimView(APIView):
    """
    View and submit reimbursement claims.
    PHC-UC-04: Apply for Medical Bill Reimbursement
    PHC-UC-05: Track Reimbursement Status
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    def get(self, request, pk=None):
        """Get reimbursement claims"""
        if not is_employee(request.user):
            return Response(
                {'detail': 'Only employees can view their claims'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        patient_id = ExtraInfo.objects.get(user=request.user).id
        
        if pk:
            claim = selectors.get_reimbursement_claim_detail(pk)
            if not claim or claim.patient_id != patient_id:
                return Response({'detail': 'Claim not found'}, status=status.HTTP_404_NOT_FOUND)
            return Response(ReimbursementClaimSerializer(claim).data)
        else:
            claims = selectors.get_patient_reimbursement_claims(patient_id)
            return Response(ReimbursementClaimSerializer(claims, many=True).data)
    
    @transaction.atomic
    def post(self, request):
        """Submit new reimbursement claim"""
        if not is_employee(request.user):
            return Response(
                {'detail': 'Only employees can submit claims'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            patient_id = ExtraInfo.objects.get(user=request.user).id
            
            serializer = ReimbursementClaimCreateSerializer(data=request.data)
            if serializer.is_valid():
                prescription = serializer.validated_data.get('prescription')
                claim = services.submit_reimbursement_claim(
                    patient_id=patient_id,
                    prescription_id=prescription.id if prescription else None,
                    claim_amount=serializer.validated_data['claim_amount'],
                    expense_date=serializer.validated_data['expense_date'],
                    description=serializer.validated_data['description'],
                )
                return Response(
                    ReimbursementClaimSerializer(claim).data,
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except services.InvalidReimbursementSubmission as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class ClaimDocumentUploadView(APIView):
    """Upload documents to reimbursement claim - PHC-UC-04"""
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request, claim_id):
        """Upload document (optional — storage may not be configured)"""
        try:
            patient_id = ExtraInfo.objects.get(user=request.user).id
            claim = ReimbursementClaim.objects.get(id=claim_id, patient_id=patient_id)
            
            serializer = ClaimDocumentUploadSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(claim=claim)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ReimbursementClaim.DoesNotExist:
            return Response({'detail': 'Claim not found'}, status=status.HTTP_404_NOT_FOUND)
        except (OSError, IOError) as e:
            # File storage is not accessible (e.g., media directory doesn't exist or no write permission)
            return Response(
                {'detail': 'File storage is currently unavailable. The document could not be saved. '
                           'Please contact the system administrator to configure storage. '
                           f'Error: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ===========================================================================
# ── HEALTH PROFILE VIEW ──────────────────────────────────────────────────
# ===========================================================================

class HealthProfileView(APIView):
    """Get/update patient health profile"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get health profile"""
        if not is_patient(request.user):
            return Response(
                {'detail': 'Only patients can view their health profile'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        patient_id = ExtraInfo.objects.get(user=request.user).id
        profile = selectors.get_patient_health_profile(patient_id)
        
        if not profile:
            return Response({'detail': 'No health profile found'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(HealthProfileSerializer(profile).data)
    
    def put(self, request):
        """Update health profile"""
        if not is_patient(request.user):
            return Response(
                {'detail': 'Only patients can update their health profile'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        patient_id = ExtraInfo.objects.get(user=request.user).id
        
        try:
            profile = services.create_or_update_health_profile(patient_id, request.data)
            return Response(HealthProfileSerializer(profile).data)
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ===========================================================================
# ── STAFF: CLAIMS PROCESSING VIEW ─ PHC-UC-15 ────────────────────────────
# ===========================================================================

class StaffClaimProcessingView(APIView):
    """
    PHC Staff process reimbursement claims.
    PHC-UC-15: Process Reimbursement Claim
    PHC-WF-01: Workflow stages
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get pending claims for PHC staff"""
        if not is_phc_staff(request):
            return Response(
                {'detail': 'Only PHC staff can process claims'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        claims = ReimbursementClaim.objects.select_related(
            'patient__user', 'prescription__doctor'
        ).prefetch_related('documents').order_by('-submission_date')
        return Response(ReimbursementClaimSerializer(claims, many=True).data)
    
    def patch(self, request, claim_id):
        """Process claim (approve/reject)"""
        if not is_phc_staff(request):
            return Response(
                {'detail': 'Only PHC staff can process claims'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            staff_id = ExtraInfo.objects.get(user=request.user).id
            
            serializer = ProcessClaimSerializer(data=request.data)
            if serializer.is_valid():
                approved = serializer.validated_data['decision'] == 'APPROVE'
                remarks = serializer.validated_data.get('remarks', '')
                
                claim = ReimbursementClaim.objects.get(id=claim_id)
                if claim.status == 'SUBMITTED':
                    claim = services.process_claim_phc_stage(claim_id, staff_id, approved, remarks)
                elif claim.status == 'ACCOUNTS_VERIFICATION':
                    claim = services.process_claim_accounts_stage(claim_id, staff_id, approved, remarks)
                else:
                    return Response({'detail': f'Cannot process claim in status {claim.status}'}, status=status.HTTP_400_BAD_REQUEST)
                    
                return Response(ReimbursementClaimSerializer(claim).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ReimbursementClaim.DoesNotExist:
            return Response({'detail': 'Claim not found'}, status=status.HTTP_404_NOT_FOUND)
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ===========================================================================
# ── TASK 17: REIMBURSEMENT CRUD ENDPOINTS (EMPLOYEE) ────────────────────
# ===========================================================================

class ReimbursementView(APIView):
    """
    Employee reimbursement claims management (Task 17)
    
    Endpoints:
      POST   /reimbursement/                  - Employee submits claim
      GET    /reimbursement/                  - List own claims
      GET    /reimbursement/{id}/             - Get own claim detail
      PATCH  /reimbursement/{id}/             - Update own claim (if status=submitted)
      DELETE /reimbursement/{id}/             - Delete own claim (if status=submitted)
    
    Critical Validations:
      - 90-day expense window enforced in POST
      - Employee role validation
      - Ownership validation for GET/PATCH/DELETE
      - Status check for PATCH/DELETE (only allowed if submitted)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, claim_id=None):
        """GET: List own claims or get specific claim"""
        # Employee role check
        if not is_employee(request.user):
            return Response(
                {'detail': 'Only employees can view claims'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            patient_id = ExtraInfo.objects.get(user=request.user).id
            
            # Get specific claim
            if claim_id:
                claim = get_object_or_404(ReimbursementClaim, id=claim_id, patient_id=patient_id)
                serializer = ReimbursementClaimSerializer(claim)
                return Response(serializer.data, status=status.HTTP_200_OK)
            
            # List all own claims
            claims = ReimbursementClaim.objects.filter(patient_id=patient_id).order_by('-created_at')
            serializer = ReimbursementClaimSerializer(claims, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except ExtraInfo.DoesNotExist:
            return Response(
                {'detail': 'User information not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def post(self, request):
        """POST: Employee submits reimbursement claim with 90-day validation"""
        # Employee role check
        if not is_employee(request.user):
            return Response(
                {'detail': 'Only employees can submit claims'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            patient_id = ExtraInfo.objects.get(user=request.user).id
            
            # Validate serializer (includes 90-day window check)
            serializer = ReimbursementClaimCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Create claim with validated data
            claim_data = {
                'patient_id': patient_id,
                'claim_amount': serializer.validated_data['claim_amount'],
                'expense_date': serializer.validated_data['expense_date'],
                'description': serializer.validated_data['description'],
                'status': 'SUBMITTED',  # Default status
                'submission_date': date.today(),
            }
            
            # Check if prescription provided
            if 'prescription' in serializer.validated_data and serializer.validated_data['prescription']:
                claim_data['prescription_id'] = serializer.validated_data['prescription'].id
            
            # Create claim
            claim = ReimbursementClaim.objects.create(**claim_data)
            
            response_serializer = ReimbursementClaimSerializer(claim)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        except ExtraInfo.DoesNotExist:
            return Response(
                {'detail': 'User information not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def patch(self, request, claim_id):
        """PATCH: Update own claim (only if status=submitted)"""
        # Employee role check
        if not is_employee(request.user):
            return Response(
                {'detail': 'Only employees can update claims'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            patient_id = ExtraInfo.objects.get(user=request.user).id
            
            # Get claim - must be owned by employee
            claim = get_object_or_404(ReimbursementClaim, id=claim_id, patient_id=patient_id)
            
            # Can only update if status is 'SUBMITTED'
            if claim.status != 'SUBMITTED':
                return Response(
                    {'detail': f'Cannot update claim with status "{claim.status}". Only "SUBMITTED" claims can be updated.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate update serializer
            serializer = ReimbursementClaimUpdateSerializer(data=request.data, partial=True)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Update allowed fields
            for field in ['claim_amount', 'description']:
                if field in serializer.validated_data:
                    setattr(claim, field, serializer.validated_data[field])
            
            claim.save()
            
            response_serializer = ReimbursementClaimSerializer(claim)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        except ExtraInfo.DoesNotExist:
            return Response(
                {'detail': 'User information not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def delete(self, request, claim_id):
        """DELETE: Delete own claim (only if status=submitted)"""
        # Employee role check
        if not is_employee(request.user):
            return Response(
                {'detail': 'Only employees can delete claims'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            patient_id = ExtraInfo.objects.get(user=request.user).id
            
            # Get claim - must be owned by employee
            claim = get_object_or_404(ReimbursementClaim, id=claim_id, patient_id=patient_id)
            
            # Can only delete if status is 'SUBMITTED'
            if claim.status != 'SUBMITTED':
                return Response(
                    {'detail': f'Cannot delete claim with status "{claim.status}". Only "SUBMITTED" claims can be deleted.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Delete claim
            claim.delete()
            
            return Response(
                {'detail': f'Claim {claim_id} deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )
        
        except ExtraInfo.DoesNotExist:
            return Response(
                {'detail': 'User information not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ReimbursementClaim.DoesNotExist:
            return Response(
                {'detail': f'Claim {claim_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ===========================================================================
# ── TASK 17: COMPOUNDER REIMBURSEMENT VIEW (ADMIN ACCESS) ────────────────
# ===========================================================================

class CompounderReimbursementView(APIView):
    """
    Compounder/Admin view all reimbursement claims (Task 17)
    
    Endpoints:
      GET    /compounder/reimbursement/      - List all claims
      GET    /compounder/reimbursement/{id}/ - Get any claim detail
    
    RBAC: Compounder only (read-only access for workflow management)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, claim_id=None):
        """GET: List all claims or get specific claim (Compounder only)"""
        # Compounder/Staff role check
        if not is_phc_staff(request):
            return Response(
                {'detail': 'Only PHC staff can view all claims'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Get specific claim
            if claim_id:
                claim = get_object_or_404(ReimbursementClaim, id=claim_id)
                serializer = ReimbursementClaimSerializer(claim)
                return Response(serializer.data, status=status.HTTP_200_OK)
            
            # List all claims with optional filters
            claims = ReimbursementClaim.objects.all().order_by('-created_at')
            
            # Filter by status
            status_filter = request.query_params.get('status')
            if status_filter:
                claims = claims.filter(status=status_filter)
            
            # Filter by patient_id
            patient_filter = request.query_params.get('patient_id')
            if patient_filter:
                claims = claims.filter(patient_id=patient_filter)
            
            serializer = ReimbursementClaimSerializer(claims, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ===========================================================================
# ── TASK 18: REIMBURSEMENT WORKFLOW ENDPOINTS ─────────────────────────
# ===========================================================================

class CompounderReimbursementWorkflowView(APIView):
    """
    Compounder workflow for reimbursement claims (Task 18)
    
    Endpoint:
      PATCH /compounder/reimbursement/{id}/forward/ - Forward claim to auditor
    
    Workflow state transitions:
      SUBMITTED → PHC_REVIEW (compounder verifies and forwards to auditor)
      Note: Auditor approves or rejects claims. Compounder does NOT approve.
    
    RBAC: Compounder only
    Compounder can:
      ✓ Verify claim details
      ✓ Forward to auditor (with verification notes)
      ✓ Reject during verification (before auditor)
    
    Compounder CANNOT:
      ✗ Approve claims (only auditor can approve)
    """
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def patch(self, request, claim_id):
        """PATCH: Forward claim to auditor for approval
        
        Compounder verifies the claim and forwards it to auditor.
        Auditor decides whether to approve or reject.
        """
        # RBAC: Compounder only - PHC staff (not auditor)
        if not is_phc_staff(request):
            return Response(
                {'detail': 'Only PHC staff (compounder) can forward claims'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Validate request data
            serializer = ReimbursementClaimForwardSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Get compounder ID
            compounder_id = ExtraInfo.objects.get(user=request.user).id
            
            # Call service to transition state
            claim = services.forward_reimbursement_claim(
                claim_id=claim_id,
                compounder_id=compounder_id,
                phc_notes=serializer.validated_data['phc_notes']
            )
            
            response_serializer = ReimbursementClaimSerializer(claim)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        except services.InvalidPrescription as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ExtraInfo.DoesNotExist:
            return Response(
                {'detail': 'User information not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ReimbursementClaim.DoesNotExist:
            return Response(
                {'detail': f'Claim {claim_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class AccountsReimbursementApprovalView(APIView):
    """
    Auditor workflow for reimbursement claims (Task 18)
    
    Endpoints:
      PATCH /accounts/reimbursement/{id}/approve/ - Approve claim
      PATCH /accounts/reimbursement/{id}/reject/ - Reject claim
    
    Workflow state transitions:
      PHC_REVIEW → APPROVED (approve) - Auditor approves, sends to payment
      PHC_REVIEW → REJECTED (reject) - Auditor rejects, sends back to employee
    
    RBAC: Auditor only (checked via is_auditor designation)
    Only auditors can approve/reject. Compounder can only verify and forward.
    """
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def patch(self, request, claim_id, action=None):
        """PATCH: Approve or reject claim based on request path
        
        This method handles both approve and reject by checking the URL path
        Only users with 'auditor' designation can approve/reject
        """
        # RBAC: Auditor only - import here to avoid circular imports
        from .decorators import is_auditor
        
        if not is_auditor(request.user):
            return Response(
                {'detail': 'Only auditors can approve or reject claims. You must have auditor designation.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Get auditor ID
            auditor_id = ExtraInfo.objects.get(user=request.user).id
            
            # Determine action from request path
            path = request.META.get('PATH_INFO', '')
            
            if 'approve' in path:
                # Approve action - Forward claim to approved/payment stage
                serializer = ReimbursementClaimApproveSerializer(data=request.data)
                if not serializer.is_valid():
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
                claim = services.approve_reimbursement_claim(
                    claim_id=claim_id,
                    accounts_staff_id=auditor_id,
                    approval_notes=serializer.validated_data.get('approval_notes', '')
                )
                
                response_serializer = ReimbursementClaimSerializer(claim)
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            
            elif 'reject' in path:
                # Reject action - Send claim back to employee
                serializer = ReimbursementClaimRejectSerializer(data=request.data)
                if not serializer.is_valid():
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
                claim = services.reject_reimbursement_claim(
                    claim_id=claim_id,
                    accounts_staff_id=auditor_id,
                    rejection_reason=serializer.validated_data['rejection_reason']
                )
                
                response_serializer = ReimbursementClaimSerializer(claim)
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            
            else:
                return Response(
                    {'detail': 'Invalid action. Use /approve/ or /reject/'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except services.InvalidPrescription as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ExtraInfo.DoesNotExist:
            return Response(
                {'detail': 'User information not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ReimbursementClaim.DoesNotExist:
            return Response(
                {'detail': f'Claim {claim_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ===========================================================================
# ── STAFF: INVENTORY VIEW ─ PHC-UC-09, PHC-UC-11, PHC-UC-18 ─────────────
# ===========================================================================

class InventoryView(APIView):
    """Manage inventory stock"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get inventory stock list"""
        if not is_phc_staff(request):
            return Response({'detail': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        stock_list = selectors.get_inventory_stock_list()
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(stock_list, request, view=self)
        
        def format_stock(s):
            return {
                'id': s.id,
                'medicine': s.medicine.medicine_name,
                'quantity_remaining': s.quantity_remaining,
                'expiry_date': s.expiry_date,
                'days_until_expiry': (s.expiry_date - date.today()).days,
            }
            
        if page is not None:
            return paginator.get_paginated_response([format_stock(s) for s in page])
            
        return Response({
            'stock': [format_stock(s) for s in stock_list]
        })
    
    def post(self, request):
        """Update stock"""
        if not is_phc_staff(request):
            return Response({'detail': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            medicine_id = request.data.get('medicine_id')
            quantity_change = request.data.get('quantity_change')
            reason = request.data.get('reason', '')
            
            stock = services.update_inventory_stock(medicine_id, quantity_change, reason)
            return Response({
                'medicine': stock.medicine.medicine_name,
                'quantity_remaining': stock.quantity_remaining,
            })
        except services.InvalidStockUpdate as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class LowStockAlertsView(APIView):
    """View low-stock alerts - PHC-UC-18"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get active low-stock alerts"""
        if not is_phc_staff(request):
            return Response({'detail': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        alerts = selectors.get_low_stock_alerts()
        return Response(LowStockAlertSerializer(alerts, many=True).data)


# ===========================================================================
# ── DASHBOARD VIEW ───────────────────────────────────────────────────────
# ===========================================================================

class DashboardView(APIView):
    """Get dashboard statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get dashboard stats based on user role"""
        try:
            patient_id = ExtraInfo.objects.get(user=request.user).id
            
            if is_patient(request.user):
                # Patient dashboard
                summary = selectors.get_patient_summary(patient_id)
                return Response(PatientSummarySerializer(summary).data)
            elif is_phc_staff(request):
                # PHC staff dashboard
                stats = selectors.get_phc_dashboard_stats()
                return Response(DashboardStatsSerializer(stats).data)
            else:
                return Response({'detail': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ===========================================================================
# ── COMPOUNDER: DOCTOR MANAGEMENT ────────────────────────────────────────
# ===========================================================================

class CompounderDoctorView(APIView):
    """
    Doctor CRUD operations for Compounder staff.
    Task 7: Doctor Management Endpoints
    RBAC: Compounder role only
    
    Endpoints:
    - GET /compounder/doctor/ - List all doctors
    - GET /compounder/doctor/{id}/ - Retrieve doctor
    - POST /compounder/doctor/ - Create doctor
    - PATCH /compounder/doctor/{id}/ - Update doctor
    - DELETE /compounder/doctor/{id}/ - Delete doctor
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, doctor_id=None):
        """
        GET: List all doctors (optional: specific doctor by ID)
        
        Role: Compounder staff only
        Query Parameters:
            - active_only: Show only active doctors (default: true)
            - specialization: Filter by specialization (optional)
        
        Response: DoctorSerializer with enhanced filtering
        """
        if not is_phc_staff(request):
            return Response(
                {'detail': 'Unauthorized - Compounder staff access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            if doctor_id:
                # Retrieve specific doctor
                doctor = selectors.get_doctor(doctor_id)
                serializer = DoctorSerializer(doctor)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                # List all doctors with filtering
                active_only = request.query_params.get('active_only', 'true').lower() == 'true'
                specialization = request.query_params.get('specialization')
                
                queryset = Doctor.objects.all()
                
                # Filter by active status
                if active_only:
                    queryset = queryset.filter(is_active=True)
                
                # Filter by specialization if provided
                if specialization:
                    queryset = queryset.filter(specialization__icontains=specialization)
                
                queryset = queryset.order_by('doctor_name')
                serializer = DoctorSerializer(queryset, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
        except Doctor.DoesNotExist:
            return Response(
                {'detail': f'Doctor with ID {doctor_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def post(self, request):
        """
        POST: Create a new doctor
        
        Role: Compounder staff only
        Request body: {doctor_name, specialization, doctor_phone, email}
        Response: DoctorSerializer
        """
        if not is_phc_staff(request):
            return Response(
                {'detail': 'Unauthorized - Compounder staff access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Use serializer for validation
            serializer = DoctorSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(
                    {'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save the doctor
            doctor = serializer.save(is_active=True)
            
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def patch(self, request, doctor_id):
        """
        PATCH: Update doctor information
        
        Role: Compounder staff only
        Request body: {doctor_name, specialization, doctor_phone, email} (partial)
        Response: DoctorSerializer
        """
        if not is_phc_staff(request):
            return Response(
                {'detail': 'Unauthorized - Compounder staff access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            doctor = selectors.get_doctor(doctor_id)
            
            # Use serializer for partial update validation
            serializer = DoctorSerializer(doctor, data=request.data, partial=True)
            
            if not serializer.is_valid():
                return Response(
                    {'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save the updated doctor
            doctor = serializer.save()
            
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        except Doctor.DoesNotExist:
            return Response(
                {'detail': f'Doctor with ID {doctor_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def delete(self, request, doctor_id):
        """
        DELETE: Delete (soft delete) a doctor
        
        Role: Compounder staff only
        Implementation: Sets is_active=False (soft delete)
        Response: 204 No Content or error message
        """
        if not is_phc_staff(request):
            return Response(
                {'detail': 'Unauthorized - Compounder staff access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            doctor = selectors.get_doctor(doctor_id)
            
            # Strict Hard Delete Support
            # Note: models.py has `on_delete=models.SET_NULL` for Consultations and Prescriptions,
            # so firing this hard delete will cleanly drop the doctor while PRESERVING patient medical records!
            doctor.delete()
            
            return Response(
                {'detail': f'Doctor {doctor.doctor_name} successfully removed from the database.'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Doctor.DoesNotExist:
            return Response(
                {'detail': f'Doctor with ID {doctor_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class CompounderDoctorScheduleView(APIView):
    """
    Doctor Schedule CRUD operations for Compounder staff.
    Task 8: Schedule Management Endpoints (Compounder-only)
    RBAC: Compounder role only
    
    Endpoints:
    - GET /compounder/schedule/ - List all schedules
    - GET /compounder/schedule/{id}/ - Retrieve schedule
    - POST /compounder/schedule/ - Create schedule
    - PATCH /compounder/schedule/{id}/ - Update schedule
    - DELETE /compounder/schedule/{id}/ - Delete schedule
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, schedule_id=None):
        """
        GET: List all schedules or retrieve specific schedule
        
        Role: Compounder staff only
        Query params: doctor_id (optional - filter by doctor)
        Response: DoctorScheduleSerializer
        """
        if not is_phc_staff(request):
            return Response(
                {'detail': 'Unauthorized - Compounder staff access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            if schedule_id:
                # Retrieve specific schedule
                from ..models import DoctorSchedule
                schedule = selectors.get_schedule_by_id(schedule_id)
                serializer = DoctorScheduleSerializer(schedule)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                # List schedules (optional filter by doctor)
                from ..models import DoctorSchedule
                doctor_id = request.query_params.get('doctor_id')
                
                if doctor_id:
                    schedules = DoctorSchedule.objects.filter(
                        doctor_id=doctor_id
                    ).order_by('day_of_week', 'start_time')
                else:
                    schedules = DoctorSchedule.objects.all().order_by(
                        'doctor__doctor_name', 'day_of_week', 'start_time'
                    )
                
                serializer = DoctorScheduleSerializer(schedules, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def post(self, request):
        """
        POST: Create a new doctor schedule
        
        Role: Compounder staff only
        Request body: {doctor_id, day_of_week, start_time, end_time, room_number}
        Response: DoctorScheduleSerializer
        """
        if not is_phc_staff(request):
            return Response(
                {'detail': 'Unauthorized - Compounder staff access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Use serializer for validation
            serializer = DoctorScheduleSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(
                    {'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save the schedule
            schedule = serializer.save()
            
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def patch(self, request, schedule_id):
        """
        PATCH: Update schedule information
        
        Role: Compounder staff only
        Request body: {day_of_week, start_time, end_time, room_number} (partial)
        Response: DoctorScheduleSerializer
        """
        if not is_phc_staff(request):
            return Response(
                {'detail': 'Unauthorized - Compounder staff access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            from ..models import DoctorSchedule
            schedule = selectors.get_schedule_by_id(schedule_id)
            
            # Use serializer for partial update validation
            serializer = DoctorScheduleSerializer(schedule, data=request.data, partial=True)
            
            if not serializer.is_valid():
                return Response(
                    {'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save the updated schedule
            schedule = serializer.save()
            
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def delete(self, request, schedule_id):
        """
        DELETE: Delete a doctor schedule
        
        Role: Compounder staff only
        Implementation: Hard delete (schedule entries are ephemeral)
        Response: 204 No Content
        """
        if not is_phc_staff(request):
            return Response(
                {'detail': 'Unauthorized - Compounder staff access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            from ..models import DoctorSchedule
            schedule = selectors.get_schedule_by_id(schedule_id)
            
            doctor_name = schedule.doctor.doctor_name
            day = schedule.get_day_of_week_display()
            
            # Hard delete (schedule entries are recurring and not tied to individual records)
            schedule.delete()
            
            return Response(
                {'detail': f'Schedule for {doctor_name} on {day} successfully deleted'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class PatientScheduleView(APIView):
    """
    Doctor Schedule VIEW for Patients (Read-Only).
    Task 8: Patient Schedule View Endpoint
    RBAC: Any authenticated user (patient read-only)
    
    Endpoints:
    - GET /schedule/ - List all schedules (public read-only)
    - GET /schedule/{doctor_id}/ - View specific doctor's schedule
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, doctor_id=None):
        """
        GET: View doctor schedules (public read-only)
        
        Role: Any authenticated user
        Returns: All active doctor schedules or specific doctor's schedule
        Response: DoctorScheduleSerializer (read-only)
        """
        try:
            from ..models import DoctorSchedule
            
            if doctor_id:
                # Specific doctor's schedule
                doctor = Doctor.objects.get(id=doctor_id, is_active=True)
                schedules = doctor.schedules.filter(is_available=True).order_by(
                    'day_of_week', 'start_time'
                )
                serializer = DoctorScheduleSerializer(schedules, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                # All active doctors' schedules
                schedules = DoctorSchedule.objects.filter(
                    doctor__is_active=True,
                    is_available=True
                ).order_by('doctor__doctor_name', 'day_of_week', 'start_time')
                
                serializer = DoctorScheduleSerializer(schedules, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
        except Doctor.DoesNotExist:
            return Response(
                {'detail': f'Doctor with ID {doctor_id} not found or is inactive'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class CompounderAttendanceView(APIView):
    """
    Doctor Attendance CRUD Endpoints.
    Task 9: Compounder Staff Marks Doctor Present/Absent/On-Break Status
    RBAC: Compounder staff only
    
    Endpoints:
    - GET /compounder/attendance/ - List attendance records
    - GET /compounder/attendance/{id}/ - Retrieve attendance record
    - POST /compounder/attendance/ - Create attendance record
    - PATCH /compounder/attendance/{id}/ - Update attendance record
    - DELETE /compounder/attendance/{id}/ - Delete attendance record
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, attendance_id=None):
        """
        GET: Retrieve attendance record(s)
        
        Role: Compounder staff only
        Returns: Attendance records with doctor details
        Response: DoctorAttendanceSerializer
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can access attendance records'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if attendance_id:
                # Specific attendance record
                attendance = selectors.get_doctor_attendance_by_id(attendance_id)
                serializer = DoctorAttendanceSerializer(attendance)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                # List attendance records with optional filters
                query_date = request.query_params.get('date')
                doctor_id = request.query_params.get('doctor_id')
                
                queryset = DoctorAttendance.objects.all()
                
                if query_date:
                    queryset = queryset.filter(attendance_date=query_date)
                if doctor_id:
                    queryset = queryset.filter(doctor_id=doctor_id)
                
                queryset = queryset.order_by('-attendance_date', 'doctor__doctor_name')
                
                serializer = DoctorAttendanceSerializer(queryset, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
                
        except DoctorAttendance.DoesNotExist:
            return Response(
                {'detail': f'Attendance record with ID {attendance_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def post(self, request):
        """
        POST: Create new attendance record
        
        Role: Compounder staff only
        Body: {doctor: int, attendance_date: date, status: str, notes: str (optional)}
        Response: DoctorAttendanceSerializer
        Status: 201 Created
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can create attendance records'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = DoctorAttendanceSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def patch(self, request, attendance_id=None):
        """
        PATCH: Update attendance record
        
        Role: Compounder staff only
        Body: {status: str, notes: str} (partial update)
        Response: DoctorAttendanceSerializer
        Status: 200 OK
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can update attendance records'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if not attendance_id:
                return Response(
                    {'detail': 'Attendance ID required for update'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            attendance = selectors.get_doctor_attendance_by_id(attendance_id)
            serializer = DoctorAttendanceSerializer(
                attendance,
                data=request.data,
                partial=True
            )
            
            if not serializer.is_valid():
                return Response(
                    {'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except DoctorAttendance.DoesNotExist:
            return Response(
                {'detail': f'Attendance record with ID {attendance_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def delete(self, request, attendance_id=None):
        """
        DELETE: Remove attendance record
        
        Role: Compounder staff only
        Response: Empty (204 No Content)
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can delete attendance records'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if not attendance_id:
                return Response(
                    {'detail': 'Attendance ID required for deletion'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            attendance = selectors.get_doctor_attendance_by_id(attendance_id)
            attendance.delete()
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except DoctorAttendance.DoesNotExist:
            return Response(
                {'detail': f'Attendance record with ID {attendance_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class CompounderMedicineView(APIView):
    """
    Medicine Dropdown Endpoints (for selecting medicines in stock form)
    
    Endpoints:
    - GET /compounder/medicine/ - List all available medicines for stock selection
    - POST /compounder/medicine/ - Create a new medicine (Compounder staff only)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET: List all available medicines for dropdown selection
        
        Role: Compounder staff only
        Returns: List of medicines with id and medicine_name
        Response: MedicineSerializer (simplified)
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can access medicine list'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            medicines = Medicine.objects.all().order_by('medicine_name')
            serializer = MedicineSerializer(medicines, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
                
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def post(self, request):
        """
        POST: Create a new medicine
        
        Role: Compounder staff only
        Request body:
        {
            "medicine_name": "Aspirin",
            "brand_name": "Bayer Aspirin",
            "generic_name": "Acetylsalicylic Acid",
            "manufacturer_name": "Bayer AG",
            "unit": "tablets",
            "pack_size_label": "500mg",
            "reorder_threshold": 10
        }
        
        Response: MedicineSerializer with created medicine data
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can create medicines'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = MedicineSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class CompounderStockView(APIView):
    """
    Stock (Medicine Inventory) CRUD Endpoints.
    Task 10: Compounder Staff Manages Medicine Stock with Expiry Batches
    RBAC: Compounder staff only
    
    Endpoints:
    - GET /compounder/stock/ - List all medicines with total quantities
    - GET /compounder/stock/{id}/ - Retrieve stock with all expiry batches
    - POST /compounder/stock/ - Create stock (auto-creates Expiry batch)
    - PATCH /compounder/stock/{id}/ - Update stock metadata
    - DELETE /compounder/stock/{id}/ - Delete stock (hard delete)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, stock_id=None):
        """
        GET: Retrieve stock record(s)
        
        Role: Compounder staff only
        Returns: Stock with nested Expiry batches (FIFO sorted)
        Response: StockSerializer
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can access stock records'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if stock_id:
                # Specific stock record with all batches
                stock = selectors.get_stock_by_id(stock_id)
                serializer = StockSerializer(stock)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                # List all stocks
                medicine_id = request.query_params.get('medicine_id')
                
                queryset = Stock.objects.all()
                
                if medicine_id:
                    queryset = queryset.filter(medicine_id=medicine_id)
                
                queryset = queryset.order_by('medicine__medicine_name')
                
                serializer = StockSerializer(queryset, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
                
        except Stock.DoesNotExist:
            return Response(
                {'detail': f'Stock with ID {stock_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def post(self, request):
        """
        POST: Create new stock + Expiry batch
        
        Role: Compounder staff only
        Body: {medicine_id: int, qty: int, expiry_date: date, batch_no: str}
        Response: StockSerializer with created Expiry batch
        Status: 201 Created
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can create stock records'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = StockCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get or create stock
            medicine_id = serializer.validated_data['medicine_id']
            medicine = Medicine.objects.get(id=medicine_id)
            
            stock, created = Stock.objects.get_or_create(
                medicine=medicine,
                defaults={'total_qty': 0}
            )
            
            # Create Expiry batch
            expiry = Expiry.objects.create(
                stock=stock,
                batch_no=serializer.validated_data['batch_no'],
                qty=serializer.validated_data['qty'],
                expiry_date=serializer.validated_data['expiry_date'],
                is_returned=False,
                returned_qty=0
            )
            
            # Return stock with all batches
            stock_serializer = StockSerializer(stock)
            return Response(stock_serializer.data, status=status.HTTP_201_CREATED)
            
        except Medicine.DoesNotExist:
            return Response(
                {'detail': 'Medicine not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def patch(self, request, stock_id=None):
        """
        PATCH: Update stock (metadata only, not quantities)
        
        Role: Compounder staff only
        Body: {} (no editable fields on Stock itself)
        Response: StockSerializer
        Status: 200 OK
        Note: Use Expiry endpoints to manage quantities
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can update stock records'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if not stock_id:
                return Response(
                    {'detail': 'Stock ID required for update'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            stock = selectors.get_stock_by_id(stock_id)
            
            # Stock model only has auto-managed fields, no direct updates possible
            # This endpoint is provided for API consistency
            serializer = StockSerializer(stock)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Stock.DoesNotExist:
            return Response(
                {'detail': f'Stock with ID {stock_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def delete(self, request, stock_id=None):
        """
        DELETE: Remove stock (hard delete - no historical data needed)
        
        Role: Compounder staff only
        Response: Empty (204 No Content)
        Note: This removes medicine from inventory system entirely
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can delete stock records'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if not stock_id:
                return Response(
                    {'detail': 'Stock ID required for deletion'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            stock = selectors.get_stock_by_id(stock_id)
            stock.delete()
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Stock.DoesNotExist:
            return Response(
                {'detail': f'Stock with ID {stock_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ===========================================================================
# ── COMPOUNDER: EXPIRY BATCH MANAGEMENT ───────────────────────────────────
# ===========================================================================

class CompounderExpiryView(APIView):
    """
    Expiry Batch CRUD Endpoints.
    Task 11: Compounder Staff Manages Medicine Expiry Batches
    RBAC: Compounder staff only
    
    Endpoints:
    - GET /compounder/expiry/ - List all batches (sorted by expiry_date, then created_date)
    - GET /compounder/expiry/{id}/ - Retrieve batch details
    - POST /compounder/expiry/ - Create new batch for existing stock
    - PATCH /compounder/expiry/{id}/ - Update batch info (batch_no, qty, expiry_date)
    - PATCH /compounder/expiry/{id}/return/ - Mark batch as returned (only if expired)
    - DELETE /compounder/expiry/{id}/ - Delete batch
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, expiry_id=None):
        """
        GET: Retrieve expiry batch record(s)
        
        Role: Compounder staff only
        Returns: Expiry batch(es) sorted by expiry_date (FIFO), then created_date
        Response: ExpirySerializer
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can access expiry records'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if expiry_id:
                # Specific expiry batch
                expiry = selectors.get_expiry_batch(expiry_id)
                serializer = ExpirySerializer(expiry)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                # List all expiry batches, sorted by expiry_date (FIFO), then created_date
                stock_id = request.query_params.get('stock_id')
                
                queryset = Expiry.objects.all().order_by('expiry_date', 'created_at')
                
                if stock_id:
                    queryset = queryset.filter(stock_id=stock_id)
                
                serializer = ExpirySerializer(queryset, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
                
        except Expiry.DoesNotExist:
            return Response(
                {'detail': f'Expiry batch with ID {expiry_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def post(self, request):
        """
        POST: Create new expiry batch for existing stock
        
        Role: Compounder staff only
        Body: {stock_id: int, batch_no: str, qty: int, expiry_date: date}
        Response: ExpirySerializer with created batch
        Status: 201 Created
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can create expiry batches'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = ExpiryCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get stock
            stock_id = serializer.validated_data['stock_id']
            try:
                stock = selectors.get_stock_by_id(stock_id)
            except Stock.DoesNotExist:
                return Response(
                    {'detail': f'Stock with ID {stock_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create Expiry batch
            expiry = Expiry.objects.create(
                stock=stock,
                batch_no=serializer.validated_data['batch_no'],
                qty=serializer.validated_data['qty'],
                expiry_date=serializer.validated_data['expiry_date'],
                is_returned=False,
                returned_qty=0
            )
            
            response_serializer = ExpirySerializer(expiry)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def patch(self, request, expiry_id=None):
        """
        PATCH: Update expiry batch metadata OR mark as returned
        
        Role: Compounder staff only
        
        For normal update:
            Body: {batch_no: str, qty: int, expiry_date: date}
            Response: ExpirySerializer
            Status: 200 OK
        
        For return action (/return/ in URL):
            Body: {returned_qty: int (optional, defaults to qty)}
            Validation: expiry_date must be <= today (expired)
            When marked returned:
                - is_returned flag set to True
                - returned_qty updated
                - Stock.total_qty automatically updated
            Response: ExpirySerializer
            Status: 200 OK
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can update expiry batches'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if not expiry_id:
                return Response(
                    {'detail': 'Expiry batch ID required for update'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            expiry = selectors.get_expiry_batch(expiry_id)
            
            # Check if this is a return action
            if request.path.endswith('/return/'):
                # Mark batch as returned
                serializer = ExpiryReturnSerializer(data=request.data)
                if not serializer.is_valid():
                    return Response(
                        {'errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Validate that batch is expired (expiry_date <= today)
                if expiry.expiry_date > date.today():
                    return Response(
                        {'detail': f'Cannot return batch that expires in future (expires: {expiry.expiry_date})'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Set returned qty
                returned_qty = serializer.validated_data.get('returned_qty')
                if returned_qty is None:
                    # Default: return entire batch
                    returned_qty = expiry.qty
                
                if returned_qty > expiry.qty:
                    return Response(
                        {'detail': f'Returned quantity ({returned_qty}) cannot exceed batch quantity ({expiry.qty})'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Update expiry batch
                expiry.is_returned = True
                expiry.returned_qty = returned_qty
                expiry.return_reason = serializer.validated_data.get('return_reason', '')
                expiry.save()
                
                response_serializer = ExpirySerializer(expiry)
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            
            else:
                # Normal update (metadata)
                serializer = ExpiryUpdateSerializer(expiry, data=request.data, partial=True)
                if not serializer.is_valid():
                    return Response(
                        {'errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                serializer.save()
                
                # Return updated expiry
                response_serializer = ExpirySerializer(expiry)
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except Expiry.DoesNotExist:
            return Response(
                {'detail': f'Expiry batch with ID {expiry_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def delete(self, request, expiry_id=None):
        """
        DELETE: Remove expiry batch (hard delete)
        
        Role: Compounder staff only
        Response: Empty (204 No Content)
        Note: This removes batch from inventory entirely
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can delete expiry batches'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if not expiry_id:
                return Response(
                    {'detail': 'Expiry batch ID required for deletion'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            expiry = selectors.get_expiry_batch(expiry_id)
            expiry.delete()
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Expiry.DoesNotExist:
            return Response(
                {'detail': f'Expiry batch with ID {expiry_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ===========================================================================
# ── COMPOUNDER: PRESCRIPTION MANAGEMENT ────────────────────────────────────
# ===========================================================================

class CompounderPrescriptionView(APIView):
    """
    Prescription CRUD Endpoints.
    Task 12: Compounder Creates Prescriptions with FIFO Stock Deduction
    RBAC: Compounder staff only (view all prescriptions)
    
    Endpoints:
    - GET /compounder/prescription/ - List all prescriptions
    - GET /compounder/prescription/{id}/ - Retrieve prescription with medicines
    - POST /compounder/prescription/ - Create prescription (triggers FIFO stock deduction)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, prescription_id=None):
        """
        GET: Retrieve prescription record(s)
        
        Role: Compounder staff only
        Returns: Prescription with nested PrescribedMedicine records
        Response: PrescriptionSerializer
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can access prescription records'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if prescription_id:
                # Specific prescription with all medicines
                prescription = Prescription.objects.get(id=prescription_id)
                serializer = PrescriptionSerializer(prescription)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                # List all prescriptions
                doctor_id = request.query_params.get('doctor_id')
                status_filter = request.query_params.get('status')
                
                queryset = Prescription.objects.all().order_by('-issued_date')
                
                if doctor_id:
                    queryset = queryset.filter(doctor_id=doctor_id)
                
                if status_filter:
                    queryset = queryset.filter(status=status_filter)
                
                paginator = StandardResultsSetPagination()
                page = paginator.paginate_queryset(queryset, request, view=self)
                if page is not None:
                    serializer = PrescriptionSerializer(page, many=True)
                    return paginator.get_paginated_response(serializer.data)
                    
                serializer = PrescriptionSerializer(queryset, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
                
        except Prescription.DoesNotExist:
            return Response(
                {'detail': f'Prescription with ID {prescription_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def post(self, request):
        """
        POST: Create new prescription with FIFO stock deduction
        
        Role: Compounder staff only
        Body: {
            user_id: int (system user ID - finds patient's latest consultation),
            doctor_id: int,
            medicines: [
                {medicine_id: int, qty_prescribed: int, days: int, times_per_day: int, instructions: str}
            ],
            details: str (optional),
            special_instructions: str (optional),
            test_recommended: str (optional),
            follow_up_suggestions: str (optional)
        }
        Response: PrescriptionSerializer with created prescription
        Status: 201 Created
        
        Key Features:
        - Accepts user_id to find patient's latest consultation
        - Validates all medicines exist
        - Checks total stock availability
        - Implements FIFO deduction from Expiry batches
        - Creates PrescribedMedicine records
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can create prescriptions'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Modified serializer to accept user_id
            user_id = request.data.get('user_id')
            doctor_id = request.data.get('doctor_id')
            medicines_data = request.data.get('medicines', [])
            
            # Validate required fields
            if not user_id:
                return Response(
                    {'error': 'user_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not doctor_id:
                return Response(
                    {'error': 'doctor_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Find the user in Django's User table
            try:
                user_obj = User.objects.get(id=int(user_id))
            except (User.DoesNotExist, ValueError, TypeError):
                return Response(
                    {'detail': f'User with ID {user_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Find the patient profile (ExtraInfo) for this user
            try:
                patient_profile = ExtraInfo.objects.get(user=user_obj)
            except ExtraInfo.DoesNotExist:
                return Response(
                    {'detail': f'Patient profile not found for user {user_id}'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Find or create a consultation for this patient
            # First, look for an existing consultation without a prescription
            consultation = Consultation.objects.filter(
                patient=patient_profile,
                prescription__isnull=True  # Only consultations without prescriptions
            ).order_by('-consultation_date').first()
            
            # If no consultation without a prescription exists, create a new one
            if not consultation:
                consultation = Consultation.objects.create(
                    patient=patient_profile,
                    doctor_id=int(doctor_id),
                    chief_complaint='Auto-created for prescription',
                    ambulance_requested='no'
                )
            
            # Get patient_id and consultation_id
            patient_id = patient_profile.id
            consultation_id = consultation.id
            
            # Prepare medicines data for service
            medicines_list = []
            for med_data in medicines_data:
                try:
                    medicine = Medicine.objects.get(id=int(med_data.get('medicine')))
                    medicines_list.append({
                        'medicine_id': medicine.id,
                        'qty_prescribed': int(med_data.get('qty_prescribed', 0)),
                        'days': int(med_data.get('days', 0)),
                        'times_per_day': int(med_data.get('times_per_day', 1)),
                        'instructions': med_data.get('instructions', ''),
                        'notes': med_data.get('notes', ''),
                    })
                except (ValueError, TypeError, Medicine.DoesNotExist) as e:
                    return Response(
                        {'detail': f'Invalid medicine data: {str(e)}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Create prescription with FIFO deduction
            try:
                from .. services import create_prescription_with_fifo_deduction, InsufficientStock, MedicineNotFound
                prescription = create_prescription_with_fifo_deduction(
                    consultation_id=consultation_id,
                    doctor_id=int(doctor_id),
                    patient_id=patient_id,
                    medicines_data=medicines_list
                )
                
                # Update prescription metadata
                prescription.details = request.data.get('details', '')
                prescription.special_instructions = request.data.get('special_instructions', '')
                prescription.test_recommended = request.data.get('test_recommended', '')
                prescription.follow_up_suggestions = request.data.get('follow_up_suggestions', '')
                prescription.is_for_dependent = request.data.get('is_for_dependent', False)
                prescription.dependent_name = request.data.get('dependent_name', '')
                prescription.dependent_relation = request.data.get('dependent_relation', '')
                prescription.save()
                
                response_serializer = PrescriptionSerializer(prescription)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
            except InsufficientStock as e:
                return Response(
                    {'detail': f'Insufficient stock: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except MedicineNotFound as e:
                return Response(
                    {'detail': f'Medicine not found: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def patch(self, request, prescription_id):
        """
        PATCH: Update prescription details and/or status
        
        Role: Compounder staff only
        Body: {
            details: str (optional),
            special_instructions: str (optional),
            test_recommended: str (optional),
            follow_up_suggestions: str (optional),
            status: 'DISPENSED' (can only change ISSUED -> DISPENSED)
        }
        Response: Updated PrescriptionSerializer
        Status: 200 OK
        
        Key Features:
        - Cannot update medicines or quantities (immutable after creation)
        - Can update details/instructions fields
        - Can transition status from ISSUED to DISPENSED only
        - Cannot update dispensed prescriptions
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can update prescriptions'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Validate serializer
            serializer = PrescriptionUpdateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Call service to update prescription details
            try:
                from .. services import update_prescription_details, InvalidPrescription
                
                prescription = update_prescription_details(
                    prescription_id=prescription_id,
                    update_data=serializer.validated_data
                )
                
                response_serializer = PrescriptionSerializer(prescription)
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            
            except InvalidPrescription as e:
                return Response(
                    {'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Prescription.DoesNotExist:
            return Response(
                {'detail': f'Prescription with ID {prescription_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def delete(self, request, prescription_id):
        """
        DELETE: Delete prescription and restore stock
        
        Role: Compounder staff only
        Constraints: Only if status is "ISSUED" (not "DISPENSED")
        
        Key Features:
        - Validates prescription exists and status is ISSUED
        - Reverses FIFO stock deductions
        - Restores quantities to Expiry batches
        - Returns 400 if prescription is dispensed
        - Cascades to PrescribedMedicine records
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can delete prescriptions'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            try:
                from .. services import delete_prescription_with_stock_restoration, InvalidPrescription
                
                deleted_id = delete_prescription_with_stock_restoration(prescription_id)
                
                return Response(
                    {
                        'detail': f'Prescription {deleted_id} deleted successfully',
                        'deleted_id': deleted_id
                    },
                    status=status.HTTP_204_NO_CONTENT
                )
            
            except InvalidPrescription as e:
                # Could be "not found" or "status not issued"
                error_msg = str(e)
                if 'not found' in error_msg.lower():
                    return Response(
                        {'detail': error_msg},
                        status=status.HTTP_404_NOT_FOUND
                    )
                else:
                    return Response(
                        {'detail': error_msg},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ── COMPOUNDER: CONSULTATION MANAGEMENT ────────────────────────────────────
# ===========================================================================

class CompounderConsultationView(APIView):
    """
    Consultation LIST Endpoints for Compounder staff.
    Returns all consultations available for creating prescriptions.
    Task: Compounder Creates Prescriptions (Consultation Selection)
    RBAC: Compounder staff only
    
    Endpoints:
    - GET /compounder/consultations/ - List all consultations (with filtering)
    
    Query Parameters:
    - days: int (optional) - Get consultations from last N days (default: 7)
    - doctor_id: int (optional) - Filter by specific doctor
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET: Retrieve all consultations for prescription creation
        
        Role: Compounder staff only
        Query Parameters:
            - days: Filter consultations from past N days (default: 7)
            - doctor_id: Filter by specific doctor ID
        
        Returns: List of consultations with enhanced info for dropdown
        Response: Consultation list with patient, doctor, and clinical details
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can access consultations'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get query parameters
            days = request.query_params.get('days', 7)
            doctor_id = request.query_params.get('doctor_id')
            
            try:
                days = int(days)
            except (ValueError, TypeError):
                days = 7
            
            # Filter recent consultations (last N days)
            from datetime import timedelta
            from django.utils import timezone
            cutoff_date = timezone.now() - timedelta(days=days)
            
            queryset = Consultation.objects.filter(
                consultation_date__gte=cutoff_date
            ).select_related(
                'patient', 'patient__user', 'doctor'
            ).order_by('-consultation_date')
            
            # Additional filter by doctor if provided
            if doctor_id:
                try:
                    queryset = queryset.filter(doctor_id=int(doctor_id))
                except (ValueError, TypeError):
                    pass
            
            # Build response with enhanced info for dropdown
            data = []
            for consultation in queryset:
                try:
                    patient_name = f"{consultation.patient.user.first_name} {consultation.patient.user.last_name}".strip()
                    patient_username = consultation.patient.user.username
                except:
                    patient_name = 'N/A'
                    patient_username = 'N/A'
                
                doctor_name = consultation.doctor.doctor_name if consultation.doctor else 'N/A'
                doctor_spec = f" ({consultation.doctor.specialization})" if consultation.doctor and consultation.doctor.specialization else ""
                
                data.append({
                    'id': consultation.id,
                    'value': str(consultation.id),
                    'label': f"Consultation #{consultation.id} - {patient_name} (Dr. {consultation.doctor.doctor_name}{doctor_spec})",
                    'patient_name': patient_name,
                    'patient_username': patient_username,
                    'patient_id': consultation.patient.user.id,
                    'doctor_name': doctor_name,
                    'doctor_id': consultation.doctor.id if consultation.doctor else None,
                    'specialization': consultation.doctor.specialization if consultation.doctor else '',
                    'consultation_date': consultation.consultation_date.isoformat(),
                    'chief_complaint': consultation.chief_complaint or '',
                    'history_of_present_illness': consultation.history_of_present_illness or '',
                    'examination_findings': consultation.examination_findings or '',
                    'provisional_diagnosis': consultation.provisional_diagnosis or '',
                    'final_diagnosis': consultation.final_diagnosis or '',
                    'treatment_plan': consultation.treatment_plan or '',
                    'advice': consultation.advice or '',
                    'blood_pressure_systolic': consultation.blood_pressure_systolic,
                    'blood_pressure_diastolic': consultation.blood_pressure_diastolic,
                    'pulse_rate': consultation.pulse_rate,
                    'temperature': consultation.temperature,
                    'oxygen_saturation': consultation.oxygen_saturation,
                    'weight': consultation.weight,
                    'follow_up_date': consultation.follow_up_date.isoformat() if consultation.follow_up_date else None,
                    'ambulance_requested': consultation.ambulance_requested or 'no',
                })
            
            return Response(data, status=status.HTTP_200_OK)
        
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class PatientPrescriptionView(APIView):
    """
    Patient Prescription READ-ONLY Endpoints.
    Task 12: Patients can view only their own prescriptions
    RBAC: Authenticated patients only (read own prescriptions)
    
    Endpoints:
    - GET /patient/prescriptions/ - List own prescriptions
    - GET /patient/prescription/{id}/ - Retrieve specific prescription (must be own)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, prescription_id=None):
        """
        GET: Retrieve patient's own prescriptions
        
        Role: Authenticated patient
        Returns: Own prescriptions only (all non-revoked medicines)
        Response: PrescriptionSerializer
        """
        try:
            # Get patient record
            if not is_patient(request.user):
                return Response(
                    {'detail': 'Only patients can access this endpoint'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            try:
                from applications.globals.models import ExtraInfo
                patient = ExtraInfo.objects.get(user=request.user)
            except ExtraInfo.DoesNotExist:
                return Response(
                    {'detail': 'User profile not found. Please complete your profile setup.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if prescription_id:
                # Specific prescription - check ownership
                prescription = Prescription.objects.get(id=prescription_id, patient=patient)
                serializer = PrescriptionSerializer(prescription)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                # List own prescriptions, sorted by date descending
                queryset = Prescription.objects.filter(
                    patient=patient
                ).select_related('doctor', 'consultation').prefetch_related('prescribed_medicines').order_by('-issued_date')
                
                serializer = PrescriptionSerializer(queryset, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
                
        except Prescription.DoesNotExist:
            return Response(
                {'detail': 'Prescription not found or does not belong to you'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ===========================================================================
# ── PATIENT: COMPLAINT MANAGEMENT ──────────────────────────────────────────
# ===========================================================================

class PatientComplaintView(APIView):
    """
    Patient Complaint Endpoints.
    Task 14: Patients submit, view, update, and delete own complaints
    RBAC: Authenticated patients only
    
    Endpoints:
    - POST /complaint/ - Submit new complaint
    - GET /complaint/ - List own complaints
    - GET /complaint/{id}/ - Get specific complaint (must be own)
    - PATCH /complaint/{id}/ - Update complaint (if not resolved)
    - DELETE /complaint/{id}/ - Delete complaint (if not resolved)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        POST: Submit new complaint
        
        Role: Authenticated patient
        Body: {"title": str, "description": str, "category": str}
        Response: ComplaintSerializer with created complaint
        Status: 201 Created
        """
        try:
            if not is_patient(request.user):
                return Response(
                    {'detail': 'Only patients can submit complaints'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = ComplaintCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get patient record
            patient = ExtraInfo.objects.get(user=request.user)
            
            # Create complaint
            complaint = ComplaintV2.objects.create(
                patient=patient,
                title=serializer.validated_data['title'],
                description=serializer.validated_data['description'],
                category=serializer.validated_data['category'],
                status='SUBMITTED'
            )
            
            response_serializer = ComplaintSerializer(complaint)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        except ExtraInfo.DoesNotExist:
            return Response(
                {'detail': 'Patient record not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    def get(self, request, complaint_id=None):
        """
        GET: Retrieve patient's own complaints
        
        Role: Authenticated patient
        Returns: Own complaints only
        Response: ComplaintSerializer(s)
        """
        try:
            if not is_patient(request.user):
                return Response(
                    {'detail': 'Only patients can view complaints'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get patient record
            patient = ExtraInfo.objects.get(user=request.user)
            
            if complaint_id:
                # Get specific complaint (must be own)
                complaint = ComplaintV2.objects.get(id=complaint_id, patient=patient)
                serializer = ComplaintSerializer(complaint)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                # List all own complaints
                queryset = ComplaintV2.objects.filter(patient=patient).order_by('-created_date')
                
                # Optional filtering
                status_filter = request.query_params.get('status')
                category_filter = request.query_params.get('category')
                
                if status_filter:
                    queryset = queryset.filter(status=status_filter)
                
                if category_filter:
                    queryset = queryset.filter(category=category_filter)
                
                serializer = ComplaintSerializer(queryset, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
        
        except ExtraInfo.DoesNotExist:
            return Response(
                {'detail': 'Patient record not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ComplaintV2.DoesNotExist:
            return Response(
                {'detail': 'Complaint not found or does not belong to you'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def patch(self, request, complaint_id):
        """
        PATCH: Update complaint (only if not resolved)
        
        Role: Authenticated patient
        Body: {"title": str, "description": str} (optional fields)
        Response: Updated ComplaintSerializer
        Status: 200 OK
        
        Constraints: Can only update non-resolved complaints
        """
        try:
            if not is_patient(request.user):
                return Response(
                    {'detail': 'Only patients can update complaints'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get patient record
            patient = ExtraInfo.objects.get(user=request.user)
            
            # Validate serializer (optional fields)
            serializer = ComplaintUpdateSerializer(data=request.data, partial=True)
            if not serializer.is_valid():
                return Response(
                    {'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Call service to update complaint
            try:
                from .. services import update_complaint_patient, InvalidPrescription
                
                complaint = update_complaint_patient(
                    complaint_id=complaint_id,
                    patient_id=patient.id,
                    update_data=serializer.validated_data
                )
                
                response_serializer = ComplaintSerializer(complaint)
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            
            except InvalidPrescription as e:
                error_msg = str(e)
                if 'not found' in error_msg.lower():
                    return Response(
                        {'detail': error_msg},
                        status=status.HTTP_404_NOT_FOUND
                    )
                else:
                    return Response(
                        {'detail': error_msg},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        except ExtraInfo.DoesNotExist:
            return Response(
                {'detail': 'Patient record not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def delete(self, request, complaint_id):
        """
        DELETE: Delete complaint (only if not resolved)
        
        Role: Authenticated patient
        Constraints: Can only delete non-resolved complaints
        Response: 204 No Content
        """
        try:
            if not is_patient(request.user):
                return Response(
                    {'detail': 'Only patients can delete complaints'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get patient record
            patient = ExtraInfo.objects.get(user=request.user)
            
            # Get and verify ownership
            complaint = ComplaintV2.objects.get(id=complaint_id, patient=patient)
            
            # Check if resolved
            if complaint.status == 'RESOLVED':
                return Response(
                    {'detail': 'Cannot delete a resolved complaint'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Delete the complaint
            complaint.delete()
            
            return Response(
                {'detail': f'Complaint {complaint_id} deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )
        
        except ExtraInfo.DoesNotExist:
            return Response(
                {'detail': 'Patient record not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ComplaintV2.DoesNotExist:
            return Response(
                {'detail': 'Complaint not found or does not belong to you'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ===========================================================================
# ── COMPOUNDER: COMPLAINT MANAGEMENT ───────────────────────────────────────
# ===========================================================================

class CompounderComplaintView(APIView):
    """
    Compounder Complaint Endpoints.
    Task 14: Compounder views all complaints and responds to any
    RBAC: PHC staff only
    
    Endpoints:
    - GET /compounder/complaint/ - List all complaints
    - GET /compounder/complaint/{id}/ - Get complaint details
    - PATCH /compounder/complaint/{id}/respond/ - Respond/resolve complaint
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, complaint_id=None):
        """
        GET: Retrieve complaint(s)
        
        Role: Compounder staff only
        Returns: All complaints (list or detail)
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can access complaint records'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if complaint_id:
                # Get specific complaint
                complaint = ComplaintV2.objects.get(id=complaint_id)
                serializer = ComplaintSerializer(complaint)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                # List all complaints
                queryset = ComplaintV2.objects.all().order_by('-created_date')
                
                # Optional filtering
                status_filter = request.query_params.get('status')
                category_filter = request.query_params.get('category')
                patient_id = request.query_params.get('patient_id')
                
                if status_filter:
                    queryset = queryset.filter(status=status_filter)
                
                if category_filter:
                    queryset = queryset.filter(category=category_filter)
                
                if patient_id:
                    queryset = queryset.filter(patient_id=patient_id)
                
                serializer = ComplaintSerializer(queryset, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
        
        except ComplaintV2.DoesNotExist:
            return Response(
                {'detail': f'Complaint with ID {complaint_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def patch(self, request, complaint_id):
        """
        PATCH: Respond to complaint and mark resolved
        
        Role: Compounder staff only
        Body: {"resolution_notes": str}
        Response: Updated ComplaintSerializer
        Status: 200 OK
        
        Key Features:
        - Marks complaint as RESOLVED
        - Records resolution notes
        - Tracks who resolved (resolved_by field)
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can respond to complaints'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Validate serializer
            serializer = ComplaintRespondSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get compounder (staff) info
            compounder = ExtraInfo.objects.get(user=request.user)
            
            # Call service to resolve complaint
            try:
                from .. services import resolve_complaint_with_notes, InvalidPrescription
                
                complaint = resolve_complaint_with_notes(
                    complaint_id=complaint_id,
                    resolution_notes=serializer.validated_data['resolution_notes'],
                    resolved_by_id=compounder.id
                )
                
                response_serializer = ComplaintSerializer(complaint)
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            
            except InvalidPrescription as e:
                return Response(
                    {'detail': str(e)},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        except ExtraInfo.DoesNotExist:
            return Response(
                {'detail': 'Staff record not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ===========================================================================
# ── HOSPITAL ADMISSION ENDPOINTS ─────────────────────────────────────────
# ===========================================================================

class CompounderHospitalAdmitView(APIView):
    """
    Hospital admission management endpoints.
    Task 15: CRUD endpoints for hospital admissions
    
    Endpoints:
      GET    /compounder/hospital-admit/          - List all admissions
      GET    /compounder/hospital-admit/{id}/     - Get specific admission
      POST   /compounder/hospital-admit/          - Create admission
      PATCH  /compounder/hospital-admit/{id}/     - Update admission
      PATCH  /compounder/hospital-admit/{id}/discharge/ - Discharge patient
      DELETE /compounder/hospital-admit/{id}/     - Delete admission
    """
    
    def get(self, request, admission_id=None):
        """GET: List all admissions or get specific admission"""
        # RBAC: Only compounder/staff can access
        if not is_phc_staff(request):
            return Response(
                {'detail': 'Only PHC staff can access hospital admission records'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Get specific admission by ID
            if admission_id:
                admission = get_object_or_404(HospitalAdmit, id=admission_id)
                serializer = HospitalAdmitSerializer(admission)
                return Response(serializer.data, status=status.HTTP_200_OK)
            
            # List all admissions with optional filters
            admissions = HospitalAdmit.objects.all()
            
            # Filter by status (admitted vs discharged)
            status_filter = request.query_params.get('status')
            if status_filter:
                if status_filter == 'admitted':
                    admissions = admissions.filter(discharge_date__isnull=True)
                elif status_filter == 'discharged':
                    admissions = admissions.filter(discharge_date__isnull=False)
            
            # Filter by patient
            patient_id = request.query_params.get('patient_id')
            if patient_id:
                admissions = admissions.filter(patient_id=patient_id)
            
            # Filter by date range
            from_date = request.query_params.get('from_date')
            to_date = request.query_params.get('to_date')
            if from_date:
                admissions = admissions.filter(admission_date__gte=from_date)
            if to_date:
                admissions = admissions.filter(admission_date__lte=to_date)
            
            serializer = HospitalAdmitSerializer(admissions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    def post(self, request):
        """POST: Create hospital admission"""
        # RBAC: Only compounder/staff can create
        if not is_phc_staff(request):
            return Response(
                {'detail': 'Only PHC staff can create hospital admissions'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Validate serializer
            serializer = HospitalAdmitCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Get patient ID from request
            patient_id = request.data.get('patient_id')
            if not patient_id:
                return Response(
                    {'detail': 'Patient ID is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create admission via service
            admission = services.create_hospital_admission(
                patient_id=patient_id,
                admission_data=serializer.validated_data
            )
            
            response_serializer = HospitalAdmitSerializer(admission)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        except services.InvalidPrescription as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    def patch(self, request, admission_id):
        """PATCH: Update admission or discharge patient"""
        # RBAC: Only compounder/staff can update
        if not is_phc_staff(request):
            return Response(
                {'detail': 'Only PHC staff can update hospital admissions'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Check if this is a discharge operation
            is_discharge = 'discharge_date' in request.data and len(request.data) <= 2
            
            if is_discharge:
                # Discharge endpoint logic
                serializer = HospitalAdmitUpdateSerializer(data=request.data)
                if not serializer.is_valid():
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
                # Call service to discharge
                admission = services.discharge_patient(
                    admission_id=admission_id,
                    discharge_data=serializer.validated_data
                )
            else:
                # Regular update endpoint logic
                serializer = HospitalAdmitUpdateSerializer(
                    data=request.data,
                    partial=True
                )
                if not serializer.is_valid():
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
                # Call service to update
                admission = services.update_hospital_admission(
                    admission_id=admission_id,
                    update_data=serializer.validated_data
                )
            
            response_serializer = HospitalAdmitSerializer(admission)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        except services.InvalidPrescription as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    def delete(self, request, admission_id):
        """DELETE: Soft delete hospital admission"""
        # RBAC: Only compounder/staff can delete
        if not is_phc_staff(request):
            return Response(
                {'detail': 'Only PHC staff can delete hospital admissions'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            admission = get_object_or_404(HospitalAdmit, id=admission_id)
            
            # Log the deletion in audit
            services.log_audit_action(
                user_id=admission.patient_id,
                action_type='DELETE',
                entity_type='HospitalAdmit',
                entity_id=admission.id,
                details={'deleted': True}
            )
            
            # Perform hard delete (adjust if soft delete preferred)
            admission.delete()
            
            return Response(
                {'detail': f'Hospital admission {admission_id} deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )
        
        except HospitalAdmit.DoesNotExist:
            return Response(
                {'detail': f'Hospital admission {admission_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ===========================================================================
# ── AMBULANCE RECORDS ENDPOINTS ──────────────────────────────────────────
# ===========================================================================

class CompounderAmbulanceView(APIView):
    """
    Ambulance records management endpoints.
    Task 16: CRUD endpoints for ambulance fleet management (compounder only)
    
    Endpoints:
      GET    /compounder/ambulance/               - List all ambulances
      GET    /compounder/ambulance/{id}/          - Get specific ambulance
      POST   /compounder/ambulance/               - Create ambulance record
      PATCH  /compounder/ambulance/{id}/          - Update ambulance
      DELETE /compounder/ambulance/{id}/          - Delete ambulance
    """
    
    def get(self, request, ambulance_id=None):
        """GET: List all ambulances or get specific ambulance"""
        # RBAC: Only compounder/staff can access
        if not is_phc_staff(request):
            return Response(
                {'detail': 'Only PHC staff can access ambulance records'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Get specific ambulance by ID
            if ambulance_id:
                ambulance = get_object_or_404(AmbulanceRecordsV2, id=ambulance_id)
                serializer = AmbulanceRecordsSerializer(ambulance)
                return Response(serializer.data, status=status.HTTP_200_OK)
            
            # List all ambulances with optional filters
            ambulances = AmbulanceRecordsV2.objects.all()
            
            # Filter by status
            status_filter = request.query_params.get('status')
            if status_filter:
                ambulances = ambulances.filter(status=status_filter)
            
            # Filter by availability
            available_only = request.query_params.get('available_only')
            if available_only and available_only.lower() == 'true':
                ambulances = ambulances.filter(status='AVAILABLE', is_active=True)
            
            # Filter by is_active
            is_active_filter = request.query_params.get('is_active')
            if is_active_filter:
                is_active = is_active_filter.lower() == 'true'
                ambulances = ambulances.filter(is_active=is_active)
            
            # Filter by vehicle type
            vehicle_type = request.query_params.get('vehicle_type')
            if vehicle_type:
                ambulances = ambulances.filter(vehicle_type=vehicle_type)
            
            serializer = AmbulanceRecordsSerializer(ambulances, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    def post(self, request):
        """POST: Create ambulance record"""
        # RBAC: Only compounder/staff can create
        if not is_phc_staff(request):
            return Response(
                {'detail': 'Only PHC staff can create ambulance records'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Validate serializer
            serializer = AmbulanceRecordsCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Create ambulance via service
            ambulance = services.create_ambulance_record(
                ambulance_data=serializer.validated_data
            )
            
            response_serializer = AmbulanceRecordsSerializer(ambulance)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        except services.InvalidPrescription as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    def patch(self, request, ambulance_id):
        """PATCH: Update ambulance record"""
        # RBAC: Only compounder/staff can update
        if not is_phc_staff(request):
            return Response(
                {'detail': 'Only PHC staff can update ambulance records'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Validate serializer
            serializer = AmbulanceRecordsUpdateSerializer(
                data=request.data,
                partial=True
            )
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Call service to update
            ambulance = services.update_ambulance_record(
                ambulance_id=ambulance_id,
                update_data=serializer.validated_data
            )
            
            response_serializer = AmbulanceRecordsSerializer(ambulance)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        except services.InvalidPrescription as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    def delete(self, request, ambulance_id):
        """DELETE: Hard delete ambulance record"""
        # RBAC: Only compounder/staff can delete
        if not is_phc_staff(request):
            return Response(
                {'detail': 'Only PHC staff can delete ambulance records'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            ambulance = get_object_or_404(AmbulanceRecordsV2, id=ambulance_id)
            
            # Log the deletion in audit
            services.log_audit_action(
                user_id=None,
                action_type='DELETE',
                entity_type='AmbulanceRecord',
                entity_id=ambulance.id,
                details={'registration': ambulance.registration_number}
            )
            
            # Perform hard delete (or soft delete if preferred)
            ambulance.delete()
            
            return Response(
                {'detail': f'Ambulance {ambulance_id} deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )
        
        except AmbulanceRecordsV2.DoesNotExist:
            return Response(
                {'detail': f'Ambulance {ambulance_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ===========================================================================
# ── PHC-UC-11: AMBULANCE USAGE LOG VIEW ──────────────────────────────────
# ===========================================================================

class CompounderAmbulanceLogView(APIView):
    """
    PHC-UC-11: Ambulance Usage Log — chronological dispatch records.

    This view manages the usage LOG of ambulance calls (who was transported,
    when, and where). It is SEPARATE from CompounderAmbulanceView which
    manages the fleet (vehicles, drivers, maintenance).

    Business Rules enforced:
      - PHC-BR-03 (RBAC): Only PHC staff can create/delete log entries
      - PHC-BR-09 (Audit Trail): Every create/delete is written to AuditLog
                                  via the service layer (S-LOG-AUDIT)

    Endpoints:
      GET    /compounder/ambulance-log/          — list all log entries (newest first)
      GET    /compounder/ambulance-log/<id>/     — fetch one specific entry
      POST   /compounder/ambulance-log/          — create a new dispatch log entry
      DELETE /compounder/ambulance-log/<id>/     — delete an entry (correction only)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, log_id=None):
        """GET: List all ambulance log entries or retrieve a specific one."""
        if not is_phc_staff(request):
            return Response({'detail': 'Only PHC staff can access ambulance logs.'},
                            status=status.HTTP_403_FORBIDDEN)
        try:
            if log_id:
                entry = get_object_or_404(AmbulanceLog, id=log_id)
                return Response(AmbulanceLogSerializer(entry).data, status=status.HTTP_200_OK)

            logs = AmbulanceLog.objects.select_related('ambulance', 'logged_by__user').all()

            # Optional filters
            date_from = request.query_params.get('date_from')
            date_to   = request.query_params.get('date_to')
            search    = request.query_params.get('search', '').strip()

            if date_from:
                logs = logs.filter(call_date__gte=date_from)
            if date_to:
                logs = logs.filter(call_date__lte=date_to)
            if search:
                logs = logs.filter(patient_name__icontains=search) | \
                       logs.filter(destination__icontains=search)

            return Response(AmbulanceLogSerializer(logs, many=True).data, status=status.HTTP_200_OK)

        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @transaction.atomic
    def post(self, request):
        """POST: Create a new ambulance dispatch log entry (PHC-UC-11 M2)."""
        if not is_phc_staff(request):
            return Response({'detail': 'Only PHC staff can log ambulance usage.'},
                            status=status.HTTP_403_FORBIDDEN)
        try:
            serializer = AmbulanceLogCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({'detail': f"Validation error: {serializer.errors}"}, status=status.HTTP_400_BAD_REQUEST)

            from applications.health_center.services import create_ambulance_log
            from applications.globals.models import ExtraInfo

            try:
                extrainfo = ExtraInfo.objects.get(user=request.user)
                logged_by_id = extrainfo.id
            except ExtraInfo.DoesNotExist:
                logged_by_id = None

            entry = create_ambulance_log(
                log_data=serializer.validated_data,
                logged_by_id=logged_by_id,
            )

            return Response(AmbulanceLogSerializer(entry).data, status=status.HTTP_201_CREATED)

        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @transaction.atomic
    def delete(self, request, log_id):
        """DELETE: Remove a log entry (PHC-UC-11 correction; audit-logged per PHC-BR-09)."""
        if not is_phc_staff(request):
            return Response({'detail': 'Only PHC staff can delete ambulance log entries.'},
                            status=status.HTTP_403_FORBIDDEN)
        try:
            from applications.health_center.services import delete_ambulance_log
            from applications.globals.models import ExtraInfo

            try:
                extrainfo = ExtraInfo.objects.get(user=request.user)
                deleted_by_id = extrainfo.id
            except ExtraInfo.DoesNotExist:
                deleted_by_id = None

            delete_ambulance_log(log_id=log_id, deleted_by_id=deleted_by_id)
            return Response({'detail': f'Ambulance log #{log_id} deleted.'},
                            status=status.HTTP_200_OK)

        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class CompounderUserView(APIView):
    """
    User LIST Endpoints for Compounder staff.
    Returns all active users who can login to the system.
    Task: Compounder Creates Prescriptions (User Selection)
    RBAC: Compounder staff only
    
    Endpoints:
    - GET /compounder/users/ - List all active users for system
    
    Query Parameters:
    - search: str (optional) - Search by username, first name, or last name
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        GET: Retrieve all active users who can login to system
        
        Role: Compounder staff only
        Query Parameters:
            - search: Search by username, first_name, or last_name
        
        Returns: List of users for dropdown selection
        Response: User list with enhanced info for dropdown
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can access users'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get query parameters
            search = request.query_params.get('search', '').strip()
            
            # Filter active users who can login to system
            queryset = User.objects.filter(
                is_active=True
            ).select_related().order_by('username')
            
            # Additional search if provided
            if search:
                from django.db.models import Q
                queryset = queryset.filter(
                    Q(username__icontains=search) |
                    Q(first_name__icontains=search) |
                    Q(last_name__icontains=search)
                )
            
            # Build response with enhanced info for dropdown
            data = []
            for user in queryset:
                full_name = f"{user.first_name} {user.last_name}".strip()
                if not full_name:
                    full_name = user.username
                
                data.append({
                    'id': user.id,
                    'value': str(user.id),
                    'label': f"{user.username} - {full_name}",
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'full_name': full_name,
                    'email': user.email,
                })
            
            return Response(data, status=status.HTTP_200_OK)
        
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class CompounderConsultationFormView(APIView):
    """
    Consultation Creation Endpoint.
    Allows compounder staff to create new consultations for patients.
    Task: Create consultations with clinical information
    RBAC: Compounder staff only
    
    Endpoints:
    - POST /compounder/consultation/ - Create new consultation
    """
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        """
        POST: Create new consultation
        
        Role: Compounder staff only
        Body: {
            user_id: int (system user ID - finds patient profile),
            doctor_id: int,
            chief_complaint: str (required),
            history_of_present_illness: str (optional),
            examination_findings: str (optional),
            provisional_diagnosis: str (optional),
            final_diagnosis: str (optional),
            treatment_plan: str (optional),
            advice: str (optional),
            blood_pressure_systolic: int (optional),
            blood_pressure_diastolic: int (optional),
            pulse_rate: int (optional),
            temperature: float (optional),
            oxygen_saturation: int (optional),
            weight: float (optional),
            follow_up_date: date (optional),
        }
        Response: ConsultationSerializer with created consultation
        Status: 201 Created
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can create consultations'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get and validate required fields
            user_id = request.data.get('user_id')
            doctor_id = request.data.get('doctor_id')
            chief_complaint = request.data.get('chief_complaint', '')
            
            if not user_id:
                return Response(
                    {'error': 'user_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not doctor_id:
                return Response(
                    {'error': 'doctor_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not chief_complaint:
                return Response(
                    {'error': 'chief_complaint is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Find the user in Django's User table
            try:
                user_obj = User.objects.get(id=int(user_id))
            except (User.DoesNotExist, ValueError, TypeError):
                return Response(
                    {'detail': f'User with ID {user_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Find or create patient profile (ExtraInfo) for this user
            patient_profile, created = ExtraInfo.objects.get_or_create(
                user=user_obj,
                defaults={'category': 'Student'}
            )
            
            # Create the consultation
            consultation = Consultation.objects.create(
                patient=patient_profile,
                doctor_id=int(doctor_id),
                chief_complaint=chief_complaint,
                history_of_present_illness=request.data.get('history_of_present_illness', ''),
                examination_findings=request.data.get('examination_findings', ''),
                provisional_diagnosis=request.data.get('provisional_diagnosis', ''),
                final_diagnosis=request.data.get('final_diagnosis', ''),
                treatment_plan=request.data.get('treatment_plan', ''),
                advice=request.data.get('advice', ''),
                blood_pressure_systolic=request.data.get('blood_pressure_systolic'),
                blood_pressure_diastolic=request.data.get('blood_pressure_diastolic'),
                pulse_rate=request.data.get('pulse_rate'),
                temperature=request.data.get('temperature'),
                oxygen_saturation=request.data.get('oxygen_saturation'),
                weight=request.data.get('weight'),
                follow_up_date=request.data.get('follow_up_date'),
                ambulance_requested=request.data.get('ambulance_requested', 'no'),
            )
            
            response_serializer = ConsultationSerializer(consultation)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        except ValueError as e:
            return Response(
                {'detail': f'Invalid data format: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @transaction.atomic
    def delete(self, request, consultation_id):
        """
        DELETE: Delete a consultation
        
        Role: Compounder staff only
        URL param: consultation_id
        Response: Success message
        Status: 204 No Content
        """
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can delete consultations'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            consultation = Consultation.objects.get(id=int(consultation_id))
            consultation.delete()
            
            return Response(
                {'detail': 'Consultation deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )
        
        except Consultation.DoesNotExist:
            return Response(
                {'detail': 'Consultation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {'detail': 'Invalid consultation ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# =========================================================================
# ── AUDITOR: PING TEST - Simple endpoint to verify routing ──────────────
# =========================================================================

class AuditorPingView(APIView):
    """Minimal ping endpoint to verify routing works"""
    def get(self, request):
        """GET: Simple response to test if endpoint is reached"""
        return Response({
            'status': 'success',
            'message': 'Auditor ping endpoint is working',
            'user': str(request.user),
            'authenticated': request.user.is_authenticated
        })


# =========================================================================
# ── AUDITOR: DEBUG VIEW - Raw claim data without serialization ─────────
# =========================================================================

class AuditorDebugView(APIView):
    """Debug endpoint to see raw claim data"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """GET: Return raw claim data for debugging"""
        try:
            from applications.health_center.decorators import is_auditor
            if not is_auditor(request.user):
                return Response({'detail': 'Not auditor'}, status=403)
            
            # Get all claims (any status)
            all_claims = ReimbursementClaim.objects.all().count()
            phc_review_claims = ReimbursementClaim.objects.filter(status='PHC_REVIEW').count()
            
            # Get all statuses
            from django.db.models import F
            statuses = list(
                ReimbursementClaim.objects.values_list('status', flat=True).distinct()
            )
            
            return Response({
                'debug': 'Claim statistics',
                'total_claims': all_claims,
                'claims_in_PHC_REVIEW': phc_review_claims,
                'available_statuses': statuses,
                'authenticated_user': str(request.user),
            })
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# =========================================================================
# ── AUDITOR: REIMBURSEMENT CLAIMS REVIEW & APPROVAL ──────────────────
# =========================================================================

class AuditorReimbursementView(APIView):
    """
    Auditor interface for reviewing and approving/rejecting reimbursement claims
    
    Endpoints:
      GET /auditor/reimbursement-claims/ - List all claims in PHC_REVIEW status
      GET /auditor/reimbursement-claims/{id}/ - Get specific claim details
      PATCH /auditor/reimbursement-claims/{id}/approve/ - Approve claim
      PATCH /auditor/reimbursement-claims/{id}/reject/ - Reject claim
    
    RBAC: Auditor only (AUDITOR user_type or auditor designation)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, claim_id=None):
        """GET: List claims or get specific claim"""
        import traceback
        logger = logging.getLogger(__name__)
        
        try:
            from applications.health_center.decorators import is_auditor
            
            # Check auditor authorization
            if not is_auditor(request.user):
                return Response(
                    {'detail': 'Unauthorized - auditor access required'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            logger.info(f'[AUDITOR] {request.user.username} passed authorization check')
            
            # If fetching specific claim
            if claim_id:
                try:
                    claim = ReimbursementClaim.objects.get(id=claim_id)
                    serializer = ReimbursementClaimSerializer(claim)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                except ReimbursementClaim.DoesNotExist:
                    return Response(
                        {'detail': 'Claim not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            # List all claims visible to auditor (pending review + already processed)
            logger.info(f'[AUDITOR] Fetching all auditor-visible claims')
            claims = ReimbursementClaim.objects.filter(
                status__in=['PHC_REVIEW', 'SANCTION_APPROVED', 'FINAL_PAYMENT', 'REIMBURSED', 'REJECTED']
            ).order_by('-created_at')
            
            logger.info(f'[AUDITOR] Found {claims.count()} claims')
            
            serializer = ReimbursementClaimSerializer(claims, many=True)
            logger.info(f'[AUDITOR] Serialization successful')
            
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    @transaction.atomic
    def patch(self, request, claim_id):
        """PATCH: Approve or reject claim based on URL path"""
        try:
            # Check auditor authorization
            from applications.health_center.decorators import is_auditor
            if not is_auditor(request.user):
                return Response(
                    {'detail': 'Only auditors can approve or reject claims'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get auditor ID
            try:
                auditor = ExtraInfo.objects.get(user=request.user)
            except ExtraInfo.DoesNotExist:
                return Response(
                    {'detail': 'User profile not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the claim
            claim = ReimbursementClaim.objects.get(id=claim_id)
            
            # Verify claim is in PHC_REVIEW status (pending auditor review)
            if claim.status != 'PHC_REVIEW':
                return Response(
                    {'detail': 'Only claims in PHC Review status can be approved/rejected'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get remarks
            remarks = request.data.get('remarks', '')
            if not remarks:
                return Response(
                    {'detail': 'Remarks are required for approval/rejection'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Determine action from URL path
            path = request.META.get('PATH_INFO', '')
            
            if 'approve' in path:
                # Approve claim - move to FINAL_PAYMENT
                claim.status = 'FINAL_PAYMENT'
                claim.auditor_approval_remarks = remarks
                claim.auditor_approved_by = auditor
                claim.auditor_approved_date = timezone.now()
                claim.save()
                
                # Log the approval action
                logger = logging.getLogger(__name__)
                logger.info(f'Claim {claim.id} approved by auditor {auditor.id}')
                
            elif 'reject' in path:
                # Reject claim - move to REJECTED
                claim.status = 'REJECTED'
                claim.rejection_remarks = remarks
                claim.rejected_by_auditor = auditor
                claim.rejection_date = timezone.now()
                claim.save()
                
                # Log the rejection
                logger = logging.getLogger(__name__)
                logger.info(f'Claim {claim.id} rejected by auditor {auditor.id}')
            
            else:
                return Response(
                    {'detail': 'Invalid action. Use /approve/ or /reject/'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = ReimbursementClaimSerializer(claim)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except ReimbursementClaim.DoesNotExist:
            return Response(
                {'detail': 'Claim not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class AuditorClaimDocumentDownloadView(APIView):
    """Download claim documents for auditor review"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, document_id):
        """GET: Download claim document"""
        try:
            # Check auditor authorization
            from applications.health_center.decorators import is_auditor
            if not is_auditor(request.user):
                return Response(
                    {'detail': 'Only auditors can download claim documents'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            from applications.health_center.models import ClaimDocument
            document = ClaimDocument.objects.get(id=document_id)
            
            # Verify the document's claim is in SANCTION_REVIEW or already processed
            if document.claim.status not in ['SANCTION_REVIEW', 'FINAL_PAYMENT', 'REIMBURSED', 'REJECTED']:
                return Response(
                    {'detail': 'Document not available'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if document.document_file:
                response = FileResponse(
                    document.document_file.open('rb'),
                    as_attachment=True,
                    filename=document.document_name
                )
                return response
            else:
                return Response(
                    {'detail': 'Document file not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ===========================================================================
# ── TASK 5: INVENTORY REQUISITIONS ───────────────────────────────────────
# ===========================================================================

class CompounderInventoryRequisitionView(APIView):
    """
    Compounder manages Inventory Requisitions.
    Task 5: Send the inventory requisition request, also show the status in it.
    
    Endpoints:
    - GET /compounder/requisition/ -> List created requisitions with status
    - POST /compounder/requisition/ -> Submit new requisition
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        """GET: List all requisitions or a specific one"""
        try:
            if not is_phc_staff(request):
                return Response({'detail': 'Only PHC staff can access requisitions'}, status=status.HTTP_403_FORBIDDEN)
                
            if pk:
                req = InventoryRequisition.objects.get(id=pk)
                return Response(InventoryRequisitionSerializer(req).data)
            else:
                reqs = InventoryRequisition.objects.all().order_by('-created_date')
                return Response(InventoryRequisitionSerializer(reqs, many=True).data)
        except InventoryRequisition.DoesNotExist:
            return Response({'detail': 'Requisition not found'}, status=status.HTTP_404_NOT_FOUND)
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @transaction.atomic
    def post(self, request):
        """POST: Compounder submits new requisition"""
        try:
            if not is_phc_staff(request):
                return Response({'detail': 'Only PHC staff can create requisitions'}, status=status.HTTP_403_FORBIDDEN)
                
            serializer = InventoryRequisitionCreateSerializer(data=request.data)
            if serializer.is_valid():
                from applications.health_center.services import create_requisition
                
                # Fetch created_by_id (assumes ExtraInfo ID is standard)
                created_by_id = request.user.extrainfo.id if hasattr(request.user, 'extrainfo') else request.user.id
                
                requisition = create_requisition(
                    medicine_id=serializer.validated_data['medicine'].id,
                    quantity_requested=serializer.validated_data['quantity_requested'],
                    created_by_id=created_by_id
                )
                
                # Automatically mark it SUBMITTED based on the workflow
                # Some implementations might leave it as CREATED initially, but compounders usually submit it immediately here.
                requisition.status = 'SUBMITTED'
                requisition.save()
                
                return Response(InventoryRequisitionSerializer(requisition).data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @transaction.atomic
    def patch(self, request, pk):
        """PATCH /compounder/requisition/<pk>/fulfill/ — Mark requisition as fulfilled (PHC-UC-14)"""
        try:
            if not is_phc_staff(request):
                return Response(
                    {'detail': 'Only PHC staff can fulfill requisitions'},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = FulfillRequisitionSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            from applications.health_center.services import fulfill_inventory_requisition

            fulfilled_by_id = request.user.extrainfo.id if hasattr(request.user, 'extrainfo') else request.user.id

            requisition = fulfill_inventory_requisition(
                requisition_id=pk,
                fulfilled_by_id=fulfilled_by_id,
                quantity_fulfilled=serializer.validated_data['quantity_fulfilled'],
            )

            return Response(InventoryRequisitionSerializer(requisition).data, status=status.HTTP_200_OK)

        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===========================================================================
# ── PHC-UC-16: APPROVE INVENTORY REQUISITION (AUTHORITY) ─────────────────
# ===========================================================================
#
# STATUS: IMPLEMENTED — COMMENTED OUT (Cross-module boundary pending)
#
# WHY COMMENTED OUT:
#   The "Approving Authority" actor (e.g. CMO, Director, Accounts Officer)
#   is NOT a role managed within the health_center module. The exact
#   designation/role that maps to this authority has not been finalised
#   by the institute and is expected to be defined in a future integration
#   with the institute-wide globals/admin module.
#
# WHAT TO DO WHEN INTEGRATING:
#   1. Update _is_authority() below to check the correct role/designation
#      (e.g., a specific user_type or a permission group like
#      'phc_approving_authority', set in the admin panel).
#   2. Uncomment this class entirely.
#   3. Uncomment the corresponding URL routes in urls.py (see below).
#   4. Uncomment the PHC-BR-11 notification blocks in services.py's
#      approve_inventory_requisition() and reject_inventory_requisition().
#
# IMPLEMENTS: PHC-UC-16, PHC-BR-10, PHC-BR-11, PHC-WF-02
#
# ENDPOINTS (once uncommented):
#   GET  /authority/requisition/           → List pending requisitions
#   GET  /authority/requisition/<id>/      → Get specific requisition
#   PATCH /authority/requisition/<id>/approve/ → Approve requisition
#   PATCH /authority/requisition/<id>/reject/  → Reject requisition
# ===========================================================================
#
# class AuthorityInventoryRequisitionView(APIView):
#     """
#     PHC-UC-16: Approving Authority reviews and acts on inventory requisitions.
#
#     This view must only be accessible to the designated approving authority
#     (e.g., CMO, Director, or Accounts Officer). Update _is_authority() to
#     reflect the correct role once the institute-wide role definition is ready.
#     """
#     permission_classes = [IsAuthenticated]
#
#     def _is_authority(self, user):
#         """
#         CROSS-MODULE BOUNDARY: Authority role check.
#         ─────────────────────────────────────────────
#         Currently defaults to Django's built-in is_staff / is_superuser.
#         Replace or extend this based on the institute's authority role once
#         defined (e.g., check a Django permission group or ExtraInfo.user_type).
#
#         Example when role is defined:
#             extra = getattr(user, 'extrainfo', None)
#             return extra and extra.user_type.lower() == 'cmo'
#         """
#         return user.is_staff or user.is_superuser
#
#     def get(self, request, pk=None, action=None):
#         """GET: List SUBMITTED requisitions pending approval, or fetch one by pk."""
#         try:
#             if not self._is_authority(request.user):
#                 return Response(
#                     {'detail': 'Only the Approving Authority can view requisitions for approval.'},
#                     status=status.HTTP_403_FORBIDDEN
#                 )
#
#             if pk:
#                 req = InventoryRequisition.objects.get(id=pk)
#                 return Response(InventoryRequisitionSerializer(req).data)
#             else:
#                 # Show all requisitions with SUBMITTED status pending action
#                 reqs = InventoryRequisition.objects.filter(
#                     status='SUBMITTED'
#                 ).order_by('-created_date')
#                 return Response(InventoryRequisitionSerializer(reqs, many=True).data)
#
#         except InventoryRequisition.DoesNotExist:
#             return Response({'detail': 'Requisition not found'}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
#
#     @transaction.atomic
#     def patch(self, request, pk, action=None):
#         """
#         PATCH: Approve or reject a requisition.
#
#         Actions:
#           approve → Transitions status to APPROVED (PHC-BR-10 gate)
#           reject  → Transitions status to REJECTED (rejection_reason required)
#         """
#         try:
#             if not self._is_authority(request.user):
#                 return Response(
#                     {'detail': 'Only the Approving Authority can perform this action.'},
#                     status=status.HTTP_403_FORBIDDEN
#                 )
#
#             from applications.health_center.services import (
#                 approve_inventory_requisition, reject_inventory_requisition
#             )
#
#             approver_id = request.user.extrainfo.id if hasattr(request.user, 'extrainfo') else request.user.id
#
#             if action == 'approve':
#                 # PHC-UC-16: Approve the requisition (SUBMITTED → APPROVED)
#                 serializer = ApproveRequisitionSerializer(data=request.data)
#                 if not serializer.is_valid():
#                     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#                 req = approve_inventory_requisition(pk, approver_id)
#                 req.approval_remarks = serializer.validated_data.get('approval_remarks', '')
#                 req.save(update_fields=['approval_remarks'])
#
#                 # PHC-BR-11 notification is in approve_inventory_requisition() — see services.py
#                 return Response(InventoryRequisitionSerializer(req).data, status=status.HTTP_200_OK)
#
#             elif action == 'reject':
#                 # PHC-UC-16: Reject the requisition (SUBMITTED → REJECTED)
#                 reason = request.data.get('reason', '').strip()
#                 if not reason:
#                     return Response(
#                         {'detail': 'reason is required when rejecting a requisition.'},
#                         status=status.HTTP_400_BAD_REQUEST
#                     )
#
#                 req = reject_inventory_requisition(pk, approver_id, reason)
#
#                 # PHC-BR-11 notification is in reject_inventory_requisition() — see services.py
#                 return Response(InventoryRequisitionSerializer(req).data, status=status.HTTP_200_OK)
#
#             else:
#                 return Response(
#                     {'detail': "Invalid action. Use 'approve' or 'reject'."},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
#
#         except Exception as e:
#             return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ===========================================================================
# ── ANNOUNCEMENTS — PHC-UC-12 ─────────────────────────────────────────────
# ===========================================================================

class AnnouncementView(APIView):
    """
    GET  /api/phc/announcements/        - All authenticated users: list active announcements
    POST /api/phc/announcements/        - PHC staff only: create + broadcast announcement (PHC-UC-12)
    DELETE /api/phc/announcements/<id>/ - PHC staff only: deactivate announcement

    PHC-UC-12  : Broadcast Health Announcements
    PHC-UC-17  : Portal notification fired on create (S-NOTIFY broadcast)
    PHC-BR-09  : Audit-logged create/deactivate events
    """

    def get(self, request):
        """GET: Return all active, non-expired announcements for portal display."""
        from django.utils import timezone
        now = timezone.now()
        announcements = HealthAnnouncement.objects.filter(
            is_active=True
        ).exclude(
            expires_at__lt=now
        ).order_by('-priority', '-created_at')
        serializer = HealthAnnouncementSerializer(announcements, many=True)
        return Response(serializer.data)

    @transaction.atomic
    def post(self, request):
        """POST: Create and broadcast a new health announcement (PHC-UC-12)."""
        if not is_phc_staff(request):
            return Response(
                {'detail': 'Only PHC staff can post announcements.'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            serializer = HealthAnnouncementCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({'detail': str(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)

            from applications.health_center.services import create_announcement
            from applications.globals.models import ExtraInfo

            try:
                extrainfo = ExtraInfo.objects.get(user=request.user)
                created_by_id = extrainfo.id
            except ExtraInfo.DoesNotExist:
                created_by_id = None

            announcement = create_announcement(
                data=serializer.validated_data,
                created_by_id=created_by_id,
                sender_user=request.user,
            )
            return Response(
                HealthAnnouncementSerializer(announcement).data,
                status=status.HTTP_201_CREATED
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @transaction.atomic
    def delete(self, request, announcement_id):
        """DELETE: Deactivate an announcement (soft delete, audit-logged)."""
        if not is_phc_staff(request):
            return Response(
                {'detail': 'Only PHC staff can deactivate announcements.'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            from applications.health_center.services import deactivate_announcement
            from applications.globals.models import ExtraInfo

            try:
                extrainfo = ExtraInfo.objects.get(user=request.user)
                deactivated_by_id = extrainfo.id
            except ExtraInfo.DoesNotExist:
                deactivated_by_id = None

            deactivate_announcement(
                announcement_id=announcement_id,
                deactivated_by_id=deactivated_by_id,
            )
            return Response(
                {'detail': f'Announcement #{announcement_id} deactivated.'},
                status=status.HTTP_200_OK
            )
        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ===========================================================================
# ── SYSTEM REPORTS — PHC-UC-13 ────────────────────────────────────────────
# ===========================================================================

class SystemReportView(APIView):
    """
    GET /api/phc/compounder/reports/
    Generate utilization reports including demographics and inventory consumption.
    PHC-UC-13
    
    Query Params:
      start_date (YYYY-MM-DD): Optiona. Default 30 days ago.
      end_date (YYYY-MM-DD): Optional. Default today.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_phc_staff(request):
            return Response(
                {'detail': 'Only PHC staff can generate reports.'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        from datetime import datetime, timedelta
        from django.utils import timezone
        from django.db.models import Count, Sum
        from ..models import Consultation, PrescribedMedicine
        
        start_str = request.query_params.get('start_date')
        end_str = request.query_params.get('end_date')
        
        try:
            if end_str:
                end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
            else:
                end_date = timezone.now().date()
                
            if start_str:
                start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            else:
                start_date = end_date - timedelta(days=30)
                
        except ValueError:
            return Response(
                {'detail': 'Invalid date format. Use YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ensure start is before end
        if start_date > end_date:
            start_date, end_date = end_date, start_date

        try:
            from django.core.cache import cache
            cache_key = f'system_report_{start_date.strftime("%Y-%m-%d")}_{end_date.strftime("%Y-%m-%d")}'
            cached_data = cache.get(cache_key)
            if cached_data:
                return Response(cached_data, status=status.HTTP_200_OK)

            # 1. Total Visits
            consultations = Consultation.objects.filter(
                consultation_date__range=[start_date, end_date]
            )
            total_visits = consultations.count()

            # 2. Demographics Split (by User Type)
            # Patient -> ExtraInfo -> User_type
            # Typically user_type in ExtraInfo might be 'student', 'faculty', 'staff'
            demo_breakdown = consultations.values(
                'patient__user_type'
            ).annotate(
                count=Count('id')
            )
            demographics = {}
            for item in demo_breakdown:
                u_type = str(item['patient__user_type'] or 'Unknown').capitalize()
                demographics[u_type] = item['count']

            # 3. Inventory Consumption Breakdown
            # Join PrescribedMedicine -> Prescription -> Consultation
            prescribed_meds = PrescribedMedicine.objects.filter(
                prescription__consultation__consultation_date__range=[start_date, end_date]
            ).values(
                'medicine__medicine_name'
            ).annotate(
                total_dispensed=Sum('qty_dispensed')
            ).order_by('-total_dispensed')[:15]  # Top 15 consumed medicines
            
            consumption_data = [
                {
                    'medicine_name': item['medicine__medicine_name'],
                    'total_dispensed': item['total_dispensed']
                } 
                for item in prescribed_meds if item['total_dispensed']
            ]

            # 4. Disease Patterns
            # Annotate disease frequency
            disease_patterns = consultations.values('provisional_diagnosis').annotate(
                count=Count('id')
            ).order_by('-count')[:10]  # Top 10 diseases
            
            diseases_data = [
                {'disease': item['provisional_diagnosis'] or 'Unspecified', 'count': item['count']}
                for item in disease_patterns
            ]

            # Construct final payload
            report_payload = {
                'period': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'days': (end_date - start_date).days + 1
                },
                'metrics': {
                    'total_visits': total_visits,
                    'demographics': demographics,
                },
                'inventory_consumption': consumption_data,
                'disease_patterns': diseases_data
            }

            cache.set(cache_key, report_payload, timeout=3600)

            return Response(report_payload, status=status.HTTP_200_OK)

        except Http404:
            raise
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}', exc_info=True)
            return Response({'detail': 'An unexpected error occurred while processing the request. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)