"""
API views for otheracademic module.
Views are thin - they validate input, call services/selectors, and return responses.
All business logic is in services.py, all DB queries are in selectors.py.
"""
from datetime import datetime

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from notifications.signals import notify

from applications.otheracademic import services, selectors
from applications.otheracademic.models import LeaveStatusChoices, NoDues
from .serializers import (
    LeaveFormInputSerializer,
    LeavePGInputSerializer,
    LeaveStatusUpdateSerializer,
    BonafideFormInputSerializer,
    BonafideStatusUpdateSerializer,
    AssistantshipFormInputSerializer,
    AssistantshipStatusUpdateSerializer,
    TAAssignmentUpdateSerializer,
    FacultySupervisorAssignmentUpdateSerializer,
    NoDuesStatusSerializer,
    NoDuesVerificationSerializer,
    NoDuesCertificateSerializer,
)


# ==================== LEAVE VIEWS ====================

class LeaveFormSubmitView(APIView):
    """Submit a UG leave application."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.POST
        file = request.FILES.get('related_document')

        try:
            leave = services.submit_ug_leave(
                user=request.user,
                date_from=data.get('date_from'),
                date_to=data.get('date_to'),
                leave_type=data.get('leave_type'),
                address=data.get('address'),
                purpose=data.get('purpose'),
                hod_credential=data.get('hod_credential'),
                semester=data.get('semester'),
                mobile_number=data.get('mobile_number'),
                parents_mobile=data.get('parents_mobile'),
                mobile_during_leave=data.get('mobile_during_leave'),
                upload_file=file,
            )
            return Response(
                {"message": "You successfully submitted your form"},
                status=status.HTTP_201_CREATED
            )
        except services.LeaveServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LeavePGSubmitView(APIView):
    """Submit a PG leave application."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.POST
        file = request.FILES.get('related_document')

        try:
            leave = services.submit_pg_leave(
                user=request.user,
                date_from=data.get('date_from'),
                date_to=data.get('date_to'),
                leave_type=data.get('leave_type'),
                address=data.get('address'),
                purpose=data.get('purpose'),
                hod_credential=data.get('hod_credential'),
                ta_supervisor_credential=data.get('ta_superCredential'),
                thesis_supervisor_credential=data.get('thesis_superCredential'),
                semester=data.get('semester'),
                mobile_number=data.get('mobile_number'),
                parents_mobile=data.get('parents_mobile'),
                mobile_during_leave=data.get('mobile_during_leave'),
                upload_file=file,
            )
            return Response(
                {"message": "You successfully submitted your form"},
                status=status.HTTP_201_CREATED
            )
        except services.LeaveServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class FetchPendingLeaveRequests(APIView):
    """Fetch pending leave requests for HOD approval."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not selectors.user_has_designation_contains(request.user, "hod"):
            raise PermissionDenied("Only HOD can access this queue.")

        # Get pending UG leaves
        pending_ug = selectors.get_pending_ug_leaves_for_hod(request.user.username)
        data = [selectors.serialize_ug_leave(leave) for leave in pending_ug]

        # Get pending PG leaves (for HOD)
        pending_pg = selectors.get_pending_pg_leaves_for_hod_user(request.user.username)
        for leave in pending_pg:
            data.append(selectors.serialize_pg_leave(leave))

        return Response(data)


class FetchPendingLeaveRequestsTA(APIView):
    """Fetch pending PG leave requests for TA supervisor approval."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        pending_leaves = selectors.get_pending_pg_leaves_for_ta_user(request.user.username)
        data = [selectors.serialize_pg_leave(leave) for leave in pending_leaves]
        return Response(data)


class FetchPendingLeaveRequestsThesis(APIView):
    """Fetch pending PG leave requests for Thesis supervisor approval."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        pending_leaves = selectors.get_pending_pg_leaves_for_thesis_user(request.user.username)
        data = [selectors.serialize_pg_leave(leave) for leave in pending_leaves]
        return Response(data)


class UpdateLeaveStatus(APIView):
    """Update leave status (HOD approval for UG and final approval for PG)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if not selectors.user_has_designation_contains(request.user, "hod"):
            raise PermissionDenied("Only HOD can approve or reject leave requests.")

        serializer = LeaveStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approved_ids = serializer.validated_data.get('approvedLeaves', [])
        rejected_ids = serializer.validated_data.get('rejectedLeaves', [])

        try:
            services.update_ug_leave_status(approved_ids, rejected_ids, request.user)
            services.update_pg_leave_status_hod(approved_ids, rejected_ids, request.user)
        except services.LeaveServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Leave statuses updated successfully."})


