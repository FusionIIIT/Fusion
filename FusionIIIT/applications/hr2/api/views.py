"""Consolidated API views for HR2 module.

This module contains all REST API view classes for HR2 form operations,
including LTC, CPDA, Leave, Appraisal forms and management/workflow views.
"""

import datetime
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from applications.hr2.api.permissions import ModuleAccessHRPermission
from applications.hr2.constants.form_types import FormType
from applications.hr2.api.serializers import (
    Appraisal_serializer,
    CPDAAdvance_serializer,
    CPDAReimbursement_serializer,
    Leave_serializer,
    LeaveBalanace_serializer,
    LTC_serializer,
    ResponsibilityActionSerializer,
)
from applications.hr2.models import ExtraInfo, LeaveBalance, EmpConfidentialDetails, LeaveForm
from applications.hr2.services import (
    get_archived,
    get_file_history,
    get_inbox,
    get_outbox,
    forward_form_file,
    get_forms_for_user,
    get_form_for_type_and_id,
    create_form_file,
    archive_form_file,
)
from applications.filetracking.sdk.methods import (
    get_current_file_owner,
    get_current_file_owner_designation,
)
from applications.globals.models import HoldsDesignation


User = get_user_model()

_FORM_TYPE_TO_SERIALIZER = {
    FormType.LTC: LTC_serializer,
    FormType.CPDA_ADVANCE: CPDAAdvance_serializer,
    FormType.CPDA_REIMBURSEMENT: CPDAReimbursement_serializer,
    FormType.LEAVE: Leave_serializer,
    FormType.APPRAISAL: Appraisal_serializer,
}

_LEAVE_TYPE_TO_ALLOTTED_USED = {
    "casual": ("casual_leave_allotted", "casual_leave_used"),
    "special casual leave": ("special_casual_leave_allotted", "special_casual_leave_used"),
    "special casual": ("special_casual_leave_allotted", "special_casual_leave_used"),
    "earned": ("earned_leave_allotted", "earned_leave_used"),
    "earned leave": ("earned_leave_allotted", "earned_leave_used"),
    "commuted": ("commuted_leave_allotted", "commuted_leave_used"),
    "commuted leave": ("commuted_leave_allotted", "commuted_leave_used"),
    "restricted holiday": ("restricted_holiday_allotted", "restricted_holiday_used"),
    "station leave": ("station_leave_allotted", "station_leave_used"),
    "vacation": ("vacation_leave_allotted", "vacation_leave_used"),
    "vacation leave": ("vacation_leave_allotted", "vacation_leave_used"),
}



def _get_request_designation(request, receiver_payload=None):
    receiver_payload = receiver_payload or {}
    request_data_designation = request.data.get("designation") if isinstance(request.data, dict) else None
    return (
        request.query_params.get("designation")
        or receiver_payload.get("current_designation")
        or receiver_payload.get("uploader_designation")
        or receiver_payload.get("designation")
        or request_data_designation
    )


