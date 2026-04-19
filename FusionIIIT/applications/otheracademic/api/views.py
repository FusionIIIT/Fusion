"""
API views for otheracademic module.
Views are thin - they validate input, call services/selectors, and return responses.
All business logic is in services.py, all DB queries are in selectors.py.
"""
from datetime import datetime

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from applications.otheracademic import services, selectors
from applications.otheracademic.models import LeaveStatusChoices
from .serializers import (
    LeaveFormInputSerializer,
    LeavePGInputSerializer,
    LeaveStatusUpdateSerializer,
    BonafideFormInputSerializer,
    BonafideStatusUpdateSerializer,
    AssistantshipFormInputSerializer,
    AssistantshipStatusUpdateSerializer,
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
    """Fetch pending assistantship requests for TA supervisor approval."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            pending_forms = selectors.get_pending_assistantships_for_ta()
            response_data = [selectors.serialize_assistantship_pending(form) for form in pending_forms]
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": "Error fetching pending forms", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TA_SupervisorUpdateAssistantshipStatus(APIView):
    """Update assistantship status (TA supervisor approval)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AssistantshipStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approved_ids = serializer.validated_data.get('approvedRequests', [])
        rejected_ids = serializer.validated_data.get('rejectedRequests', [])

        try:
            services.update_assistantship_status_ta(approved_ids, rejected_ids)
            return Response({"message": "Assistantship statuses updated successfully"}, status=status.HTTP_200_OK)
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
    """Fetch pending assistantship requests for HOD approval."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
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
    """Update assistantship status (HOD approval)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AssistantshipStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approved_ids = serializer.validated_data.get('approvedRequests', [])
        rejected_ids = serializer.validated_data.get('rejectedRequests', [])

        services.update_assistantship_status_hod(approved_ids, rejected_ids)
        return Response({"message": "Assistantship statuses updated successfully."})


class AcadAdminFetchPendingAssistantshipRequests(APIView):
    """Fetch pending assistantship requests for Academic Admin approval."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pending_forms = selectors.get_pending_assistantships_for_acad_admin()
        response_data = [selectors.serialize_assistantship_pending(form) for form in pending_forms]
        return Response(response_data, status=status.HTTP_200_OK)


class AcadAdminUpdateAssistantshipStatus(APIView):
    """Update assistantship status (Academic Admin approval)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AssistantshipStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approved_ids = serializer.validated_data.get('approvedRequests', [])
        rejected_ids = serializer.validated_data.get('rejectedRequests', [])

        services.update_assistantship_status_acad_admin(approved_ids, rejected_ids)
        return Response({"message": "Assistantship statuses updated successfully."})


class DeanAcadFetchPendingAssistantshipRequests(APIView):
    """Fetch pending assistantship requests for Dean Academic approval."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pending_forms = selectors.get_pending_assistantships_for_dean()
        response_data = [selectors.serialize_assistantship_pending(form) for form in pending_forms]
        return Response(response_data, status=status.HTTP_200_OK)


class DeanAcadUpdateAssistantshipStatus(APIView):
    """Update assistantship status (Dean Academic approval)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AssistantshipStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approved_ids = serializer.validated_data.get('approvedRequests', [])
        rejected_ids = serializer.validated_data.get('rejectedRequests', [])

        services.update_assistantship_status_dean(approved_ids, rejected_ids)
        return Response({"message": "Assistantship statuses updated successfully."})


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

        try:
            assistantship_requests = selectors.get_assistantships_by_roll_no(roll_no)

            response_data = [{
                "rollNo": form.roll_no.id,
                "name": form.student_name,
                "discipline": form.discipline,
                "dateApplied": form.dateApplied.strftime("%Y-%m-%d") if form.dateApplied else None,
                "bank_account": form.bank_account,
                "status": services.get_assistantship_status_text(form),
                "approvalStages": services.get_assistantship_approval_stages(form),
            } for form in assistantship_requests]

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "An error occurred while fetching assistantship status.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
