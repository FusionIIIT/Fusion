"""Consolidated API views for HR2 module.

This module contains all REST API view classes for HR2 form operations,
including LTC, CPDA, Leave, Appraisal forms and management/workflow views.
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import HttpResponse

from applications.hr2.constants.form_types import FormType
from applications.hr2.api.serializers import (
    Appraisal_serializer,
    CPDAAdvance_serializer,
    CPDAReimbursement_serializer,
    Leave_serializer,
    LeaveBalanace_serializer,
    LTC_serializer,
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


# ============================================================================
# Form CRUD Views
# ============================================================================

class LTC(APIView):
    """API view for LTC (Long Term Advance) form operations."""
    serializer_class = LTC_serializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        is_complete, message = _is_profile_complete_for_ltc(request.user)
        if not is_complete:
            return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)
        user_info = request.data[1]
        serializer = self.serializer_class(data=request.data[0])
        if serializer.is_valid():
            instance = serializer.save()
            create_form_file(
                uploader=user_info["uploader_name"],
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
        forms, many = get_forms_for_user(FormType.LTC, username)
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


class CPDAAdvance(APIView):
    """API view for CPDA Advance form operations."""
    serializer_class = CPDAAdvance_serializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user_info = request.data[1]
        serializer = self.serializer_class(data=request.data[0])
        if serializer.is_valid():
            instance = serializer.save()
            create_form_file(
                uploader=user_info["uploader_name"],
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
        forms, many = get_forms_for_user(FormType.CPDA_ADVANCE, username)
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


class CPDAReimbursement(APIView):
    """API view for CPDA Reimbursement form operations."""
    serializer_class = CPDAReimbursement_serializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user_info = request.data[1]
        serializer = self.serializer_class(data=request.data[0])
        if serializer.is_valid():
            instance = serializer.save()
            create_form_file(
                uploader=user_info["uploader_name"],
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
        forms, many = get_forms_for_user(FormType.CPDA_REIMBURSEMENT, username)
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


class Leave(APIView):
    """API view for Leave form operations."""
    serializer_class = Leave_serializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user_info = request.data[1]
        serializer = self.serializer_class(data=request.data[0])
        if serializer.is_valid():
            instance = serializer.save()
            create_form_file(
                uploader=user_info["uploader_name"],
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
        forms, many = get_forms_for_user(FormType.LEAVE, username)
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


class Appraisal(APIView):
    """API view for Appraisal form operations."""
    serializer_class = Appraisal_serializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user_info = request.data[1]
        serializer = self.serializer_class(data=request.data[0])
        if serializer.is_valid():
            instance = serializer.save()
            create_form_file(
                uploader=user_info["uploader_name"],
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
        forms, many = get_forms_for_user(FormType.APPRAISAL, username)
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


class LeaveFormPdfDownload(APIView):
    """Download stored leave application PDF bytes (refactored hr2 endpoint)."""

    permission_classes = (IsAuthenticated,)

    def get(self, request, form_id=None, *args, **kwargs):
        form_id = form_id or request.query_params.get("id")
        if not form_id:
            return Response(
                {"detail": "Missing form id."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            leave = LeaveForm.objects.only("id", "leave_pdf").get(pk=form_id)
        except LeaveForm.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if not leave.leave_pdf:
            return Response(
                {"detail": "No PDF stored for this leave form."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return HttpResponse(
            bytes(leave.leave_pdf),
            content_type="application/pdf",
        )


# ============================================================================
# Form Management & Workflow Views
# ============================================================================

class FormManagement(APIView):
    """API view for form management (inbox operations)."""
    permission_classes = (IsAuthenticated,)

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


class GetFormHistory(APIView):
    """API view to retrieve form history for a user."""
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        form_type = request.query_params.get("type")
        username = request.query_params.get("id")

        if form_type not in _FORM_TYPE_TO_SERIALIZER:
            return Response([], status=status.HTTP_200_OK)

        forms, many = get_forms_for_user(form_type, username)
        serializer_cls = _FORM_TYPE_TO_SERIALIZER[form_type]
        serializer = serializer_cls(forms, many=many)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TrackProgress(APIView):
    """API view to track form workflow progress."""
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        file_id = request.query_params.get("id")
        progress = get_file_history(file_id=file_id)
        return Response({"status": progress}, status=status.HTTP_200_OK)


class FormFetch(APIView):
    """API view to fetch form details with workflow tracking."""
    permission_classes = (IsAuthenticated,)

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


class CheckLeaveBalance(APIView):
    """API view to check and update leave balance."""
    permission_classes = (IsAuthenticated,)
    serializer_class = LeaveBalanace_serializer

    def get(self, request, *args, **kwargs):
        name = request.query_params.get("name")
        person = User.objects.get(username=name)
        extrainfo = ExtraInfo.objects.get(user=person)
        leave_balance = LeaveBalance.objects.get(employeeId=extrainfo)
        serializer = self.serializer_class(leave_balance, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

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


class AllEmployeeLeaveBalances(APIView):
    """API view to fetch all employee leave balances (HR Admin only)."""
    permission_classes = (IsAuthenticated,)

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


class DropDown(APIView):
    """API view to get user designations for dropdown."""
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get("username")
        user = User.objects.get(username=user_id)
        designations = user.holdsdesignation_set.all()
        designation_list = [d.designation.name for d in designations]
        return Response(designation_list, status=status.HTTP_200_OK)


class UserById(APIView):
    """API view to get user information by ID."""
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get("id")
        user = User.objects.get(id=user_id)
        return Response({"username": user.username}, status=status.HTTP_200_OK)


class ViewArchived(APIView):
    """API view to retrieve archived forms."""
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user_name = request.query_params.get("username")
        user_designation = request.query_params.get("designation")
        archived_inbox = get_archived(username=user_name, designation=user_designation)
        return Response(archived_inbox, status=status.HTTP_200_OK)


class GetOutbox(APIView):
    """API view to retrieve outbox."""
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        name = request.query_params.get("username")
        user_designation = request.query_params.get("designation")
        outbox = get_outbox(username=name, designation=user_designation)
        return Response(outbox, status=status.HTTP_200_OK)