class UpdateLeaveStatusTA(APIView):
    """Update PG leave status (TA supervisor approval)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = LeaveStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approved_ids = serializer.validated_data.get('approvedLeaves', [])
        rejected_ids = serializer.validated_data.get('rejectedLeaves', [])

        try:
            services.update_pg_leave_status_ta(approved_ids, rejected_ids, request.user)
        except services.LeaveServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Leave statuses updated successfully."})


class UpdateLeaveStatusThesis(APIView):
    """Update PG leave status (Thesis supervisor approval)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = LeaveStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approved_ids = serializer.validated_data.get('approvedLeaves', [])
        rejected_ids = serializer.validated_data.get('rejectedLeaves', [])

        try:
            services.update_pg_leave_status_thesis(approved_ids, rejected_ids, request.user)
        except services.LeaveServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Leave statuses updated successfully."})


class GetLeaveRequests(APIView):
    """Get leave requests for a specific student (UG)."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        roll_no_id = request.user.extrainfo.id

        leave_requests = selectors.get_ug_leaves_by_roll_no(roll_no_id)
        data = [selectors.serialize_leave_status(leave, roll_no_id) for leave in leave_requests]

        return Response(data, status=status.HTTP_200_OK)


class GetPGLeaveRequests(APIView):
    """Get leave requests for a specific student (PG)."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        roll_no_id = request.user.extrainfo.id

        leave_requests = selectors.get_pg_leaves_by_roll_no(roll_no_id)
        data = [selectors.serialize_leave_status(leave, roll_no_id) for leave in leave_requests]

        return Response(data, status=status.HTTP_200_OK)


class WithdrawUGLeave(APIView):
    """Withdraw a UG leave request before HOD verifies it."""
    permission_classes = [IsAuthenticated]

    def post(self, request, leave_id, *args, **kwargs):
        try:
            services.withdraw_ug_leave(request.user, leave_id)
            return Response({"message": "Leave request withdrawn successfully."}, status=status.HTTP_200_OK)
        except services.LeaveServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class WithdrawPGLeave(APIView):
    """Withdraw a PG leave request before HOD verifies it."""
    permission_classes = [IsAuthenticated]

    def post(self, request, leave_id, *args, **kwargs):
        try:
            services.withdraw_pg_leave(request.user, leave_id)
            return Response({"message": "PG leave request withdrawn successfully."}, status=status.HTTP_200_OK)
        except services.LeaveServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ==================== BONAFIDE VIEWS ====================

class BonafideFormSubmitView(APIView):
    """Submit a bonafide application."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.POST
        file = request.FILES.get('related_document')

        try:
            bonafide = services.submit_bonafide(
                user=request.user,
                branch=data.get('branch'),
                semester=data.get('semester'),
                purpose=data.get('purpose'),
                download_file=file,
            )
            return Response(
                {"message": "Your bonafide form has been successfully submitted."},
                status=status.HTTP_201_CREATED
            )
        except services.BonafideServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )


class FetchPendingBonafideRequests(APIView):
    """Fetch pending bonafide requests for admin approval."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not selectors.user_has_designation(request.user, "acadadmin"):
            raise PermissionDenied("Only Academic Administrator can access bonafide verification queue.")

        pending_bonafides = selectors.get_pending_bonafides()
        data = [selectors.serialize_pending_bonafide(b) for b in pending_bonafides]
        return Response(data)


class UpdateBonafideStatus(APIView):
    """Update bonafide status (admin approval/rejection)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if not selectors.user_has_designation(request.user, "acadadmin"):
            raise PermissionDenied("Only Academic Administrator can verify bonafide requests.")

        serializer = BonafideStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approved_ids = serializer.validated_data.get('approvedBonafides', [])
        rejected_ids = serializer.validated_data.get('rejectedBonafides', [])

        try:
            services.update_bonafide_status(approved_ids, rejected_ids, request.user)
            return Response({"message": "Bonafide statuses updated successfully."})
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )


class UploadBonafideCertificate(APIView):
    """Upload certificate file for a bonafide request (admin action)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, bonafide_id, *args, **kwargs):
        if not selectors.user_has_designation(request.user, "acadadmin"):
            raise PermissionDenied("Only Academic Administrator can upload bonafide certificates.")

        certificate = request.FILES.get("certificate")
        if not certificate:
            return Response(
                {"error": "certificate file is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            bonafide = services.upload_bonafide_certificate(bonafide_id, certificate)
        except services.BonafideServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "message": "Certificate uploaded successfully.",
                "bonafideId": bonafide.id,
                "downloadUrl": request.build_absolute_uri(bonafide.download_file.url),
            },
            status=status.HTTP_200_OK,
        )


