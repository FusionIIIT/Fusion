"""Consolidated API views for HR2 module.

This module contains all REST API view classes for HR2 form operations,
including LTC, CPDA, Leave, Appraisal forms and management/workflow views.
"""

import datetime
import logging
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
from applications.filetracking.models import File
from applications.hr2.models import (
    CPDAAdvanceform,
    ExtraInfo,
    LeaveBalance,
    EmpConfidentialDetails,
    LeaveForm,
    LTCform,
    Appraisalform,
)
from applications.hr2.workflow import appraisal as appraisal_wf
from applications.hr2.workflow import cpda_advance as cpda_wf
from applications.hr2.workflow import ltc as ltc_wf
from applications.hr2.services import (
    get_archived,
    get_archived_for_all_held_designations,
    get_file_history,
    get_inbox,
    get_inbox_for_all_held_designations,
    get_outbox,
    get_outbox_for_all_held_designations,
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


class Hr2AuthenticatedAPIView(APIView):
    """Logged-in users only (self-service forms, inbox, track). Not gated on ModuleAccess.hr."""

    permission_classes = (IsAuthenticated,)


# ============================================================================
# Form CRUD Views
# ============================================================================

def _submit_ltc_application(request, form_data, user_info):
    """Create LTC row, filetracking entry, and initial workflow state.

    Returns:
        (dict, None) with serialized form data on success,
        (None, Response) on error.
    """
    receiver = (user_info.get("receiver_name") or "").strip()
    recv_desig = (user_info.get("receiver_designation") or "").strip()
    if not receiver or not recv_desig:
        return None, Response(
            {"detail": "Approver username and designation are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    uploader_desig = (
        user_info.get("uploader_designation")
        or _get_user_primary_designation(request.user)
        or ""
    )
    if not uploader_desig:
        return None, Response(
            {"detail": "Your designation could not be determined. Cannot submit."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = LTC_serializer(data=form_data)
    if not serializer.is_valid():
        return None, Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    instance = serializer.save(created_by=request.user)
    try:
        create_form_file(
            uploader=request.user.username,
            uploader_designation=uploader_desig,
            receiver=receiver,
            receiver_designation=recv_desig,
            src_object_id=str(instance.id),
            form_type=FormType.LTC,
            file_extra_JSON={"workflow_status": ltc_wf.WF_SUBMITTED},
        )
    except Exception as e:
        logging.getLogger(__name__).error("File tracking failed for LTC: %s", e)
        instance.delete()
        return None, Response(
            {"detail": f"File tracking failed: {e!s}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    ltc_wf.append_workflow_event(
        instance,
        ltc_wf.WF_SUBMITTED,
        request.user.username,
        "Application submitted",
    )
    refreshed = get_form_for_type_and_id(FormType.LTC, instance.id)
    return LTC_serializer(refreshed).data, None


def _submit_appraisal_application(request, form_data, user_info):
    """Create Appraisal row, filetracking entry, and initial workflow state."""
    window_error = _ensure_appraisal_submission_window()
    if window_error:
        return None, window_error

    receiver = (user_info.get("receiver_name") or "").strip()
    recv_desig = (user_info.get("receiver_designation") or "").strip()
    if not receiver or not recv_desig:
        return None, Response(
            {"detail": "Approver username and designation are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    uploader_desig = (
        user_info.get("uploader_designation")
        or _get_user_primary_designation(request.user)
        or ""
    )
    if not uploader_desig:
        return None, Response(
            {"detail": "Your designation could not be determined. Cannot submit."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = Appraisal_serializer(data=form_data)
    if not serializer.is_valid():
        return None, Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    instance = serializer.save(created_by=request.user)
    try:
        create_form_file(
            uploader=request.user.username,
            uploader_designation=uploader_desig,
            receiver=receiver,
            receiver_designation=recv_desig,
            src_object_id=str(instance.id),
            form_type=FormType.APPRAISAL,
            file_extra_JSON={"workflow_status": appraisal_wf.WF_SUBMITTED},
        )
    except Exception as e:
        logging.getLogger(__name__).error("File tracking failed for Appraisal: %s", e)
        instance.delete()
        return None, Response(
            {"detail": f"File tracking failed: {e!s}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    appraisal_wf.append_workflow_event(
        instance,
        appraisal_wf.WF_SUBMITTED,
        request.user.username,
        "Appraisal submitted",
    )
    refreshed = get_form_for_type_and_id(FormType.APPRAISAL, instance.id)
    return Appraisal_serializer(refreshed).data, None


class LTC(Hr2APIView):
    """API view for LTC (Long Term Advance) form operations."""
    serializer_class = LTC_serializer

    def post(self, request):
        is_complete, message = _is_profile_complete_for_ltc(request.user)
        if not is_complete:
            return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)
        if isinstance(request.data, list):
            form_data = request.data[0] if len(request.data) > 0 else {}
            user_info = request.data[1] if len(request.data) > 1 else {}
        else:
            form_data = request.data.get("form_data", request.data)
            user_info = request.data.get("user_info", {})
        data, err = _submit_ltc_application(request, form_data, user_info)
        if err:
            return err
        return Response(data, status=status.HTTP_200_OK)

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
    """API view for CPDA Advance form operations (submission routes to department HOD)."""
    serializer_class = CPDAAdvance_serializer

    def get_permissions(self):
        # Faculty/staff submit and list their own forms without globals.ModuleAccess.hr.
        if self.request.method in ("POST", "GET"):
            return [IsAuthenticated()]
        return [IsAuthenticated(), ModuleAccessHRPermission()]

    def post(self, request):
        if isinstance(request.data, list):
            form_data = request.data[0] if len(request.data) > 0 else {}
            user_info = request.data[1] if len(request.data) > 1 else {}
        else:
            form_data = request.data.get("form_data", request.data)
            user_info = request.data.get("user_info", {})
        user_info = user_info or {}
        serializer = self.serializer_class(data=form_data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        hod_user, hod_desig = cpda_wf.resolve_hod_for_applicant(request.user)
        if not hod_user:
            return Response(
                {
                    "detail": (
                        "No HOD is configured for your department. "
                        "Ask an administrator to create the HOD designation and assign a holder."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        uploader_desig = (
            user_info.get("uploader_designation")
            or _get_user_primary_designation(request.user)
            or ""
        )
        if not uploader_desig:
            return Response(
                {"detail": "Your designation could not be determined. Cannot submit."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        import logging

        instance = serializer.save(created_by=request.user)
        try:
            create_form_file(
                uploader=request.user.username,
                uploader_designation=uploader_desig,
                receiver=hod_user,
                receiver_designation=hod_desig,
                src_object_id=str(instance.id),
                form_type=FormType.CPDA_ADVANCE,
                file_extra_JSON={"workflow_status": cpda_wf.WF_SUBMITTED},
            )
        except Exception as e:
            logging.getLogger(__name__).error("File tracking failed for CPDA Advance: %s", e)
            instance.delete()
            return Response(
                {"detail": f"File tracking failed: {e!s}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        cpda_wf.append_workflow_event(
            instance,
            cpda_wf.WF_SUBMITTED,
            request.user.username,
            "Application submitted",
        )

        refreshed = get_form_for_type_and_id(FormType.CPDA_ADVANCE, instance.id)
        return Response(
            self.serializer_class(refreshed).data,
            status=status.HTTP_200_OK,
        )

    def get(self, request, *args, **kwargs):
        username = request.query_params.get("name")
        if username and username != request.user.username and not _is_hr_admin(request.user):
            return Response(
                {"detail": "You may only list CPDA Advance forms for your own account."},
                status=status.HTTP_403_FORBIDDEN,
            )
        lookup_user = username or request.user.username
        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")
        forms, many = get_forms_for_user(
            FormType.CPDA_ADVANCE, lookup_user, from_date, to_date
        )
        serializer = self.serializer_class(forms, many=many)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        if not _is_hr_admin(request.user):
            return Response(
                {
                    "detail": (
                        "CPDA Advance workflow changes must be made through the workflow API "
                        "(or contact HR Admin for data corrections)."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )
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


class CPDAAdvanceWorkflowHandle(Hr2AuthenticatedAPIView):
    """Role-based actions for CPDA Advance (HOD → Director → Accountant)."""

    def post(self, request, file_id):
        action = (request.data.get("action") or "").strip()
        designation = request.data.get("designation") or _get_request_designation(request)
        remarks = (request.data.get("remarks") or "").strip()

        perm_err = _ensure_current_owner_with_designation(
            request,
            file_id=file_id,
            receiver_payload=request.data,
        )
        if perm_err:
            return perm_err

        try:
            file_obj = File.objects.get(pk=file_id)
        except File.DoesNotExist:
            return Response({"detail": "File not found."}, status=status.HTTP_404_NOT_FOUND)

        extra = file_obj.file_extra_JSON or {}
        if extra.get("type") != FormType.CPDA_ADVANCE:
            return Response({"detail": "Not a CPDA Advance file."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            form = get_form_for_type_and_id(
                FormType.CPDA_ADVANCE, int(file_obj.src_object_id)
            )
        except Exception:
            return Response({"detail": "Form not found."}, status=status.HTTP_404_NOT_FOUND)

        if form.workflow_status in cpda_wf.TERMINAL_STATUSES:
            return Response(
                {"detail": "This application is already closed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username = request.user.username

        def _forward_extra(status_key):
            return {"type": FormType.CPDA_ADVANCE, "workflow_status": status_key}

        if action == "hod_verify":
            if not cpda_wf.designation_is_hod(designation):
                return Response({"detail": "Only HOD can verify."}, status=status.HTTP_403_FORBIDDEN)
            if not cpda_wf.hod_covers_applicant(designation, form.created_by):
                return Response(
                    {"detail": "You are not the HOD for this applicant's department."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if form.workflow_status != cpda_wf.WF_SUBMITTED:
                return Response(
                    {"detail": "Application is not awaiting HOD verification."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            dir_user, dir_desig = cpda_wf.resolve_director()
            if not dir_user:
                return Response(
                    {
                        "detail": (
                            "Director is not configured (no user holds the Director designation)."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Verify and immediately route the file to the Director so the inbox updates.
            # (Previously only workflow_status changed; physical file routing required a second
            # "Forward" step, so the Director saw an empty inbox.)
            with transaction.atomic():
                cpda_wf.append_workflow_event(
                    form, cpda_wf.WF_HOD_VERIFIED, username, remarks or "Verified by HOD"
                )
                cpda_wf.sync_file_extra_workflow(file_obj, cpda_wf.WF_HOD_VERIFIED)
                forward_form_file(
                    file_id=str(file_id),
                    receiver=dir_user,
                    receiver_designation=dir_desig,
                    remarks=remarks or "Verified by HOD — forwarded to Director",
                    file_extra_JSON=_forward_extra(cpda_wf.WF_FORWARDED_DIRECTOR),
                )
                cpda_wf.append_workflow_event(
                    form,
                    cpda_wf.WF_FORWARDED_DIRECTOR,
                    username,
                    remarks or "Forwarded to Director",
                )
                file_obj.refresh_from_db()
                cpda_wf.sync_file_extra_workflow(file_obj, cpda_wf.WF_FORWARDED_DIRECTOR)
            return Response(
                {
                    "detail": "Verified and forwarded to Director.",
                    "workflow_status": form.workflow_status,
                }
            )

        if action == "hod_not_verify":
            if not cpda_wf.designation_is_hod(designation):
                return Response({"detail": "Only HOD can reject at this stage."}, status=status.HTTP_403_FORBIDDEN)
            if not cpda_wf.hod_covers_applicant(designation, form.created_by):
                return Response(
                    {"detail": "You are not the HOD for this applicant's department."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if form.workflow_status != cpda_wf.WF_SUBMITTED:
                return Response(
                    {"detail": "Application is not awaiting HOD verification."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            with transaction.atomic():
                cpda_wf.append_workflow_event(
                    form,
                    cpda_wf.WF_HOD_NOT_VERIFIED,
                    username,
                    remarks or "Not verified by HOD",
                    approved=False,
                )
                cpda_wf.sync_file_extra_workflow(file_obj, cpda_wf.WF_HOD_NOT_VERIFIED)
                archive_form_file(file_id=str(file_id))
            return Response({"detail": "Marked as not verified.", "workflow_status": form.workflow_status})

        if action == "hod_forward":
            if not cpda_wf.designation_is_hod(designation):
                return Response({"detail": "Only HOD can forward to the Director."}, status=status.HTTP_403_FORBIDDEN)
            if not cpda_wf.hod_covers_applicant(designation, form.created_by):
                return Response(
                    {"detail": "You are not the HOD for this applicant's department."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if form.workflow_status != cpda_wf.WF_HOD_VERIFIED:
                return Response(
                    {"detail": "Verify the application before forwarding to the Director."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            dir_user, dir_desig = cpda_wf.resolve_director()
            if not dir_user:
                return Response(
                    {"detail": "Director is not configured (no user holds the Director designation)."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            with transaction.atomic():
                forward_form_file(
                    file_id=str(file_id),
                    receiver=dir_user,
                    receiver_designation=dir_desig,
                    remarks=remarks or "Forwarded to Director (Sanctioning Authority)",
                    file_extra_JSON=_forward_extra(cpda_wf.WF_FORWARDED_DIRECTOR),
                )
                cpda_wf.append_workflow_event(
                    form,
                    cpda_wf.WF_FORWARDED_DIRECTOR,
                    username,
                    remarks or "Forwarded to Director",
                )
                file_obj.refresh_from_db()
                cpda_wf.sync_file_extra_workflow(file_obj, cpda_wf.WF_FORWARDED_DIRECTOR)
            return Response({"detail": "Forwarded to Director.", "workflow_status": form.workflow_status})

        if action == "director_approve":
            if not cpda_wf.designation_is_director(designation):
                return Response({"detail": "Only the Director can approve."}, status=status.HTTP_403_FORBIDDEN)
            if form.workflow_status != cpda_wf.WF_FORWARDED_DIRECTOR:
                return Response(
                    {"detail": "Application is not with the Director for approval."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            acct_user, acct_desig = cpda_wf.resolve_accountant()
            if not acct_user:
                return Response(
                    {"detail": "Accountant is not configured."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            with transaction.atomic():
                forward_form_file(
                    file_id=str(file_id),
                    receiver=acct_user,
                    receiver_designation=acct_desig,
                    remarks=remarks or "Approved by Director; forwarded to Accountant",
                    file_extra_JSON=_forward_extra(cpda_wf.WF_DIRECTOR_APPROVED),
                )
                cpda_wf.append_workflow_event(
                    form,
                    cpda_wf.WF_DIRECTOR_APPROVED,
                    username,
                    remarks or "Approved by Director",
                    approved=True,
                    approved_by=request.user,
                    approvedDate=datetime.date.today(),
                )
                file_obj.refresh_from_db()
                cpda_wf.sync_file_extra_workflow(file_obj, cpda_wf.WF_DIRECTOR_APPROVED)
            return Response({"detail": "Approved and sent to Accountant.", "workflow_status": form.workflow_status})

        if action == "director_reject":
            if not cpda_wf.designation_is_director(designation):
                return Response({"detail": "Only the Director can reject."}, status=status.HTTP_403_FORBIDDEN)
            if form.workflow_status != cpda_wf.WF_FORWARDED_DIRECTOR:
                return Response(
                    {"detail": "Application is not with the Director."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not remarks:
                return Response(
                    {"detail": "Remarks are required when rejecting."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            with transaction.atomic():
                cpda_wf.append_workflow_event(
                    form,
                    cpda_wf.WF_DIRECTOR_REJECTED,
                    username,
                    remarks,
                    approved=False,
                )
                cpda_wf.sync_file_extra_workflow(file_obj, cpda_wf.WF_DIRECTOR_REJECTED)
                archive_form_file(file_id=str(file_id))
            return Response({"detail": "Rejected.", "workflow_status": form.workflow_status})

        if action == "accountant_complete":
            if not cpda_wf.designation_is_accountant(designation):
                return Response(
                    {"detail": "Only the Accountant can complete processing."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if form.workflow_status != cpda_wf.WF_DIRECTOR_APPROVED:
                return Response(
                    {"detail": "Application is not awaiting accountant processing."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            with transaction.atomic():
                cpda_wf.append_workflow_event(
                    form,
                    cpda_wf.WF_ACCOUNTANT_PROCESSED,
                    username,
                    remarks or "Processing completed by Accountant",
                )
                cpda_wf.sync_file_extra_workflow(file_obj, cpda_wf.WF_ACCOUNTANT_PROCESSED)
                archive_form_file(file_id=str(file_id))
            return Response({"detail": "Processing completed.", "workflow_status": form.workflow_status})

        return Response({"detail": "Unknown or missing action."}, status=status.HTTP_400_BAD_REQUEST)


class LTCWorkflowHandle(Hr2AuthenticatedAPIView):
    """HR Admin (or chosen approver with HR Admin role) approves/rejects; approval forwards to Accountant."""

    def post(self, request, file_id):
        action = (request.data.get("action") or "").strip()
        designation = request.data.get("designation") or _get_request_designation(request)
        remarks = (request.data.get("remarks") or "").strip()

        perm_err = _ensure_current_owner_with_designation(
            request,
            file_id=file_id,
            receiver_payload=request.data,
        )
        if perm_err:
            return perm_err

        try:
            file_obj = File.objects.get(pk=file_id)
        except File.DoesNotExist:
            return Response({"detail": "File not found."}, status=status.HTTP_404_NOT_FOUND)

        extra = file_obj.file_extra_JSON or {}
        if extra.get("type") != FormType.LTC:
            return Response({"detail": "Not an LTC file."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            form = get_form_for_type_and_id(FormType.LTC, int(file_obj.src_object_id))
        except Exception:
            return Response({"detail": "Form not found."}, status=status.HTTP_404_NOT_FOUND)

        if form.workflow_status in ltc_wf.TERMINAL_STATUSES:
            return Response(
                {"detail": "This application is already closed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username = request.user.username

        if action == "hr_admin_approve":
            if not ltc_wf.designation_is_hr_admin(designation):
                return Response(
                    {"detail": "Only HR Admin can approve at this stage."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if form.workflow_status != ltc_wf.WF_SUBMITTED:
                return Response(
                    {"detail": "Application is not awaiting HR approval."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            acct_user, acct_desig = ltc_wf.resolve_accountant()
            if not acct_user:
                return Response(
                    {"detail": "Accountant is not configured (no user holds the Accountant designation)."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            with transaction.atomic():
                forward_form_file(
                    file_id=str(file_id),
                    receiver=acct_user,
                    receiver_designation=acct_desig,
                    remarks=remarks or "Approved by HR; forwarded to Accountant",
                    file_extra_JSON={
                        "type": FormType.LTC,
                        "workflow_status": ltc_wf.WF_WITH_ACCOUNTANT,
                    },
                )
                ltc_wf.append_workflow_event(
                    form,
                    ltc_wf.WF_HR_APPROVED,
                    username,
                    remarks or "Approved by HR",
                    approved=True,
                    approved_by=request.user,
                    approvedDate=datetime.date.today(),
                )
                ltc_wf.append_workflow_event(
                    form,
                    ltc_wf.WF_WITH_ACCOUNTANT,
                    username,
                    remarks or "Forwarded to Accountant",
                )
                file_obj.refresh_from_db()
                ltc_wf.sync_file_extra_workflow(file_obj, ltc_wf.WF_WITH_ACCOUNTANT)
            refreshed = get_form_for_type_and_id(FormType.LTC, form.id)
            return Response(
                {
                    "detail": "Approved and sent to Accountant.",
                    "workflow_status": refreshed.workflow_status,
                    "form": LTC_serializer(refreshed).data,
                }
            )

        if action == "hr_admin_reject":
            if not ltc_wf.designation_is_hr_admin(designation):
                return Response(
                    {"detail": "Only HR Admin can reject at this stage."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if form.workflow_status != ltc_wf.WF_SUBMITTED:
                return Response(
                    {"detail": "Application is not awaiting HR approval."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not remarks:
                return Response(
                    {"detail": "Remarks are required when rejecting."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            with transaction.atomic():
                ltc_wf.append_workflow_event(
                    form,
                    ltc_wf.WF_HR_REJECTED,
                    username,
                    remarks,
                    approved=False,
                )
                ltc_wf.sync_file_extra_workflow(file_obj, ltc_wf.WF_HR_REJECTED)
                archive_form_file(file_id=str(file_id))
            return Response({"detail": "Rejected.", "workflow_status": form.workflow_status})

        return Response({"detail": "Unknown or missing action."}, status=status.HTTP_400_BAD_REQUEST)


class AppraisalWorkflowHandle(Hr2AuthenticatedAPIView):
    """HR Admin approves or rejects appraisal; file is archived after decision."""

    def post(self, request, file_id):
        action = (request.data.get("action") or "").strip()
        designation = request.data.get("designation") or _get_request_designation(request)
        remarks = (request.data.get("remarks") or "").strip()

        perm_err = _ensure_current_owner_with_designation(
            request,
            file_id=file_id,
            receiver_payload=request.data,
        )
        if perm_err:
            return perm_err

        try:
            file_obj = File.objects.get(pk=file_id)
        except File.DoesNotExist:
            return Response({"detail": "File not found."}, status=status.HTTP_404_NOT_FOUND)

        extra = file_obj.file_extra_JSON or {}
        if extra.get("type") != FormType.APPRAISAL:
            return Response({"detail": "Not an Appraisal file."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            form = get_form_for_type_and_id(FormType.APPRAISAL, int(file_obj.src_object_id))
        except Exception:
            return Response({"detail": "Form not found."}, status=status.HTTP_404_NOT_FOUND)

        if form.workflow_status in appraisal_wf.TERMINAL_STATUSES:
            return Response(
                {"detail": "This application is already closed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username = request.user.username

        if action == "hr_admin_approve":
            if not ltc_wf.designation_is_hr_admin(designation):
                return Response(
                    {"detail": "Only HR Admin can approve at this stage."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if form.workflow_status != appraisal_wf.WF_SUBMITTED:
                return Response(
                    {"detail": "Application is not awaiting HR approval."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            with transaction.atomic():
                appraisal_wf.append_workflow_event(
                    form,
                    appraisal_wf.WF_HR_APPROVED,
                    username,
                    remarks or "Approved by HR",
                    approved=True,
                    approved_by=request.user,
                    approvedDate=datetime.date.today(),
                )
                appraisal_wf.sync_file_extra_workflow(file_obj, appraisal_wf.WF_HR_APPROVED)
                archive_form_file(file_id=str(file_id))
            refreshed = get_form_for_type_and_id(FormType.APPRAISAL, form.id)
            return Response(
                {
                    "detail": "Approved.",
                    "workflow_status": refreshed.workflow_status,
                    "form": Appraisal_serializer(refreshed).data,
                }
            )

        if action == "hr_admin_reject":
            if not ltc_wf.designation_is_hr_admin(designation):
                return Response(
                    {"detail": "Only HR Admin can reject at this stage."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if form.workflow_status != appraisal_wf.WF_SUBMITTED:
                return Response(
                    {"detail": "Application is not awaiting HR approval."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not remarks:
                return Response(
                    {"detail": "Remarks are required when rejecting."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            with transaction.atomic():
                appraisal_wf.append_workflow_event(
                    form,
                    appraisal_wf.WF_HR_REJECTED,
                    username,
                    remarks,
                    approved=False,
                )
                appraisal_wf.sync_file_extra_workflow(file_obj, appraisal_wf.WF_HR_REJECTED)
                archive_form_file(file_id=str(file_id))
            return Response({"detail": "Rejected.", "workflow_status": form.workflow_status})

        return Response({"detail": "Unknown or missing action."}, status=status.HTTP_400_BAD_REQUEST)


class CPDAReimbursement(Hr2APIView):
    """API view for CPDA Reimbursement form operations."""
    serializer_class = CPDAReimbursement_serializer

    def post(self, request):
        user_info = request.data[1]
        serializer = self.serializer_class(data=request.data[0])
        if serializer.is_valid():
            instance = serializer.save()
            try:
                create_form_file(
                    uploader=request.user.username,
                    uploader_designation=user_info["uploader_designation"],
                    receiver=user_info["receiver_name"],
                    receiver_designation=user_info["receiver_designation"],
                    src_object_id=str(instance.id),
                    form_type=FormType.CPDA_REIMBURSEMENT,
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).error("File tracking failed for CPDA Reimbursement: %s", e)
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
        if isinstance(request.data, list):
            form_data = request.data[0] if len(request.data) > 0 else {}
            user_info = request.data[1] if len(request.data) > 1 else {}
        else:
            form_data = request.data.get("form_data", request.data)
            user_info = request.data.get("user_info", {})
        data, err = _submit_appraisal_application(request, form_data, user_info)
        if err:
            return err
        return Response(data, status=status.HTTP_200_OK)

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


class LeaveFormPdfDownload(Hr2AuthenticatedAPIView):
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


class LeaveFormInitials(Hr2AuthenticatedAPIView):
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


class CheckLeaveBalance(Hr2AuthenticatedAPIView):
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


class GetMyDetails(Hr2AuthenticatedAPIView):
    """API view to get current user's details (username and designation)."""

    def get(self, request, *args, **kwargs):
        user = request.user
        designations = []
        seen = set()
        for hd in (
            HoldsDesignation.objects.filter(working=user)
            .select_related("designation")
            .order_by("designation__name")
        ):
            if not hd.designation_id:
                continue
            n = (hd.designation.name or "").strip()
            if n and n not in seen:
                seen.add(n)
                designations.append(n)
        designation = designations[0] if designations else None

        return Response(
            {
                "username": user.username,
                "designation": designation or "N/A",
                "designations": designations,
            },
            status=status.HTTP_200_OK
        )


class SearchEmployee(Hr2AuthenticatedAPIView):
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
    "cpda_claim": FormType.CPDA_REIMBURSEMENT,
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

class FormTypeRequests(Hr2AuthenticatedAPIView):
    """Outbox (submitted forms) filtered by form type."""

    def get(self, request, form_type_slug):
        form_type = _URL_SLUG_TO_FORM_TYPE.get(form_type_slug)
        if not form_type:
            return Response({"detail": "Unknown form type."}, status=status.HTTP_400_BAD_REQUEST)

        if not HoldsDesignation.objects.filter(working=request.user).exists():
            return Response({f"{form_type_slug}_requests": []}, status=status.HTTP_200_OK)

        try:
            outbox = get_outbox_for_all_held_designations(
                username=request.user.username
            )
        except Exception:
            outbox = []

        filtered = _filter_files_by_form_type(outbox, form_type)
        return Response({f"{form_type_slug}_requests": filtered}, status=status.HTTP_200_OK)


class FormTypeInbox(Hr2AuthenticatedAPIView):
    """Inbox filtered by form type."""

    def get(self, request, form_type_slug):
        form_type = _URL_SLUG_TO_FORM_TYPE.get(form_type_slug)
        if not form_type:
            return Response({"detail": "Unknown form type."}, status=status.HTTP_400_BAD_REQUEST)

        if not HoldsDesignation.objects.filter(working=request.user).exists():
            return Response({f"{form_type_slug}_inbox": []}, status=status.HTTP_200_OK)

        try:
            inbox = get_inbox_for_all_held_designations(
                username=request.user.username
            )
        except Exception:
            inbox = []

        filtered = _filter_files_by_form_type(inbox, form_type)
        return Response({f"{form_type_slug}_inbox": filtered}, status=status.HTTP_200_OK)


class FormTypeArchive(Hr2AuthenticatedAPIView):
    """Archive filtered by form type."""

    def get(self, request, form_type_slug):
        form_type = _URL_SLUG_TO_FORM_TYPE.get(form_type_slug)
        if not form_type:
            return Response({"detail": "Unknown form type."}, status=status.HTTP_400_BAD_REQUEST)

        if not HoldsDesignation.objects.filter(working=request.user).exists():
            return Response({f"{form_type_slug}_archive": []}, status=status.HTTP_200_OK)

        try:
            archived = get_archived_for_all_held_designations(
                username=request.user.username
            )
        except Exception:
            archived = []

        filtered = _filter_files_by_form_type(archived, form_type)
        return Response({f"{form_type_slug}_archive": filtered}, status=status.HTTP_200_OK)


class FormTypeTrack(Hr2AuthenticatedAPIView):
    """File tracking history for a given file id."""

    def get(self, request, form_type_slug, file_id):
        history = get_file_history(file_id=str(file_id))
        payload = {"file_history": history}
        if form_type_slug == "cpda_adv":
            try:
                f_obj = File.objects.get(pk=file_id)
                if (f_obj.file_extra_JSON or {}).get("type") == FormType.CPDA_ADVANCE:
                    cpda_form = CPDAAdvanceform.objects.filter(
                        pk=int(f_obj.src_object_id)
                    ).first()
                    if cpda_form:
                        payload["workflow_status"] = cpda_form.workflow_status
                        payload["workflow_history"] = cpda_form.workflow_history or []
            except (File.DoesNotExist, ValueError, TypeError):
                pass
        elif form_type_slug == "ltc":
            try:
                f_obj = File.objects.get(pk=file_id)
                if (f_obj.file_extra_JSON or {}).get("type") == FormType.LTC:
                    ltc_row = LTCform.objects.filter(pk=int(f_obj.src_object_id)).first()
                    if ltc_row:
                        payload["workflow_status"] = ltc_row.workflow_status
                        payload["workflow_history"] = ltc_row.workflow_history or []
            except (File.DoesNotExist, ValueError, TypeError):
                pass
        elif form_type_slug == "appraisal":
            try:
                f_obj = File.objects.get(pk=file_id)
                if (f_obj.file_extra_JSON or {}).get("type") == FormType.APPRAISAL:
                    row = Appraisalform.objects.filter(pk=int(f_obj.src_object_id)).first()
                    if row:
                        payload["workflow_status"] = row.workflow_status
                        payload["workflow_history"] = row.workflow_history or []
            except (File.DoesNotExist, ValueError, TypeError):
                pass
        return Response(payload)


class FormTypeFormDetail(Hr2AuthenticatedAPIView):
    """Fetch a single form's data by form type slug and file id."""

    def get(self, request, form_type_slug, form_id):
        form_type = _URL_SLUG_TO_FORM_TYPE.get(form_type_slug)
        if not form_type:
            return Response({"detail": "Unknown form type."}, status=status.HTTP_400_BAD_REQUEST)

        serializer_cls = _FORM_TYPE_TO_SERIALIZER.get(form_type)
        if not serializer_cls:
            return Response({"detail": "Unknown form type."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            file_obj = File.objects.get(pk=form_id)
            real_form_id = int(file_obj.src_object_id)
        except (File.DoesNotExist, ValueError, TypeError):
            return Response({"detail": "File not found or invalid format."}, status=status.HTTP_404_NOT_FOUND)

        try:
            form = get_form_for_type_and_id(form_type, real_form_id)
        except Exception:
            return Response({"detail": "Form not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = serializer_cls(form, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================================
# CPDA Claim specific views (nested under cpda/claim/)
# ============================================================================

class CpdaClaimRequests(Hr2AuthenticatedAPIView):
    """Outbox filtered for CPDA Reimbursement (claim)."""

    def get(self, request):
        if not HoldsDesignation.objects.filter(working=request.user).exists():
            return Response({"cpda_claim_requests": []}, status=status.HTTP_200_OK)

        try:
            outbox = get_outbox_for_all_held_designations(
                username=request.user.username
            )
        except Exception:
            outbox = []

        filtered = _filter_files_by_form_type(outbox, FormType.CPDA_REIMBURSEMENT)
        return Response({"cpda_claim_requests": filtered}, status=status.HTTP_200_OK)


class CpdaClaimInbox(Hr2AuthenticatedAPIView):
    """Inbox filtered for CPDA Reimbursement (claim)."""

    def get(self, request):
        if not HoldsDesignation.objects.filter(working=request.user).exists():
            return Response({"cpda_claim_inbox": []}, status=status.HTTP_200_OK)

        try:
            inbox = get_inbox_for_all_held_designations(
                username=request.user.username
            )
        except Exception:
            inbox = []

        filtered = _filter_files_by_form_type(inbox, FormType.CPDA_REIMBURSEMENT)
        return Response({"cpda_claim_inbox": filtered}, status=status.HTTP_200_OK)


class CpdaClaimArchive(Hr2AuthenticatedAPIView):
    """Archive filtered for CPDA Reimbursement (claim)."""

    def get(self, request):
        if not HoldsDesignation.objects.filter(working=request.user).exists():
            return Response({"cpda_claim_archive": []}, status=status.HTTP_200_OK)

        try:
            archived = get_archived_for_all_held_designations(
                username=request.user.username
            )
        except Exception:
            archived = []

        filtered = _filter_files_by_form_type(archived, FormType.CPDA_REIMBURSEMENT)
        return Response({"cpda_claim_archive": filtered}, status=status.HTTP_200_OK)


class CpdaClaimTrack(Hr2AuthenticatedAPIView):
    """File tracking for CPDA Claim."""

    def get(self, request, file_id):
        history = get_file_history(file_id=str(file_id))
        return Response({"file_history": history}, status=status.HTTP_200_OK)


class CpdaClaimSubmit(Hr2AuthenticatedAPIView):
    """Submit a CPDA Reimbursement (claim) form."""
    serializer_class = CPDAReimbursement_serializer

    def post(self, request):
        if isinstance(request.data, list):
            form_data = request.data[0] if len(request.data) > 0 else {}
            user_info = request.data[1] if len(request.data) > 1 else {}
        else:
            form_data = request.data.get("form_data", request.data)
            user_info = request.data.get("user_info", {})
        serializer = self.serializer_class(data=form_data)
        if serializer.is_valid():
            instance = serializer.save()
            try:
                create_form_file(
                    uploader=user_info.get("uploader_name", request.user.username),
                    uploader_designation=user_info.get("uploader_designation", _get_user_primary_designation(request.user) or ""),
                    receiver=user_info.get("receiver_name", ""),
                    receiver_designation=user_info.get("receiver_designation", ""),
                    src_object_id=str(instance.id),
                    form_type=FormType.CPDA_REIMBURSEMENT,
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).error("File tracking failed for CPDA Claim: %s", e)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# Appraisal submit view
# ============================================================================

class AppraisalSubmit(Hr2AuthenticatedAPIView):
    """Submit an Appraisal form."""
    serializer_class = Appraisal_serializer

    def post(self, request):
        if isinstance(request.data, list):
            form_data = request.data[0] if len(request.data) > 0 else {}
            user_info = request.data[1] if len(request.data) > 1 else {}
        else:
            form_data = request.data.get("form_data", request.data)
            user_info = request.data.get("user_info", {})
        data, err = _submit_appraisal_application(request, form_data, user_info)
        if err:
            return err
        return Response(data, status=status.HTTP_200_OK)


# ============================================================================
# Leave-specific views
# ============================================================================

class LeaveSubmit(Hr2AuthenticatedAPIView):
    """Submit a leave form (POST)."""
    serializer_class = Leave_serializer

    def post(self, request):
        if isinstance(request.data, list):
            form_data = request.data[0] if len(request.data) > 0 else {}
            user_info = request.data[1] if len(request.data) > 1 else {}
        else:
            form_data = request.data.get("form_data", request.data)
            user_info = request.data.get("user_info", {})
        serializer = self.serializer_class(data=form_data)
        if serializer.is_valid():
            instance = serializer.save()
            try:
                create_form_file(
                    uploader=user_info.get("uploader_name", request.user.username),
                    uploader_designation=user_info.get("uploader_designation", _get_user_primary_designation(request.user) or ""),
                    receiver=user_info.get("receiver_name", ""),
                    receiver_designation=user_info.get("receiver_designation", ""),
                    src_object_id=str(instance.id),
                    form_type=FormType.LEAVE,
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).error("File tracking failed for Leave: %s", e)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeaveFileHandle(Hr2AuthenticatedAPIView):
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

class SearchEmployeesView(Hr2AuthenticatedAPIView):
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


class FormTrackGeneric(Hr2AuthenticatedAPIView):
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


class LtcCreate(Hr2AuthenticatedAPIView):
    """Create an LTC form (POST) — authenticated users; same pipeline as ``LTC.post``."""
    serializer_class = LTC_serializer

    def post(self, request):
        is_complete, message = _is_profile_complete_for_ltc(request.user)
        if not is_complete:
            return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(request.data, list):
            form_data = request.data[0] if len(request.data) > 0 else {}
            user_info = request.data[1] if len(request.data) > 1 else {}
        else:
            form_data = request.data.get("form_data", request.data)
            user_info = request.data.get("user_info", {})
        data, err = _submit_ltc_application(request, form_data, user_info)
        if err:
            return err
        return Response(data, status=status.HTTP_200_OK)


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