def _ensure_current_owner_with_designation(request, file_id, receiver_payload=None):
    designation = _get_request_designation(request, receiver_payload=receiver_payload)
    if not designation:
        return Response(
            {"detail": "Current user designation is required for this action."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        current_owner = get_current_file_owner(file_id)
        current_owner_designation = get_current_file_owner_designation(file_id)
    except Exception:
        return Response(
            {"detail": "Unable to verify current owner for this file."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if (
        current_owner != request.user
        or current_owner_designation.name.strip().lower() != designation.strip().lower()
    ):
        return Response(
            {"detail": "Only the current owner with matching designation can perform this action."},
            status=status.HTTP_403_FORBIDDEN,
        )
    return None


def _is_hr_admin(user):
    return HoldsDesignation.objects.filter(
        working=user,
        designation__name__icontains="hr admin",
    ).exists()


def _is_profile_complete_for_ltc(user):
    extra_info = ExtraInfo.objects.filter(user=user).first()
    if not extra_info:
        return False, "Employee profile not found."

    confidential = EmpConfidentialDetails.objects.filter(extra_info=extra_info).first()
    if not confidential:
        return False, "Complete Aadhaar, PAN, and bank details before submitting LTC."

    missing = []
    if not getattr(confidential, "aadhar_no", 0):
        missing.append("Aadhaar")
    if not getattr(confidential, "bank_account_no", 0):
        missing.append("bank account")

    # PAN might be present in newer schema; enforce if available.
    pan_value = getattr(confidential, "pan_no", None) or getattr(confidential, "pan_number", None)
    if hasattr(confidential, "pan_no") or hasattr(confidential, "pan_number"):
        if not pan_value:
            missing.append("PAN")

    if missing:
        return False, f"Complete {', '.join(missing)} details before submitting LTC."
    return True, ""


def _decrement_leave_balance_on_approval(form):
    leave_type = (form.natureOfLeave or "").strip().lower()
    fields = _LEAVE_TYPE_TO_ALLOTTED_USED.get(leave_type)
    if not fields:
        return False, "Unsupported leave type for balance update."

    allotted_f, used_f = fields
    leave_balance = LeaveBalance.objects.filter(employeeId_id=form.employeeId).first()
    if not leave_balance:
        return False, "Leave balance record not found for employee."

    allotted = int(getattr(leave_balance, allotted_f, 0) or 0)
    used = int(getattr(leave_balance, used_f, 0) or 0)
    if allotted - used < 1:
        return False, "Insufficient leave balance to approve this leave."

    setattr(leave_balance, used_f, used + 1)
    leave_balance.save()
    return True, ""


def _ensure_rejection_remarks_if_rejecting(receiver, form_payload):
    if form_payload is None:
        return None
    if form_payload.get("approved") is not False:
        return None
    remark = (receiver or {}).get("remarks") or form_payload.get("rejection_remarks") or ""
    if not str(remark).strip():
        return Response(
            {"detail": "Rejection remarks are required when rejecting."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return None


def _get_appraisal_submission_window():
    start = getattr(settings, "HR2_APPRAISAL_SUBMISSION_START", None)
    end = getattr(settings, "HR2_APPRAISAL_SUBMISSION_END", None)

    if isinstance(start, str):
        try:
            start = datetime.date.fromisoformat(start)
        except ValueError:
            start = None
    if isinstance(end, str):
        try:
            end = datetime.date.fromisoformat(end)
        except ValueError:
            end = None

    return start, end


def _ensure_appraisal_submission_window():
    start, end = _get_appraisal_submission_window()
    if start is None or end is None:
        return None
    today = datetime.date.today()
    if not (start <= today <= end):
        return Response(
            {
                "detail": (
                    f"Appraisal submissions are allowed only between "
                    f"{start.isoformat()} and {end.isoformat()}."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    return None


def _validate_search_query(value, param_name="query"):
    if value is None or str(value).strip() == "":
        return Response(
            {"detail": f"{param_name} parameter must be at least 1 character."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return None


class Hr2APIView(APIView):
    """Base API view for HR2 endpoints enforcing login and HR module access."""

    permission_classes = (IsAuthenticated, ModuleAccessHRPermission,)


# ============================================================================
# Form CRUD Views
# ============================================================================

class LTC(Hr2APIView):
    """API view for LTC (Long Term Advance) form operations."""
    serializer_class = LTC_serializer

    def post(self, request):
        is_complete, message = _is_profile_complete_for_ltc(request.user)
        if not is_complete:
            return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)
        user_info = request.data[1]
        serializer = self.serializer_class(data=request.data[0])
        if serializer.is_valid():
            instance = serializer.save()
            create_form_file(
                uploader=request.user.username,
                uploader_designation=user_info["uploader_designation"],
                receiver=user_info["receiver_name"],
                receiver_designation=user_info["receiver_designation"],
                src_object_id=str(instance.id),
                form_type=FormType.LTC,
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        username = request.query_params.get("name")
        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")
        forms, many = get_forms_for_user(FormType.LTC, username, from_date, to_date)
        serializer = self.serializer_class(forms, many=many)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        form_id = request.query_params.get("id")
        receiver = request.data[0]
        permission_error = _ensure_current_owner_with_designation(
            request,
            file_id=receiver.get("file_id"),
            receiver_payload=receiver,
        )
        if permission_error:
            return permission_error
        form = get_form_for_type_and_id(FormType.LTC, form_id)
        form_payload = request.data[1]
        rem_err = _ensure_rejection_remarks_if_rejecting(receiver, form_payload)
        if rem_err:
            return rem_err
        serializer = self.serializer_class(
            form, data=form_payload, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            forward_form_file(
                file_id=receiver["file_id"],
                receiver=receiver["receiver"],
                receiver_designation=receiver["receiver_designation"],
                remarks=receiver["remarks"],
                file_extra_JSON=receiver["file_extra_JSON"],
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        file_id = request.query_params.get("id")
        if archive_form_file(file_id=file_id):
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class CPDAAdvance(Hr2APIView):
    """API view for CPDA Advance form operations."""
    serializer_class = CPDAAdvance_serializer

    def post(self, request):
        user_info = request.data[1]
        serializer = self.serializer_class(data=request.data[0])
        if serializer.is_valid():
            instance = serializer.save()
            create_form_file(
                uploader=request.user.username,
                uploader_designation=user_info["uploader_designation"],
                receiver=user_info["receiver_name"],
                receiver_designation=user_info["receiver_designation"],
                src_object_id=str(instance.id),
                form_type=FormType.CPDA_ADVANCE,
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        username = request.query_params.get("name")
        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")
        forms, many = get_forms_for_user(FormType.CPDA_ADVANCE, username, from_date, to_date)
        serializer = self.serializer_class(forms, many=many)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        form_id = request.query_params.get("id")
        receiver = request.data[0]
        permission_error = _ensure_current_owner_with_designation(
            request,
            file_id=receiver.get("file_id"),
            receiver_payload=receiver,
        )
        if permission_error:
            return permission_error
        form = get_form_for_type_and_id(FormType.CPDA_ADVANCE, form_id)
        form_payload = request.data[1]
        rem_err = _ensure_rejection_remarks_if_rejecting(receiver, form_payload)
        if rem_err:
            return rem_err
        serializer = self.serializer_class(
            form, data=form_payload, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            forward_form_file(
                file_id=receiver["file_id"],
                receiver=receiver["receiver"],
                receiver_designation=receiver["receiver_designation"],
                remarks=receiver["remarks"],
                file_extra_JSON=receiver["file_extra_JSON"],
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        file_id = request.query_params.get("id")
        if archive_form_file(file_id=file_id):
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class CPDAReimbursement(Hr2APIView):
    """API view for CPDA Reimbursement form operations."""
    serializer_class = CPDAReimbursement_serializer

    def post(self, request):
        user_info = request.data[1]
        serializer = self.serializer_class(data=request.data[0])
        if serializer.is_valid():
            instance = serializer.save()
            create_form_file(
                uploader=request.user.username,
                uploader_designation=user_info["uploader_designation"],
                receiver=user_info["receiver_name"],
                receiver_designation=user_info["receiver_designation"],
                src_object_id=str(instance.id),
                form_type=FormType.CPDA_REIMBURSEMENT,
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        username = request.query_params.get("name")
        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")
        forms, many = get_forms_for_user(FormType.CPDA_REIMBURSEMENT, username, from_date, to_date)
        serializer = self.serializer_class(forms, many=many)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        form_id = request.query_params.get("id")
        receiver = request.data[0]
        permission_error = _ensure_current_owner_with_designation(
            request,
            file_id=receiver.get("file_id"),
            receiver_payload=receiver,
        )
        if permission_error:
            return permission_error
        form = get_form_for_type_and_id(FormType.CPDA_REIMBURSEMENT, form_id)
        form_payload = request.data[1]
        rem_err = _ensure_rejection_remarks_if_rejecting(receiver, form_payload)
        if rem_err:
            return rem_err
        serializer = self.serializer_class(
            form, data=form_payload, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            forward_form_file(
                file_id=receiver["file_id"],
                receiver=receiver["receiver"],
                receiver_designation=receiver["receiver_designation"],
                remarks=receiver["remarks"],
                file_extra_JSON=receiver["file_extra_JSON"],
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        file_id = request.query_params.get("id")
        if archive_form_file(file_id=file_id):
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class Leave(Hr2APIView):
    """API view for Leave form operations."""
    serializer_class = Leave_serializer

    def post(self, request):
        user_info = request.data[1]
        serializer = self.serializer_class(data=request.data[0])
        if serializer.is_valid():
            instance = serializer.save()
            create_form_file(
                uploader=request.user.username,
                uploader_designation=user_info["uploader_designation"],
                receiver=user_info["receiver_name"],
                receiver_designation=user_info["receiver_designation"],
                src_object_id=str(instance.id),
                form_type=FormType.LEAVE,
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        username = request.query_params.get("name")
        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")
        forms, many = get_forms_for_user(FormType.LEAVE, username, from_date, to_date)
        serializer = self.serializer_class(forms, many=many)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        form_id = request.query_params.get("id")
        receiver = request.data[0]
        permission_error = _ensure_current_owner_with_designation(
            request,
            file_id=receiver.get("file_id"),
            receiver_payload=receiver,
        )
        if permission_error:
            return permission_error
        form = get_form_for_type_and_id(FormType.LEAVE, form_id)
        form_payload = request.data[1]
        rem_err = _ensure_rejection_remarks_if_rejecting(receiver, form_payload)
        if rem_err:
            return rem_err
        serializer = self.serializer_class(
            form, data=form_payload, context={"request": request}
        )
        if serializer.is_valid():
            with transaction.atomic():
                previous_approved = form.approved is True
                updated_form = serializer.save()
                now_approved = updated_form.approved is True
                if not previous_approved and now_approved:
                    success, message = _decrement_leave_balance_on_approval(updated_form)
                    if not success:
                        transaction.set_rollback(True)
                        return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)
            forward_form_file(
                file_id=receiver["file_id"],
                receiver=receiver["receiver"],
                receiver_designation=receiver["receiver_designation"],
                remarks=receiver["remarks"],
                file_extra_JSON=receiver["file_extra_JSON"],
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        file_id = request.query_params.get("id")
        if archive_form_file(file_id=file_id):
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class Appraisal(Hr2APIView):
    """API view for Appraisal form operations."""
    serializer_class = Appraisal_serializer

    def post(self, request):
        window_error = _ensure_appraisal_submission_window()
        if window_error:
            return window_error

        user_info = request.data[1]
        serializer = self.serializer_class(data=request.data[0])
        if serializer.is_valid():
            instance = serializer.save()
            create_form_file(
                uploader=request.user.username,
                uploader_designation=user_info["uploader_designation"],
                receiver=user_info["receiver_name"],
                receiver_designation=user_info["receiver_designation"],
                src_object_id=str(instance.id),
                form_type=FormType.APPRAISAL,
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        username = request.query_params.get("name")
        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")
        forms, many = get_forms_for_user(FormType.APPRAISAL, username, from_date, to_date)
        serializer = self.serializer_class(forms, many=many)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        form_id = request.query_params.get("id")
        receiver = request.data[0]
        permission_error = _ensure_current_owner_with_designation(
            request,
            file_id=receiver.get("file_id"),
            receiver_payload=receiver,
        )
        if permission_error:
            return permission_error
        form = get_form_for_type_and_id(FormType.APPRAISAL, form_id)
        form_payload = request.data[1]
        rem_err = _ensure_rejection_remarks_if_rejecting(receiver, form_payload)
        if rem_err:
            return rem_err
        serializer = self.serializer_class(
            form, data=form_payload, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            forward_form_file(
                file_id=receiver["file_id"],
                receiver=receiver["receiver"],
                receiver_designation=receiver["receiver_designation"],
                remarks=receiver["remarks"],
                file_extra_JSON=receiver["file_extra_JSON"],
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        file_id = request.query_params.get("id")
        if archive_form_file(file_id=file_id):
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class LeaveFormPdfDownload(Hr2APIView):
    """Download stored leave application PDF bytes (refactored hr2 endpoint)."""

    def get(self, request, form_id=None, *args, **kwargs):
        form_id = form_id or request.query_params.get("id")
        if not form_id:
            return Response(
                {"detail": "Missing form id."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            leave = LeaveForm.objects.only("id", "leave_pdf", "leave_pdf_file").get(pk=form_id)
        except LeaveForm.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if leave.leave_pdf:
            return HttpResponse(
                bytes(leave.leave_pdf),
                content_type="application/pdf",
            )
        if leave.leave_pdf_file:
            response = HttpResponse(
                leave.leave_pdf_file.read(),
                content_type="application/pdf",
            )
            response["Content-Disposition"] = (
                f'attachment; filename="{os.path.basename(leave.leave_pdf_file.name)}"'
            )
            return response
        return Response(
            {"detail": "No PDF stored for this leave form."},
            status=status.HTTP_404_NOT_FOUND,
        )


class LeaveFormInitials(Hr2APIView):
    """Return authenticated user's baseline details for leave form prefill."""
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        extra_info = ExtraInfo.objects.filter(user=request.user).select_related("department").first()
        if not extra_info:
            return Response(
                {"detail": "Employee profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        full_name = f"{request.user.first_name} {request.user.last_name}".strip()
        designation = (
            extra_info.last_selected_role
            or HoldsDesignation.objects.filter(working=request.user)
            .select_related("designation")
            .values_list("designation__name", flat=True)
            .first()
            or ""
        )

        return Response(
            {
                "name": full_name or request.user.username,
                "last_selected_role": designation,
                "pfno": extra_info.id,
                "department": getattr(extra_info.department, "name", "") or "",
            },
            status=status.HTTP_200_OK,
        )


# ============================================================================
# Form Management & Workflow Views
# ============================================================================

class FormManagement(Hr2APIView):
    """API view for form management (inbox operations)."""

    def get(self, request, *args, **kwargs):
        username = request.query_params.get("username")
        designation = request.query_params.get("designation")
        inbox = get_inbox(username=username, designation=designation)
        return Response(inbox, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        permission_error = _ensure_current_owner_with_designation(
            request,
            file_id=request.data.get("file_id"),
            receiver_payload=request.data,
        )
        if permission_error:
            return permission_error
        forward_form_file(
            file_id=request.data["file_id"],
            receiver=request.data["receiver"],
            receiver_designation=request.data["receiver_designation"],
            remarks=request.data["remarks"],
            file_extra_JSON=request.data["file_extra_JSON"],
        )
        return Response(status=status.HTTP_200_OK)


class GetFormHistory(Hr2APIView):
    """API view to retrieve form history for a user."""

    def get(self, request, *args, **kwargs):
        form_type = request.query_params.get("type")
        username = request.query_params.get("id")
        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")

        if form_type not in _FORM_TYPE_TO_SERIALIZER:
            return Response([], status=status.HTTP_200_OK)

        forms, many = get_forms_for_user(form_type, username, from_date, to_date)
        serializer_cls = _FORM_TYPE_TO_SERIALIZER[form_type]
        serializer = serializer_cls(forms, many=many)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TrackProgress(Hr2APIView):
    """API view to track form workflow progress."""

    def get(self, request, *args, **kwargs):
        file_id = request.query_params.get("id")
        progress = get_file_history(file_id=file_id)
        return Response({"status": progress}, status=status.HTTP_200_OK)


class FormFetch(Hr2APIView):
    """API view to fetch form details with workflow tracking."""

    def get(self, request, *args, **kwargs):
        file_id = request.query_params.get("file_id")
        form_id = request.query_params.get("id")
        form_type = request.query_params.get("type")

        if form_type not in _FORM_TYPE_TO_SERIALIZER:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        form = get_form_for_type_and_id(form_type, form_id)
        serializer_cls = _FORM_TYPE_TO_SERIALIZER[form_type]
        serializer = serializer_cls(form, many=False)
        form_data = serializer.data

        user = User.objects.get(id=int(form_data["created_by"]))

        # When tracking is required, it is generally looked up via Tracking model.
        from applications.filetracking.models import Tracking

        owner_qs = Tracking.objects.filter(file_id=file_id)
        current_owner = None
        if owner_qs.exists():
            current_owner = owner_qs.last().receiver_id.username

        return Response(
            {"form": serializer.data, "creator": user.username, "current_owner": current_owner},
            status=status.HTTP_200_OK
        )


class CheckLeaveBalance(Hr2APIView):
    """API view to check and update leave balance."""
    serializer_class = LeaveBalanace_serializer

    def get(self, request, *args, **kwargs):
        name = request.query_params.get("name") or request.user.username
        try:
            person = User.objects.get(username=name)
            extrainfo = ExtraInfo.objects.get(user=person)
        except (User.DoesNotExist, ExtraInfo.DoesNotExist):
            return Response(
                {"detail": "Leave balance not found for this user."},
                status=status.HTTP_404_NOT_FOUND,
            )

        leave_balance, _ = LeaveBalance.objects.get_or_create(employeeId=extrainfo)
        leave_balance_summary = {
            "casual_leave": {
                "allotted": int(leave_balance.casual_leave_allotted or 0),
                "taken": int(leave_balance.casual_leave_used or 0),
                "balance": int(leave_balance.casualLeave or 0),
            },
            "special_casual_leave": {
                "allotted": int(leave_balance.special_casual_leave_allotted or 0),
                "taken": int(leave_balance.special_casual_leave_used or 0),
                "balance": int(leave_balance.specialCasualLeave or 0),
            },
            "earned_leave": {
                "allotted": int(leave_balance.earned_leave_allotted or 0),
                "taken": int(leave_balance.earned_leave_used or 0),
                "balance": int(leave_balance.earnedLeave or 0),
            },
            "commuted_leave": {
                "allotted": int(leave_balance.commuted_leave_allotted or 0),
                "taken": int(leave_balance.commuted_leave_used or 0),
                "balance": int(leave_balance.commutedLeave or 0),
            },
            "restricted_holiday": {
                "allotted": int(leave_balance.restricted_holiday_allotted or 0),
                "taken": int(leave_balance.restricted_holiday_used or 0),
                "balance": int(leave_balance.restrictedHoliday or 0),
            },
            "station_leave": {
                "allotted": int(leave_balance.station_leave_allotted or 0),
                "taken": int(leave_balance.station_leave_used or 0),
                "balance": int(leave_balance.stationLeave or 0),
            },
            "vacation_leave": {
                "allotted": int(leave_balance.vacation_leave_allotted or 0),
                "taken": int(leave_balance.vacation_leave_used or 0),
                "balance": int(leave_balance.vacationLeave or 0),
            },
        }
        return Response({"leave_balance": leave_balance_summary}, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        if not _is_hr_admin(request.user):
            return Response(
                {"detail": "Only HR Admin can update leave balances."},
                status=status.HTTP_403_FORBIDDEN,
            )
        name = request.query_params.get("name")
        person = User.objects.get(username=name)
        extrainfo = ExtraInfo.objects.get(user=person)
        leave_balance = LeaveBalance.objects.get(employeeId=extrainfo)
        data = request.data
        data["employeeId"] = extrainfo.id
        serializer = self.serializer_class(leave_balance, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AllEmployeeLeaveBalances(Hr2APIView):
    """API view to fetch all employee leave balances (HR Admin only)."""

    def get(self, request, *args, **kwargs):
        if not _is_hr_admin(request.user):
            return Response(
                {"detail": "Only HR Admin can view all employee leave balances."},
                status=status.HTTP_403_FORBIDDEN,
            )

        leave_balances = LeaveBalance.objects.select_related(
            "employeeId", "employeeId__user", "employeeId__department"
        ).all()
        rows = []
        for lb in leave_balances:
            user = lb.employeeId.user
            full_name = f"{user.first_name} {user.last_name}".strip() or user.username
            rows.append({
                "employee_id": lb.employeeId.id,
                "employee_username": user.username,
                "employee_fullname": full_name,
                "department": getattr(lb.employeeId.department, "name", None) or "",
                "casualLeave": lb.casualLeave,
                "casual_leave_allotted": lb.casual_leave_allotted,
                "casual_leave_taken": lb.casual_leave_used,
                "specialCasualLeave": lb.specialCasualLeave,
                "special_casual_leave_allotted": lb.special_casual_leave_allotted,
                "special_casual_leave_taken": lb.special_casual_leave_used,
                "earnedLeave": lb.earnedLeave,
                "earned_leave_allotted": lb.earned_leave_allotted,
                "earned_leave_taken": lb.earned_leave_used,
                "commutedLeave": lb.commutedLeave,
                "commuted_leave_allotted": lb.commuted_leave_allotted,
                "commuted_leave_taken": lb.commuted_leave_used,
                "restrictedHoliday": lb.restrictedHoliday,
                "restricted_holiday_allotted": lb.restricted_holiday_allotted,
                "restricted_holiday_taken": lb.restricted_holiday_used,
                "stationLeave": lb.stationLeave,
                "station_leave_allotted": lb.station_leave_allotted,
                "station_leave_taken": lb.station_leave_used,
                "vacationLeave": lb.vacationLeave,
                "vacation_leave_allotted": lb.vacation_leave_allotted,
                "vacation_leave_taken": lb.vacation_leave_used,
            })
        return Response({"leave_balances": rows}, status=status.HTTP_200_OK)


class DropDown(Hr2APIView):
    """API view to get user designations for dropdown."""

    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get("username")
        validation_error = _validate_search_query(user_id, "username")
        if validation_error:
            return validation_error
        user = User.objects.get(username=user_id)
        designations = user.holdsdesignation_set.all()
        designation_list = [d.designation.name for d in designations]
        return Response(designation_list, status=status.HTTP_200_OK)


class UserById(Hr2APIView):
    """API view to get user information by ID."""

    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get("id")
        validation_error = _validate_search_query(user_id, "id")
        if validation_error:
            return validation_error
        user = User.objects.get(id=user_id)
        return Response({"username": user.username}, status=status.HTTP_200_OK)


class ViewArchived(Hr2APIView):
    """API view to retrieve archived forms."""

    def get(self, request, *args, **kwargs):
        user_name = request.query_params.get("username")
        user_designation = request.query_params.get("designation")
        archived_inbox = get_archived(username=user_name, designation=user_designation)
        return Response(archived_inbox, status=status.HTTP_200_OK)


class GetOutbox(Hr2APIView):
    """API view to retrieve outbox."""

    def get(self, request, *args, **kwargs):
        name = request.query_params.get("username")
        user_designation = request.query_params.get("designation")
        outbox = get_outbox(username=name, designation=user_designation)
        return Response(outbox, status=status.HTTP_200_OK)


class GetMyDetails(Hr2APIView):
    """API view to get current user's details (username and designation)."""

    def get(self, request, *args, **kwargs):
        user = request.user
        extra_info = ExtraInfo.objects.filter(user=user).first()
        
        # Get the user's current designation if available
        designation = None
        if extra_info:
            # Try to get designation from HoldsDesignation (current roles)
            current_role = HoldsDesignation.objects.filter(
                working=user
            ).first()
            if current_role:
                designation = current_role.designation.name
        
        return Response(
            {
                "username": user.username,
                "designation": designation or "N/A",
            },
            status=status.HTTP_200_OK
        )


class SearchEmployee(Hr2APIView):
    """API view to search employees by username."""

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get("search")
        validation_error = _validate_search_query(search_query, "search")
        if validation_error:
            return validation_error
        
        # Search for user by username (case-insensitive)
        user = User.objects.filter(username__icontains=search_query).first()
        if not user:
            return Response(
                {"detail": "Employee not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        extra_info = ExtraInfo.objects.filter(user=user).first()
        
        # Get the user's designation
        designation = None
        if extra_info:
            current_role = HoldsDesignation.objects.filter(
                working=user
            ).first()
            if current_role:
                designation = current_role.designation.name
        
        return Response(
            {
                "username": user.username,
                "designation": designation or "N/A",
            },
            status=status.HTTP_200_OK
        )


# ============================================================================
# URL-slug → FormType mapping for the new REST-style endpoints
# ============================================================================

_URL_SLUG_TO_FORM_TYPE = {
    "cpda_adv": FormType.CPDA_ADVANCE,
    "ltc": FormType.LTC,
    "leave": FormType.LEAVE,
    "appraisal": FormType.APPRAISAL,
}


def _get_user_primary_designation(user):
    """Return the name of the first designation the user holds, or None."""
    hd = HoldsDesignation.objects.filter(
        working=user
    ).select_related("designation").first()
    return hd.designation.name if hd else None


def _filter_files_by_form_type(files, form_type_value):
    """Filter a list of serialized file dicts by file_extra_JSON.type."""
    return [
        f for f in files
        if isinstance(f.get("file_extra_JSON"), dict)
        and f["file_extra_JSON"].get("type") == form_type_value
    ]


# ============================================================================
# Generic form-type-specific views (requests / inbox / archive / track / form)
# ============================================================================

class FormTypeRequests(Hr2APIView):
    """Outbox (submitted forms) filtered by form type."""

    def get(self, request, form_type_slug):
        form_type = _URL_SLUG_TO_FORM_TYPE.get(form_type_slug)
        if not form_type:
            return Response({"detail": "Unknown form type."}, status=status.HTTP_400_BAD_REQUEST)

        designation = _get_user_primary_designation(request.user)
        if not designation:
            return Response({f"{form_type_slug}_requests": []}, status=status.HTTP_200_OK)

        try:
            outbox = get_outbox(username=request.user.username, designation=designation)
        except Exception:
            outbox = []

        filtered = _filter_files_by_form_type(outbox, form_type)
        return Response({f"{form_type_slug}_requests": filtered}, status=status.HTTP_200_OK)


class FormTypeInbox(Hr2APIView):
    """Inbox filtered by form type."""

    def get(self, request, form_type_slug):
        form_type = _URL_SLUG_TO_FORM_TYPE.get(form_type_slug)
        if not form_type:
            return Response({"detail": "Unknown form type."}, status=status.HTTP_400_BAD_REQUEST)

        designation = _get_user_primary_designation(request.user)
        if not designation:
            return Response({f"{form_type_slug}_inbox": []}, status=status.HTTP_200_OK)

        try:
            inbox = get_inbox(username=request.user.username, designation=designation)
        except Exception:
            inbox = []

        filtered = _filter_files_by_form_type(inbox, form_type)
        return Response({f"{form_type_slug}_inbox": filtered}, status=status.HTTP_200_OK)


class FormTypeArchive(Hr2APIView):
    """Archive filtered by form type."""

    def get(self, request, form_type_slug):
        form_type = _URL_SLUG_TO_FORM_TYPE.get(form_type_slug)
        if not form_type:
            return Response({"detail": "Unknown form type."}, status=status.HTTP_400_BAD_REQUEST)

        designation = _get_user_primary_designation(request.user)
        if not designation:
            return Response({f"{form_type_slug}_archive": []}, status=status.HTTP_200_OK)

        try:
            archived = get_archived(username=request.user.username, designation=designation)
        except Exception:
            archived = []

        filtered = _filter_files_by_form_type(archived, form_type)
        return Response({f"{form_type_slug}_archive": filtered}, status=status.HTTP_200_OK)


class FormTypeTrack(Hr2APIView):
    """File tracking history for a given file id."""

    def get(self, request, file_id):
        history = get_file_history(file_id=str(file_id))
        return Response({"file_history": history}, status=status.HTTP_200_OK)


class FormTypeFormDetail(Hr2APIView):
    """Fetch a single form's data by form type slug and form id."""

    def get(self, request, form_type_slug, form_id):
        form_type = _URL_SLUG_TO_FORM_TYPE.get(form_type_slug)
        if not form_type:
            return Response({"detail": "Unknown form type."}, status=status.HTTP_400_BAD_REQUEST)

        serializer_cls = _FORM_TYPE_TO_SERIALIZER.get(form_type)
        if not serializer_cls:
            return Response({"detail": "Unknown form type."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            form = get_form_for_type_and_id(form_type, form_id)
        except Exception:
            return Response({"detail": "Form not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = serializer_cls(form, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================================
# CPDA Claim specific views (nested under cpda/claim/)
# ============================================================================

class CpdaClaimRequests(Hr2APIView):
    """Outbox filtered for CPDA Reimbursement (claim)."""

    def get(self, request):
        designation = _get_user_primary_designation(request.user)
        if not designation:
            return Response({"cpda_claim_requests": []}, status=status.HTTP_200_OK)

        try:
            outbox = get_outbox(username=request.user.username, designation=designation)
        except Exception:
            outbox = []

        filtered = _filter_files_by_form_type(outbox, FormType.CPDA_REIMBURSEMENT)
        return Response({"cpda_claim_requests": filtered}, status=status.HTTP_200_OK)


class CpdaClaimInbox(Hr2APIView):
    """Inbox filtered for CPDA Reimbursement (claim)."""

    def get(self, request):
        designation = _get_user_primary_designation(request.user)
        if not designation:
            return Response({"cpda_claim_inbox": []}, status=status.HTTP_200_OK)

        try:
            inbox = get_inbox(username=request.user.username, designation=designation)
        except Exception:
            inbox = []

        filtered = _filter_files_by_form_type(inbox, FormType.CPDA_REIMBURSEMENT)
        return Response({"cpda_claim_inbox": filtered}, status=status.HTTP_200_OK)


class CpdaClaimArchive(Hr2APIView):
    """Archive filtered for CPDA Reimbursement (claim)."""

    def get(self, request):
        designation = _get_user_primary_designation(request.user)
        if not designation:
            return Response({"cpda_claim_archive": []}, status=status.HTTP_200_OK)

        try:
            archived = get_archived(username=request.user.username, designation=designation)
        except Exception:
            archived = []

        filtered = _filter_files_by_form_type(archived, FormType.CPDA_REIMBURSEMENT)
        return Response({"cpda_claim_archive": filtered}, status=status.HTTP_200_OK)


class CpdaClaimTrack(Hr2APIView):
    """File tracking for CPDA Claim."""

    def get(self, request, file_id):
        history = get_file_history(file_id=str(file_id))
        return Response({"file_history": history}, status=status.HTTP_200_OK)


class CpdaClaimSubmit(Hr2APIView):
    """Submit a CPDA Reimbursement (claim) form."""
    serializer_class = CPDAReimbursement_serializer

    def post(self, request):
        user_info = request.data.get("user_info", request.data[1] if isinstance(request.data, list) else {})
        form_data = request.data.get("form_data", request.data[0] if isinstance(request.data, list) else request.data)
        serializer = self.serializer_class(data=form_data)
        if serializer.is_valid():
            instance = serializer.save()
            create_form_file(
                uploader=user_info.get("uploader_name", request.user.username),
                uploader_designation=user_info.get("uploader_designation", _get_user_primary_designation(request.user) or ""),
                receiver=user_info.get("receiver_name", ""),
                receiver_designation=user_info.get("receiver_designation", ""),
                src_object_id=str(instance.id),
                form_type=FormType.CPDA_REIMBURSEMENT,
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# Appraisal submit view
# ============================================================================

class AppraisalSubmit(Hr2APIView):
    """Submit an Appraisal form."""
    serializer_class = Appraisal_serializer

    def post(self, request):
        window_error = _ensure_appraisal_submission_window()
        if window_error:
            return window_error

        user_info = request.data.get("user_info", request.data[1] if isinstance(request.data, list) else {})
        form_data = request.data.get("form_data", request.data[0] if isinstance(request.data, list) else request.data)
        serializer = self.serializer_class(data=form_data)
        if serializer.is_valid():
            instance = serializer.save()
            create_form_file(
                uploader=user_info.get("uploader_name", request.user.username),
                uploader_designation=user_info.get("uploader_designation", _get_user_primary_designation(request.user) or ""),
                receiver=user_info.get("receiver_name", ""),
                receiver_designation=user_info.get("receiver_designation", ""),
                src_object_id=str(instance.id),
                form_type=FormType.APPRAISAL,
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# Leave-specific views
# ============================================================================

class LeaveSubmit(Hr2APIView):
    """Submit a leave form (POST)."""
    serializer_class = Leave_serializer

    def post(self, request):
        user_info = request.data.get("user_info", request.data[1] if isinstance(request.data, list) else {})
        form_data = request.data.get("form_data", request.data[0] if isinstance(request.data, list) else request.data)
        serializer = self.serializer_class(data=form_data)
        if serializer.is_valid():
            instance = serializer.save()
            create_form_file(
                uploader=user_info.get("uploader_name", request.user.username),
                uploader_designation=user_info.get("uploader_designation", _get_user_primary_designation(request.user) or ""),
                receiver=user_info.get("receiver_name", ""),
                receiver_designation=user_info.get("receiver_designation", ""),
                src_object_id=str(instance.id),
                form_type=FormType.LEAVE,
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeaveFileHandle(Hr2APIView):
    """Handle a leave file action (forward/approve/reject)."""
    serializer_class = Leave_serializer

    def post(self, request, file_id):
        permission_error = _ensure_current_owner_with_designation(
            request, file_id=file_id, receiver_payload=request.data,
        )
        if permission_error:
            return permission_error

        action = request.data.get("action")
        receiver = request.data.get("receiver")
        receiver_designation = request.data.get("receiver_designation")
        remarks = request.data.get("remarks", "")

        if action == "forward" and receiver and receiver_designation:
            forward_form_file(
                file_id=str(file_id),
                receiver=receiver,
                receiver_designation=receiver_designation,
                remarks=remarks,
                file_extra_JSON=request.data.get("file_extra_JSON", {"type": FormType.LEAVE}),
            )
            return Response({"detail": "File forwarded."}, status=status.HTTP_200_OK)

        if action == "archive":
            if archive_form_file(file_id=str(file_id)):
                return Response({"detail": "File archived."}, status=status.HTTP_200_OK)
            return Response({"detail": "Failed to archive."}, status=status.HTTP_400_BAD_REQUEST)

        # Default: try to update form and forward
        form_id = request.data.get("form_id")
        if form_id:
            try:
                form = get_form_for_type_and_id(FormType.LEAVE, form_id)
            except Exception:
                return Response({"detail": "Form not found."}, status=status.HTTP_404_NOT_FOUND)
            form_payload = request.data.get("form_data", {})
            rem_err = _ensure_rejection_remarks_if_rejecting(request.data, form_payload)
            if rem_err:
                return rem_err
            serializer = self.serializer_class(form, data=form_payload, context={"request": request})
            if serializer.is_valid():
                with transaction.atomic():
                    previous_approved = form.approved is True
                    updated_form = serializer.save()
                    now_approved = updated_form.approved is True
                    if not previous_approved and now_approved:
                        success, message = _decrement_leave_balance_on_approval(updated_form)
                        if not success:
                            transaction.set_rollback(True)
                            return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)
                if receiver and receiver_designation:
                    forward_form_file(
                        file_id=str(file_id),
                        receiver=receiver,
                        receiver_designation=receiver_designation,
                        remarks=remarks,
                        file_extra_JSON=request.data.get("file_extra_JSON", {"type": FormType.LEAVE}),
                    )
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)


class LeaveAcademicResponsibility(Hr2APIView):
    """Handle academic responsibility for a leave file."""

    def post(self, request, file_id):
        action = request.data.get("action")
        remarks = request.data.get("remarks", f"Academic responsibility {action}")
        # Forward to next step or archive based on action
        if action == "accept":
            return Response({"detail": "Academic responsibility accepted."}, status=status.HTTP_200_OK)
        elif action == "reject":
            return Response({"detail": "Academic responsibility rejected."}, status=status.HTTP_200_OK)
        return Response({"detail": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)


class LeaveAdministrativeResponsibility(Hr2APIView):
    """Handle administrative responsibility for a leave file."""

    def post(self, request, file_id):
        action = request.data.get("action")
        if action == "accept":
            return Response({"detail": "Administrative responsibility accepted."}, status=status.HTTP_200_OK)
        elif action == "reject":
            return Response({"detail": "Administrative responsibility rejected."}, status=status.HTTP_200_OK)
        return Response({"detail": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)


class OfflineLeaveForm(Hr2APIView):
    """Submit an offline leave form."""
    serializer_class = Leave_serializer

    def post(self, request):
        if not _is_hr_admin(request.user):
            return Response(
                {"detail": "Only HR Admin can submit offline leave forms."},
                status=status.HTTP_403_FORBIDDEN,
            )
        # Handle multipart form data
        form_data = request.data
        serializer = self.serializer_class(data=form_data)
        if serializer.is_valid():
            instance = serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# Search & generic views
# ============================================================================

class SearchEmployeesView(Hr2APIView):
    """Search employees by text query."""

    def get(self, request):
        search_text = request.query_params.get("search_text", "")
        if len(search_text) < 3:
            return Response({"employees": []}, status=status.HTTP_200_OK)

        users = User.objects.filter(username__icontains=search_text)[:20]
        employees = []
        for u in users:
            extra = ExtraInfo.objects.filter(user=u).first()
            hd = HoldsDesignation.objects.filter(working=u).select_related("designation").first()
            employees.append({
                "username": u.username,
                "name": f"{u.first_name} {u.last_name}".strip() or u.username,
                "designation": hd.designation.name if hd else "N/A",
                "department": getattr(extra.department, "name", "") if extra and hasattr(extra, "department") else "",
            })
        return Response({"employees": employees}, status=status.HTTP_200_OK)


class FormTrackGeneric(Hr2APIView):
    """Generic form tracking by file id."""

    def get(self, request, file_id):
        history = get_file_history(file_id=str(file_id))
        return Response({"file_history": history}, status=status.HTTP_200_OK)


class EmployeeDetail(Hr2APIView):
    """Get employee info by employee/user id."""

    def get(self, request, employee_id):
        try:
            user = User.objects.get(pk=employee_id)
        except User.DoesNotExist:
            return Response({"detail": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)

        extra = ExtraInfo.objects.filter(user=user).first()
        hd = HoldsDesignation.objects.filter(working=user).select_related("designation").first()

        return Response({
            "username": user.username,
            "name": f"{user.first_name} {user.last_name}".strip() or user.username,
            "designation": hd.designation.name if hd else "N/A",
            "department": getattr(extra.department, "name", "") if extra and hasattr(extra, "department") else "",
            "pfno": extra.id if extra else None,
        }, status=status.HTTP_200_OK)


class AdminLeaveRequests(Hr2APIView):
    """Admin view of leave requests for a specific employee."""

    def get(self, request, user_id):
        if not _is_hr_admin(request.user):
            return Response(
                {"detail": "Only HR Admin can view employee leave requests."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            target_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        date_filter = request.query_params.get("date")
        forms = LeaveForm.objects.filter(created_by=target_user)
        if date_filter:
            try:
                filter_date = datetime.datetime.strptime(date_filter.strip(), "%Y-%m-%d").date()
                forms = forms.filter(submissionDate__date=filter_date)
            except ValueError:
                pass

        serializer = Leave_serializer(forms, many=True)
        return Response({"leave_requests": serializer.data}, status=status.HTTP_200_OK)


class LtcCreate(Hr2APIView):
    """Create an LTC form (POST) — thin wrapper."""
    serializer_class = LTC_serializer

    def post(self, request):
        is_complete, message = _is_profile_complete_for_ltc(request.user)
        if not is_complete:
            return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)

        user_info = request.data.get("user_info", request.data[1] if isinstance(request.data, list) else {})
        form_data = request.data.get("form_data", request.data[0] if isinstance(request.data, list) else request.data)
        serializer = self.serializer_class(data=form_data)
        if serializer.is_valid():
            instance = serializer.save()
            create_form_file(
                uploader=user_info.get("uploader_name", request.user.username),
                uploader_designation=user_info.get("uploader_designation", _get_user_primary_designation(request.user) or ""),
                receiver=user_info.get("receiver_name", ""),
                receiver_designation=user_info.get("receiver_designation", ""),
                src_object_id=str(instance.id),
                form_type=FormType.LTC,
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# Responsibility Management Views (HR-UC-026, HR-UC-027)
# ============================================================================

class ResponsibilityAction(Hr2APIView):
    """API view for handling academic and administrative responsibility accept/reject actions."""

    def post(self, request, *args, **kwargs):
        """Accept or reject an academic or administrative responsibility."""
        serializer = ResponsibilityActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        form_id = serializer.validated_data['form_id']
        responsibility_type = serializer.validated_data['responsibility_type']
        action = serializer.validated_data['action']
        remarks = serializer.validated_data.get('remarks', '')

        try:
            leave_form = LeaveForm.objects.get(id=form_id)
        except LeaveForm.DoesNotExist:
            return Response(
                {"detail": "Leave form not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Update the appropriate responsibility status
        if responsibility_type == 'academic':
            if action == 'accept':
                leave_form.academicResponsibility_status = 'accepted'
            else:  # reject
                leave_form.academicResponsibility_status = 'rejected'
        elif responsibility_type == 'admin':
            if action == 'accept':
                leave_form.adminResponsibility_status = 'accepted'
            else:  # reject
                leave_form.adminResponsibility_status = 'rejected'

        leave_form.save()

        return Response(
            {
                "status": f"Responsibility {action}ed successfully.",
                "form_id": form_id,
                "responsibility_type": responsibility_type,
                "action": action,
            },
            status=status.HTTP_200_OK,
        )