class GetBonafideStatus(APIView):
    """Get bonafide status for a specific student."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        roll_no = request.data.get("roll_no")
        username = request.data.get("username")

        if not roll_no or not username:
            return Response(
                {"error": "Roll number and username are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if str(request.user.extrainfo.id) != str(roll_no):
            return Response(
                {"error": "You can only view your own bonafide status."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            bonafide_requests = selectors.get_bonafides_by_roll_no(roll_no)
            response_data = [selectors.serialize_bonafide_status(b) for b in bonafide_requests]
            for item in response_data:
                if item.get("downloadUrl"):
                    item["downloadUrl"] = request.build_absolute_uri(item["downloadUrl"])
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": "An error occurred while fetching bonafide status.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WithdrawBonafide(APIView):
    """Withdraw a pending bonafide request."""
    permission_classes = [IsAuthenticated]

    def post(self, request, bonafide_id, *args, **kwargs):
        try:
            services.withdraw_bonafide(request.user, bonafide_id)
            return Response({"message": "Bonafide request withdrawn successfully."}, status=status.HTTP_200_OK)
        except services.BonafideServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ==================== ASSISTANTSHIP VIEWS ====================

class AssistantshipFormSubmitView(APIView):
    """Submit an assistantship claim form."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.POST
        files = request.FILES

        try:
            # Parse dates
            date_from = datetime.strptime(data.get('date_from'), '%Y-%m-%d').date()
            date_to = datetime.strptime(data.get('date_to'), '%Y-%m-%d').date()
            date_applied = datetime.strptime(data.get('date_applied'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid date format. Please use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate date range
        if date_from > date_to:
            return Response({"error": "Invalid date range."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate signature file
        signature_file = files.get('signature')
        if not signature_file:
            return Response({"error": "Signature file is missing."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            assistantship = services.submit_assistantship(
                user=request.user,
                discipline=data.get('discipline'),
                date_from=date_from,
                date_to=date_to,
                date_applied=date_applied,
                bank_account=data.get('bank_account_no'),
                signature_file=signature_file,
                ta_supervisor=data.get('ta_supervisor'),
                thesis_supervisor=data.get('thesis_supervisor'),
                hod=data.get('hod'),
                applicability=data.get('applicability'),
            )
            return Response({"message": "Form submitted successfully."}, status=status.HTTP_201_CREATED)
        except services.AssistantshipServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TA_SupervisorFetchPendingAssistantshipRequests(APIView):
    """Fetch pending assistantship requests for faculty supervisor approval."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not selectors.user_has_designation(request.user, "faculty_supervisor"):
            raise PermissionDenied("Only Faculty Supervisor can access this queue.")
        try:
            pending_forms = selectors.get_pending_assistantships_for_ta_user(request.user.username)
            response_data = [selectors.serialize_assistantship_pending(form) for form in pending_forms]
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": "Error fetching pending forms", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TA_SupervisorUpdateAssistantshipStatus(APIView):
    """Update assistantship status (faculty supervisor approval)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not selectors.user_has_designation(request.user, "faculty_supervisor"):
            raise PermissionDenied("Only Faculty Supervisor can review assistantship forms.")

        serializer = AssistantshipStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approved_ids = serializer.validated_data.get('approvedRequests', [])
        rejected_ids = serializer.validated_data.get('rejectedRequests', [])

        try:
            services.update_assistantship_status_ta(approved_ids, rejected_ids, request.user)
            return Response({"message": "Assistantship statuses updated successfully"}, status=status.HTTP_200_OK)
        except services.AssistantshipServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": "Error updating assistantship status", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class Ths_SupervisorFetchPendingAssistantshipRequests(APIView):
    """Fetch pending assistantship requests for Thesis supervisor approval."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            pending_forms = selectors.get_pending_assistantships_for_thesis()
            response_data = [selectors.serialize_assistantship_pending(form) for form in pending_forms]
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": "Error fetching pending forms", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class Ths_SupervisorUpdateAssistantshipStatus(APIView):
    """Update assistantship status (Thesis supervisor approval)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AssistantshipStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approved_ids = serializer.validated_data.get('approvedRequests', [])
        rejected_ids = serializer.validated_data.get('rejectedRequests', [])

        try:
            services.update_assistantship_status_thesis(approved_ids, rejected_ids)
            return Response({"message": "Assistantship statuses updated successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": "Error updating assistantship status", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HODFetchPendingAssistantshipRequests(APIView):
    """Fetch pending assistantship requests for Department Admin approval."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not selectors.user_has_designation(request.user, "dept_admin"):
            raise PermissionDenied("Only Department Admin can access this queue.")
        try:
            pending_forms = selectors.get_pending_assistantships_for_hod()
            response_data = [selectors.serialize_assistantship_pending(form) for form in pending_forms]
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": "Error fetching pending forms", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HODUpdateAssistantshipStatus(APIView):
    """Update assistantship status (Department Admin final approval)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if not selectors.user_has_designation(request.user, "dept_admin"):
            raise PermissionDenied("Only Department Admin can approve assistantship forms.")

        serializer = AssistantshipStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approved_ids = serializer.validated_data.get('approvedRequests', [])
        rejected_ids = serializer.validated_data.get('rejectedRequests', [])

        try:
            services.update_assistantship_status_hod(approved_ids, rejected_ids, request.user)
            return Response({"message": "Assistantship statuses updated successfully."})
        except services.AssistantshipServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AcadAdminFetchPendingAssistantshipRequests(APIView):
    """Fetch pending assistantship requests for Academic Admin disbursement audit."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not selectors.user_has_designation(request.user, "acadadmin"):
            raise PermissionDenied("Only Academic Admin can access this queue.")
        pending_forms = selectors.get_pending_assistantships_for_acad_admin()
        response_data = [selectors.serialize_assistantship_pending(form) for form in pending_forms]
        return Response(response_data, status=status.HTTP_200_OK)


class AcadAdminUpdateAssistantshipStatus(APIView):
    """Update assistantship status (Academic Admin disbursement audit)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if not selectors.user_has_designation(request.user, "acadadmin"):
            raise PermissionDenied("Only Academic Admin can update this stage.")

        serializer = AssistantshipStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approved_ids = serializer.validated_data.get('approvedRequests', [])
        rejected_ids = serializer.validated_data.get('rejectedRequests', [])

        try:
            services.update_assistantship_status_acad_admin(approved_ids, rejected_ids, request.user)
            return Response({"message": "Assistantship statuses updated successfully."})
        except services.AssistantshipServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DeanAcadFetchPendingAssistantshipRequests(APIView):
    """Fetch pending assistantship requests for HOD approval."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not selectors.user_has_designation_contains(request.user, "hod"):
            raise PermissionDenied("Only HOD can access this queue.")
        pending_forms = selectors.get_pending_assistantships_for_dean()
        response_data = [selectors.serialize_assistantship_pending(form) for form in pending_forms]
        return Response(response_data, status=status.HTTP_200_OK)


class DeanAcadUpdateAssistantshipStatus(APIView):
    """Update assistantship status (HOD approval/rejection)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if not selectors.user_has_designation_contains(request.user, "hod"):
            raise PermissionDenied("Only HOD can update this stage.")

        serializer = AssistantshipStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approved_ids = serializer.validated_data.get('approvedRequests', [])
        rejected_ids = serializer.validated_data.get('rejectedRequests', [])

        try:
            services.update_assistantship_status_dean(approved_ids, rejected_ids, request.user)
            return Response({"message": "Assistantship statuses updated successfully."})
        except services.AssistantshipServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DirectorFetchPendingAssistantshipRequests(APIView):
    """Fetch pending assistantship requests for Director approval."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pending_forms = selectors.get_pending_assistantships_for_director()
        response_data = [selectors.serialize_assistantship_pending(form) for form in pending_forms]
        return Response(response_data, status=status.HTTP_200_OK)


class DirectorUpdateAssistantshipStatus(APIView):
    """Update assistantship status (Director approval)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AssistantshipStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approved_ids = serializer.validated_data.get('approvedRequests', [])
        rejected_ids = serializer.validated_data.get('rejectedRequests', [])

        services.update_assistantship_status_director(approved_ids, rejected_ids)
        return Response({"message": "Assistantship statuses updated successfully."})


class GetAssistantshipStatus(APIView):
    """Get assistantship status for a specific student."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        roll_no = request.data.get("roll_no")
        username = request.data.get("username")

        if not roll_no or not username:
            return Response(
                {"error": "Roll number and username are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if str(request.user.extrainfo.id) != str(roll_no):
            return Response(
                {"error": "You can only view your own assistantship status."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            assistantship_requests = selectors.get_assistantships_by_roll_no(roll_no)

            response_data = [{
                "rollNo": form.roll_no.id,
                "name": form.student_name,
                "discipline": form.discipline,
                "id": form.id,
                "dateApplied": form.dateApplied.strftime("%Y-%m-%d") if form.dateApplied else None,
                "bank_account": form.bank_account,
                "status": services.get_assistantship_status_text(form),
                "approvalStages": services.get_assistantship_approval_stages(form),
                "canWithdraw": not form.TA_approved and not form.TA_rejected,
            } for form in assistantship_requests]

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "An error occurred while fetching assistantship status.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WithdrawAssistantship(APIView):
    """Withdraw assistantship form before faculty supervisor review."""
    permission_classes = [IsAuthenticated]

    def post(self, request, form_id, *args, **kwargs):
        try:
            services.withdraw_assistantship(request.user, form_id)
            return Response({"message": "Assistantship form withdrawn successfully."}, status=status.HTTP_200_OK)
        except services.AssistantshipServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class FetchTAAssignmentOptions(APIView):
    """Fetch PG students and subjects for dept_admin TA assignment."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not selectors.user_has_designation(request.user, "dept_admin"):
            raise PermissionDenied("Only Department Admin can access TA assignment options.")

        try:
            data = services.get_pg_ta_assignment_options()
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": "Error fetching TA assignment options", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UpdateTAAssignments(APIView):
    """Create/update TA subject assignments for PG students by dept_admin."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not selectors.user_has_designation(request.user, "dept_admin"):
            raise PermissionDenied("Only Department Admin can update TA assignments.")

        serializer = TAAssignmentUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_count = services.upsert_pg_ta_assignments(
                serializer.validated_data.get("assignments", []),
                request.user,
            )
            return Response(
                {"message": "TA assignments updated successfully.", "updated_count": updated_count},
                status=status.HTTP_200_OK,
            )
        except services.TAAssignmentServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": "Error updating TA assignments", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FetchFacultySupervisorAssignmentOptions(APIView):
    """Fetch PG students and faculty options for dept_admin supervisor assignment."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not selectors.user_has_designation(request.user, "dept_admin"):
            raise PermissionDenied("Only Department Admin can access supervisor assignment options.")

        try:
            data = services.get_pg_faculty_supervisor_assignment_options()
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": "Error fetching faculty supervisor assignment options", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UpdateFacultySupervisorAssignments(APIView):
    """Create/update faculty supervisor assignments for PG students by dept_admin."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not selectors.user_has_designation(request.user, "dept_admin"):
            raise PermissionDenied("Only Department Admin can update faculty supervisor assignments.")

        serializer = FacultySupervisorAssignmentUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_count = services.upsert_pg_faculty_supervisor_assignments(
                serializer.validated_data.get("assignments", []),
                request.user,
            )
            return Response(
                {
                    "message": "Faculty supervisor assignments updated successfully.",
                    "updated_count": updated_count,
                },
                status=status.HTTP_200_OK,
            )
        except services.TAAssignmentServiceError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": "Error updating faculty supervisor assignments", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ==================== NO-DUES VIEWS ====================

def _normalize_designation(name):
    return str(name).strip().lower().replace(" ", "_")


def _ensure_no_dues_approver_designations():
    from applications.globals.models import Designation

    required_designations = [
        ("librarian", "Librarian"),
        ("mess_incharge", "Mess Incharge"),
        ("lab_supervisor", "Lab Supervisor"),
        ("hostel_warden", "Hostel Warden"),
    ]

    for name, full_name in required_designations:
        Designation.objects.get_or_create(
            name=name,
            defaults={"full_name": full_name, "type": "administrative"},
        )


def _get_user_no_dues_roles(user):
    role_names = user.current_designation.values_list("designation__name", flat=True)
    return {_normalize_designation(role_name) for role_name in role_names}


NO_DUES_ROLE_DEPARTMENT_MAP = {
    "librarian": {"library"},
    "mess_incharge": {"mess"},
    "hostel_warden": {"hostel"},
    "lab_supervisor": {
        "ece",
        "physics_lab",
        "mechatronics_lab",
        "cc",
        "workshop",
        "signal_processing_lab",
        "vlsi",
        "design_studio",
        "design_project",
    },
    "acadadmin": {"acad_admin"},
}

NO_DUES_APPROVER_ROLES = set(NO_DUES_ROLE_DEPARTMENT_MAP.keys())


def _approval_status(clear_flag, notclear_flag):
    if clear_flag:
        return "clear"
    if notclear_flag:
        return "not_clear"
    return "pending"


def _lab_supervisor_status(no_dues):
    lab_departments = {
        "ece",
        "physics_lab",
        "mechatronics_lab",
        "cc",
        "workshop",
        "signal_processing_lab",
        "vlsi",
        "design_studio",
        "design_project",
    }
    has_clear = any(getattr(no_dues, f"{dept}_clear") for dept in lab_departments)
    has_not_clear = any(getattr(no_dues, f"{dept}_notclear") for dept in lab_departments)

    if has_not_clear:
        return "not_clear"
    if has_clear:
        return "clear"
    return "pending"


def _no_dues_role_statuses(no_dues):
    return {
        "librarian": _approval_status(no_dues.library_clear, no_dues.library_notclear),
        "mess_incharge": _approval_status(no_dues.mess_clear, no_dues.mess_notclear),
        "hostel_warden": _approval_status(no_dues.hostel_clear, no_dues.hostel_notclear),
        "lab_supervisor": _lab_supervisor_status(no_dues),
        "acad_admin": _approval_status(no_dues.account_clear, no_dues.account_notclear),
    }


def _no_dues_progress_summary(no_dues):
    statuses = _no_dues_role_statuses(no_dues)
    cleared_count = sum(1 for status_value in statuses.values() if status_value == "clear")
    not_cleared_count = sum(1 for status_value in statuses.values() if status_value == "not_clear")
    pending_count = sum(1 for status_value in statuses.values() if status_value == "pending")
    total_count = len(statuses)

    return {
        "statuses": statuses,
        "cleared_count": cleared_count,
        "not_cleared_count": not_cleared_count,
        "pending_count": pending_count,
        "total_count": total_count,
        "progress_percentage": (cleared_count / total_count * 100) if total_count > 0 else 0,
        "all_clear": cleared_count == total_count and not_cleared_count == 0,
    }


class InitiateNoDuesView(APIView):
    """Initiate no-dues clearance process for a student."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            from applications.globals.models import ExtraInfo

            extra_info = ExtraInfo.objects.get(user=request.user)

            if NoDues.objects.filter(roll_no=extra_info).exists():
                return Response(
                    {"error": "No-Dues clearance already initiated. You cannot initiate again."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            no_dues = NoDues.objects.create(
                roll_no=extra_info,
                name=request.user.get_full_name() or request.user.username,
            )

            serializer = NoDuesStatusSerializer(no_dues)
            return Response(
                {
                    "message": "No-Dues clearance initiated successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        except ExtraInfo.DoesNotExist:
            return Response(
                {"error": "Student information not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GetNoDuesStatusView(APIView):
    """Get current no-dues status for a student."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from applications.globals.models import ExtraInfo

            extra_info = ExtraInfo.objects.get(user=request.user)
            no_dues = NoDues.objects.get(roll_no=extra_info)

            serializer = NoDuesStatusSerializer(no_dues)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except NoDues.DoesNotExist:
            return Response(
                {"error": "No-Dues record not found. Please initiate first."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ExtraInfo.DoesNotExist:
            return Response(
                {"error": "Student information not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class VerifyNoDuesView(APIView):
    """Verify no-dues clearance for a department."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            from applications.globals.models import ExtraInfo

            _ensure_no_dues_approver_designations()

            roll_no = request.data.get('roll_no')
            department = request.data.get('department')
            is_clear = request.data.get('is_clear')

            if not all([roll_no, department, is_clear is not None]):
                return Response(
                    {"error": "roll_no, department, and is_clear are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user_roles = _get_user_no_dues_roles(request.user)
            approver_roles = user_roles.intersection(NO_DUES_APPROVER_ROLES)
            has_non_admin_role = any(role_name != 'acadadmin' for role_name in approver_roles)

            if not approver_roles:
                return Response(
                    {
                        "error": "Only librarian, mess incharge, lab supervisor, or hostel warden can verify no-dues."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            allowed_departments = set()
            for role_name in approver_roles:
                allowed_departments.update(NO_DUES_ROLE_DEPARTMENT_MAP[role_name])

            if department not in allowed_departments:
                return Response(
                    {"error": f"You are not authorized to verify department: {department}"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            extra_info = ExtraInfo.objects.get(id=roll_no)
            no_dues = NoDues.objects.get(roll_no=extra_info)

            dept_field_map = {
                'library': ('library_clear', 'library_notclear'),
                'hostel': ('hostel_clear', 'hostel_notclear'),
                'mess': ('mess_clear', 'mess_notclear'),
                'lab_supervisor': ('ece_clear', 'ece_notclear'),
                'acad_admin': ('account_clear', 'account_notclear'),
                'ece': ('ece_clear', 'ece_notclear'),
                'physics_lab': ('physics_lab_clear', 'physics_lab_notclear'),
                'mechatronics_lab': ('mechatronics_lab_clear', 'mechatronics_lab_notclear'),
                'cc': ('cc_clear', 'cc_notclear'),
                'workshop': ('workshop_clear', 'workshop_notclear'),
                'signal_processing_lab': ('signal_processing_lab_clear', 'signal_processing_lab_notclear'),
                'vlsi': ('vlsi_clear', 'vlsi_notclear'),
                'design_studio': ('design_studio_clear', 'design_studio_notclear'),
                'design_project': ('design_project_clear', 'design_project_notclear'),
                'bank': ('bank_clear', 'bank_notclear'),
                'icard_dsa': ('icard_dsa_clear', 'icard_dsa_notclear'),
                'account': ('account_clear', 'account_notclear'),
                'btp_supervisor': ('btp_supervisor_clear', 'btp_supervisor_notclear'),
                'discipline_office': ('discipline_office_clear', 'discipline_office_notclear'),
                'student_gymkhana': ('student_gymkhana_clear', 'student_gymkhana_notclear'),
                'alumni': ('alumni_clear', 'alumni_notclear'),
                'placement_cell': ('placement_cell_clear', 'placement_cell_notclear'),
            }

            if department == 'acad_admin':
                statuses = _no_dues_role_statuses(no_dues)
                first_four_clear = all(
                    statuses[role_name] == 'clear'
                    for role_name in ['librarian', 'mess_incharge', 'hostel_warden', 'lab_supervisor']
                )
                if not first_four_clear:
                    return Response(
                        {"error": "Acad Admin can finalize only after all four authorities clear."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            if department == 'lab_supervisor':
                lab_departments = [
                    'ece',
                    'physics_lab',
                    'mechatronics_lab',
                    'cc',
                    'workshop',
                    'signal_processing_lab',
                    'vlsi',
                    'design_studio',
                    'design_project',
                ]
                for lab_dept in lab_departments:
                    clear_field, notclear_field = dept_field_map[lab_dept]
                    if is_clear:
                        setattr(no_dues, clear_field, True)
                        setattr(no_dues, notclear_field, False)
                    else:
                        setattr(no_dues, clear_field, False)
                        setattr(no_dues, notclear_field, True)
            else:
                clear_field, notclear_field = dept_field_map[department]

                if is_clear:
                    setattr(no_dues, clear_field, True)
                    setattr(no_dues, notclear_field, False)
                else:
                    setattr(no_dues, clear_field, False)
                    setattr(no_dues, notclear_field, True)

            no_dues.save()

            if is_clear:
                approval_label_map = {
                    'library': 'Librarian',
                    'mess': 'Mess Incharge',
                    'hostel': 'Hostel Warden',
                    'lab_supervisor': 'Lab Supervisor',
                    'acad_admin': 'Acad Admin',
                }
                approval_label = approval_label_map.get(department, department)
                notify.send(
                    sender=request.user,
                    recipient=no_dues.roll_no.user,
                    url='/other-academics',
                    module='Other Academic',
                    verb=f'Your no-dues request was approved by {approval_label}.',
                )

            serializer = NoDuesStatusSerializer(no_dues)
            return Response(
                {
                    "message": f"No-Dues cleared by {department}",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except NoDues.DoesNotExist:
            return Response(
                {"error": "No-Dues record not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TrackNoDuesProgressView(APIView):
    """Track progress of no-dues clearance."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from applications.globals.models import ExtraInfo

            extra_info = ExtraInfo.objects.get(user=request.user)
            no_dues = NoDues.objects.get(roll_no=extra_info)
            summary = _no_dues_progress_summary(no_dues)

            return Response({
                "roll_no": extra_info.id,
                "name": no_dues.name,
                "cleared": summary["cleared_count"],
                "not_cleared": summary["not_cleared_count"],
                "pending": summary["pending_count"],
                "total": summary["total_count"],
                "progress_percentage": summary["progress_percentage"],
                "departments": summary["statuses"],
                "all_clear": summary["all_clear"],
            }, status=status.HTTP_200_OK)

        except NoDues.DoesNotExist:
            return Response(
                {"error": "No-Dues record not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ExtraInfo.DoesNotExist:
            return Response(
                {"error": "Student information not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class ListPendingNoDuesView(APIView):
    """List all students with pending no-dues clearance requests."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            _ensure_no_dues_approver_designations()

            user_roles = _get_user_no_dues_roles(request.user)
            approver_roles = user_roles.intersection(NO_DUES_APPROVER_ROLES)
            has_non_admin_role = any(role_name != 'acadadmin' for role_name in approver_roles)
            if not approver_roles:
                return Response(
                    {
                        "error": "Only librarian, mess incharge, lab supervisor, or hostel warden can view pending no-dues requests."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            pending_clearances = NoDues.objects.all()

            data = []
            for no_dues in pending_clearances:
                summary = _no_dues_progress_summary(no_dues)
                statuses = summary["statuses"]
                first_four_clear = all(
                    statuses[role_name] == 'clear'
                    for role_name in ['librarian', 'mess_incharge', 'hostel_warden', 'lab_supervisor']
                )

                show_for_non_admin_queue = has_non_admin_role and not first_four_clear
                show_for_acadadmin_queue = (
                    'acadadmin' in approver_roles
                    and first_four_clear
                    and statuses['acad_admin'] != 'clear'
                )

                if not (show_for_non_admin_queue or show_for_acadadmin_queue):
                    continue

                available_approvals = []
                if has_non_admin_role:
                    non_admin_targets = [
                        ('library', 'librarian'),
                        ('mess', 'mess_incharge'),
                        ('hostel', 'hostel_warden'),
                        ('lab_supervisor', 'lab_supervisor'),
                    ]
                    available_approvals.extend(
                        target
                        for target, status_key in non_admin_targets
                        if statuses.get(status_key) == 'pending'
                    )

                if 'acadadmin' in approver_roles and first_four_clear and statuses.get('acad_admin') == 'pending':
                    available_approvals.append('acad_admin')

                if summary["all_clear"]:
                    continue

                data.append({
                    'roll_no': no_dues.roll_no.id,
                    'name': no_dues.name,
                    'cleared_count': summary["cleared_count"],
                    'total_count': summary["total_count"],
                    'progress_percentage': summary["progress_percentage"],
                    'departments': summary["statuses"],
                    'available_approvals': list(dict.fromkeys(available_approvals)),
                })

            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DownloadNoDuesCertificateView(APIView):
    """Download no-dues certificate (if fully cleared)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from applications.globals.models import ExtraInfo
            from django.http import HttpResponse
            from io import BytesIO

            extra_info = ExtraInfo.objects.get(user=request.user)
            no_dues = NoDues.objects.get(roll_no=extra_info)
            summary = _no_dues_progress_summary(no_dues)

            if not summary["all_clear"]:
                return Response(
                    {"error": "Student has not cleared all departments yet"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            blank_pdf = b"""%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << >> >>\nendobj\n4 0 obj\n<< /Length 0 >>\nstream\n\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000061 00000 n \n0000000118 00000 n \n0000000243 00000 n \ntrailer\n<< /Root 1 0 R /Size 5 >>\nstartxref\n284\n%%EOF"""

            response = HttpResponse(blank_pdf, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="{extra_info.id}_nodues.pdf"'
            response["Content-Length"] = str(len(blank_pdf))
            return response

        except NoDues.DoesNotExist:
            return Response(
                {"error": "No-Dues record not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ExtraInfo.DoesNotExist:
            return Response(
                {"error": "Student information not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": f"Error generating certificate: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
