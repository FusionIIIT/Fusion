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
from dateutil.relativedelta import relativedelta
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from applications.hr2.workflow import leave_wf
from applications.hr2.api.permissions import ModuleAccessHRPermission
from applications.hr2.constants.form_types import FormType
from applications.hr2.constants.leave_balance_map import LEAVE_TYPE_TO_ALLOTTED_USED
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
from applications.leave.models import LeaveType
from applications.globals.models import ExtraInfo
from applications.hr2.models import (
    CPDAAdvanceform,
    LeaveBalance,
    EmpConfidentialDetails,
    LeaveForm,
    LTCform,
    Appraisalform,
    Employee,
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
    """Decrement HR2 ``LeaveBalance`` used counters by computed working days (ceil)."""
    import math

    leave_type_key = (form.natureOfLeave or "").strip().lower()
    fields = LEAVE_TYPE_TO_ALLOTTED_USED.get(leave_type_key)
    if not fields:
        return False, "Unsupported leave type for balance update."

    days = getattr(form, "applied_leave_days", None)
    if days is None:
        deduct_units = 1
    else:
        deduct_units = max(1, int(math.ceil(float(days))))

    allotted_f, used_f = fields
    applicant = getattr(form, "created_by", None)
    if not applicant:
        return False, "Leave application has no creator."
    extra = ExtraInfo.objects.filter(user=applicant).first()
    if not extra:
        return False, "Employee profile not found for applicant."
    leave_balance = LeaveBalance.objects.filter(employeeId=extra).first()
    if not leave_balance:
        return False, "Leave balance record not found for employee."

    allotted = int(getattr(leave_balance, allotted_f, 0) or 0)
    used = int(getattr(leave_balance, used_f, 0) or 0)
    if allotted - used < deduct_units:
        return False, "Insufficient leave balance to approve this leave."

    setattr(leave_balance, used_f, used + deduct_units)
    leave_balance.save()
    return True, ""


def _decrement_legacy_leaves_count_on_approval(form):
    """Update ``applications.leave.LeavesCount`` using the same day count as the leave module."""
    from applications.leave.models import LeavesCount

    applicant = form.created_by
    if not applicant:
        return
    lt = getattr(form, "leave_type", None)
    if lt is None:
        return
    if not form.leaveStartDate or not form.leaveEndDate:
        return
    days = form.applied_leave_days
    if days is None:
        return
    year = form.leaveStartDate.year
    try:
        lc = LeavesCount.objects.get(user=applicant, leave_type=lt, year=year)
    except LeavesCount.DoesNotExist:
        return
    if float(lc.remaining_leaves) < float(days):
        return
    lc.remaining_leaves = float(lc.remaining_leaves) - float(days)
    lc.save(update_fields=["remaining_leaves"])


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
    four_years_ago = datetime.date.today() - relativedelta(years=4)

    # 1. Check self-declared previous LTC date in the current form
    declared_date_str = form_data.get("certifiedThatAdvanceTakenOn")
    if declared_date_str:
        from dateutil import parser
        try:
            declared_date = parser.parse(str(declared_date_str)).date()
            if declared_date > four_years_ago:
                return None, Response(
                    {"detail": f"LTC claims are only allowed once every 4 years. You declared your last advance was taken on {declared_date.strftime('%Y-%m-%d')}."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception:
            pass

    # 2. Check previous LTC forms in the database
    last_ltc = LTCform.objects.filter(
        created_by=request.user
    ).exclude(
        workflow_status="hr_rejected"
    ).order_by('-id').first()
    
    if last_ltc:
        last_date = last_ltc.submissionDate or last_ltc.leaveStartDate or last_ltc.dateOfDepartureForFamily or getattr(last_ltc, "approvedDate", None)
        if not last_date:
            last_date = datetime.date.today()
        if last_date > four_years_ago:
            return None, Response(
                {"detail": f"LTC claims are only allowed once every 4 years. Your last claim was on {last_date.strftime('%Y-%m-%d')}."},
                status=status.HTTP_400_BAD_REQUEST
            )

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

    employee = Employee.objects.filter(extra_info__user=request.user).first()
    if not employee or not employee.date_of_joining:
        return None, Response(
            {"detail": "Your date of joining is missing in the system. Cannot submit appraisal."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    one_year_ago = datetime.date.today() - relativedelta(years=1)
    if employee.date_of_joining > one_year_ago:
        return None, Response(
            {"detail": "You must have completed a minimum of 1 year of service to submit an appraisal."},
            status=status.HTTP_400_BAD_REQUEST,
        )

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
                cpda_wf.archive_tracked_file_if_workflow_closed(
                    file_id, form.workflow_status
                )
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
                cpda_wf.archive_tracked_file_if_workflow_closed(
                    file_id, form.workflow_status
                )
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
                cpda_wf.archive_tracked_file_if_workflow_closed(
                    file_id, form.workflow_status
                )
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
        form_data = request.data[0]
        if hasattr(form_data, "dict"):
            form_data = form_data.dict()
        elif not isinstance(form_data, dict):
            form_data = dict(form_data)
        else:
            form_data = dict(form_data)
        _, bind_err = _apply_submitter_leave_identifiers(form_data, request.user)
        if bind_err is not None:
            return bind_err
        serializer = self.serializer_class(
            data=form_data, context={"request": request}
        )
        if serializer.is_valid():
            instance = serializer.save(created_by=request.user)
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


class LeaveTypesForHr(Hr2AuthenticatedAPIView):
    """Expose ``applications.leave.LeaveType`` options for the HR leave form (reuse leave module)."""

    def get(self, request):
        extra = ExtraInfo.objects.filter(user=request.user).first()
        user_type = (getattr(extra, "user_type", None) or "faculty").strip().lower()
        qs = LeaveType.objects.all().order_by("name")
        if user_type == "faculty":
            qs = qs.filter(for_faculty=True)
        elif user_type == "staff":
            qs = qs.filter(for_staff=True)
        rows = [
            {
                "id": lt.id,
                "name": lt.name,
                "requires_proof": lt.requires_proof,
                "requires_address": lt.requires_address,
                "authority_forwardable": lt.authority_forwardable,
                "max_in_year": lt.max_in_year,
            }
            for lt in qs
        ]
        return Response({"leave_types": rows}, status=status.HTTP_200_OK)


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
        elif form_type_slug == "leave":
            try:
                f_obj = File.objects.get(pk=file_id)
                if (f_obj.file_extra_JSON or {}).get("type") == FormType.LEAVE:
                    row = LeaveForm.objects.filter(pk=int(f_obj.src_object_id)).first()
                    if row:
                        payload["workflow_status"] = row.workflow_status
                        payload["workflow_history"] = row.workflow_history or []
            except (File.DoesNotExist, ValueError, TypeError):
                pass
        return Response(payload)


def _leave_tracking_file_for_form(form_pk: int):
    """Return the newest filetracking row for an HR LeaveForm, if any."""
    for f in File.objects.filter(src_object_id=str(int(form_pk))).order_by("-id"):
        if (f.file_extra_JSON or {}).get("type") == FormType.LEAVE:
            return f
    return None


class FormTypeFormDetail(Hr2AuthenticatedAPIView):
    """Fetch a single form's data by form type slug and file or (for leave) form primary key."""

    def get(self, request, form_type_slug, form_id):
        form_type = _URL_SLUG_TO_FORM_TYPE.get(form_type_slug)
        if not form_type:
            return Response({"detail": "Unknown form type."}, status=status.HTTP_400_BAD_REQUEST)

        serializer_cls = _FORM_TYPE_TO_SERIALIZER.get(form_type)
        if not serializer_cls:
            return Response({"detail": "Unknown form type."}, status=status.HTTP_400_BAD_REQUEST)

        file_obj = None
        real_form_id = None
        try:
            file_obj = File.objects.get(pk=form_id)
            real_form_id = int(file_obj.src_object_id)
        except (File.DoesNotExist, ValueError, TypeError):
            if form_type_slug == "leave":
                try:
                    real_form_id = int(form_id)
                    LeaveForm.objects.get(pk=real_form_id)
                    file_obj = _leave_tracking_file_for_form(real_form_id)
                except (LeaveForm.DoesNotExist, ValueError, TypeError):
                    return Response(
                        {"detail": "File not found or invalid format."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            else:
                return Response(
                    {"detail": "File not found or invalid format."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        try:
            form = get_form_for_type_and_id(form_type, real_form_id)
        except Exception:
            return Response({"detail": "Form not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = serializer_cls(form, many=False)
        data = serializer.data
        if form_type_slug == "leave":
            data = {**data, "file_id": str(file_obj.pk) if file_obj else None}
        return Response(data, status=status.HTTP_200_OK)


class LeaveEmployeeRequests(Hr2AuthenticatedAPIView):
    """List leave applications for the current user (workflow status + dates)."""

    serializer_class = Leave_serializer

    def get(self, request):
        lookup = (request.query_params.get("name") or "").strip()
        if lookup and lookup != request.user.username:
            return Response(
                {"detail": "You may only list your own leave requests."},
                status=status.HTTP_403_FORBIDDEN,
            )
        from_date = request.query_params.get("from_date")
        qs = LeaveForm.objects.filter(created_by=request.user).order_by("-submissionDate", "-id")
        if from_date:
            try:
                d0 = datetime.datetime.strptime(from_date.strip(), "%Y-%m-%d").date()
                qs = qs.filter(submissionDate__gte=d0)
            except ValueError:
                pass
        serialized = self.serializer_class(qs, many=True).data
        rows = []
        for row in serialized:
            d = dict(row)
            try:
                fid = _leave_tracking_file_for_form(int(d["id"]))
                d["file_id"] = str(fid.pk) if fid else None
            except (TypeError, ValueError):
                d["file_id"] = None
            rows.append(d)
        return Response(rows, status=status.HTTP_200_OK)


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

def _apply_submitter_leave_identifiers(form_data, user):
    """Bind ``employeeId`` / ``pfNo`` to integer values the serializer accepts.

    ``LeaveForm`` stores these as ``IntegerField``s, but ``ExtraInfo.id`` is a
    ``CharField`` primary key (often non-numeric). Assigning ``extra.id`` makes
    DRF raise "A valid integer is required." We therefore store the submitter's
    numeric ``User.pk`` on the form; ``LeaveBalance`` is resolved via
    ``ExtraInfo`` + ``created_by`` instead of this integer.
    """
    extra = ExtraInfo.objects.filter(user=user).first()
    if not extra:
        return (
            None,
            Response(
                {
                    "detail": (
                        "Employee profile not found for your account. "
                        "Ask an administrator to link your login to ExtraInfo."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            ),
        )
    try:
        uid = int(user.pk)
    except (TypeError, ValueError):
        return (
            None,
            Response(
                {"detail": "Could not determine a numeric user id for this account."},
                status=status.HTTP_400_BAD_REQUEST,
            ),
        )
    for k in ("employeeId", "pfNo"):
        form_data.pop(k, None)
    form_data["employeeId"] = uid
    form_data["pfNo"] = uid
    return extra, None


def _leave_submit_payload_from_request(request, user_info):
    """Normalize multipart/JSON payloads into Leave_serializer input.

    Accepts legacy frontend keys (purpose, department, pfno) and maps them to
    model fields.     Reuses leave-module leave-type naming for balance deduction
    (see ``applications.hr2.constants.leave_balance_map``).
    """
    def _as_bool(v):
        if v in (None, "", False):
            return False
        if isinstance(v, bool):
            return v
        return str(v).strip().lower() in ("1", "true", "yes", "on")

    if isinstance(request.data, list):
        raw = request.data[0] if len(request.data) > 0 else {}
        user_info = user_info or (request.data[1] if len(request.data) > 1 else {})
    elif hasattr(request.data, "get"):
        raw = request.data.get("form_data", request.data)
    else:
        raw = request.data

    if hasattr(raw, "dict"):
        raw = raw.dict()
    elif not isinstance(raw, dict):
        raw = dict(raw)

    def pick(*keys):
        for k in keys:
            v = raw.get(k)
            if v in (None, ""):
                continue
            if isinstance(v, str) and not v.strip():
                continue
            return v
        return None

    def _int_or_none(val):
        if val in (None, ""):
            return None
        try:
            return int(str(val).strip())
        except (TypeError, ValueError):
            return None

    extra = ExtraInfo.objects.filter(user=request.user).first()
    employee_id = _int_or_none(pick("employeeId", "employee_id"))
    if employee_id is None and getattr(request, "user", None) and request.user.is_authenticated:
        try:
            employee_id = int(request.user.pk)
        except (TypeError, ValueError):
            employee_id = None

    pf_no = _int_or_none(pick("pfNo", "pf_no", "pfno"))
    if pf_no is None and getattr(request, "user", None) and request.user.is_authenticated:
        try:
            pf_no = int(request.user.pk)
        except (TypeError, ValueError):
            pf_no = None

    department = pick("departmentInfo", "department_info", "department")
    lt_raw = pick("leave_type", "leaveType", "leave_type_id")
    leave_type_val = None
    if lt_raw not in (None, ""):
        try:
            leave_type_val = int(lt_raw)
        except (TypeError, ValueError):
            leave_type_val = None

    nature = pick("natureOfLeave", "nature_of_leave")
    if not nature and leave_type_val is not None:
        # Resolve the leave type ID to its name from the Leave module
        try:
            lt_obj = LeaveType.objects.get(pk=leave_type_val)
            nature = lt_obj.name
        except LeaveType.DoesNotExist:
            nature = "casual"
    if not nature and leave_type_val is None:
        nature = "casual"
    purpose = pick("purposeOfLeave", "purpose_of_leave", "purpose")

    acad = (pick("academicResponsibility", "academic_responsibility") or "").strip()
    admin_resp = (
        pick(
            "addministrativeResponsibiltyAssigned",
            "administrativeResponsibility",
            "administrative_responsibility",
        )
        or ""
    ).strip()

    payload = {
        "name": pick("name"),
        "designation": pick("designation"),
        "submissionDate": pick("submissionDate", "submission_date"),
        "departmentInfo": department,
        "natureOfLeave": nature if nature not in (None, "") else "casual",
        "leaveStartDate": pick("leaveStartDate", "leave_start_date"),
        "leaveEndDate": pick("leaveEndDate", "leave_end_date"),
        "purposeOfLeave": purpose,
        "addressDuringLeave": (pick("addressDuringLeave", "address_during_leave") or "").strip(),
        "start_half": _as_bool(pick("start_half", "startHalf")),
        "end_half": _as_bool(pick("end_half", "endHalf")),
        "leave_info": (pick("leave_info", "leaveInfo") or "").strip(),
    }
    if employee_id is not None:
        payload["employeeId"] = employee_id
    if pf_no is not None:
        payload["pfNo"] = pf_no
    if acad:
        payload["academicResponsibility"] = acad
    if admin_resp:
        payload["addministrativeResponsibiltyAssigned"] = admin_resp
    if leave_type_val is not None:
        payload["leave_type"] = leave_type_val

    def _keep_field(key, val):
        if key in ("start_half", "end_half"):
            return True
        return val is not None

    return {k: v for k, v in payload.items() if _keep_field(k, v)}, user_info or {}


class LeaveSubmit(Hr2AuthenticatedAPIView):
    """Submit a leave form (POST)."""
    serializer_class = Leave_serializer

    def post(self, request):
        if isinstance(request.data, list):
            user_info = request.data[1] if len(request.data) > 1 else {}
        else:
            user_info = request.data.get("user_info", {}) or {}

        form_data, user_info = _leave_submit_payload_from_request(request, user_info)
        extra, bind_err = _apply_submitter_leave_identifiers(form_data, request.user)
        if bind_err is not None:
            return bind_err

        serializer = self.serializer_class(
            data=form_data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        hod_username, hod_designation = leave_wf.resolve_hod_for_applicant(request.user)
        if not hod_username:
            hod_username = (user_info.get("receiver_name") or "").strip()
            hod_designation = (user_info.get("receiver_designation") or "").strip()
        if not hod_username or not hod_designation:
            return Response(
                {
                    "detail": (
                        "No HOD is configured for your department. "
                        "Ask an administrator to assign an HOD, or pass receiver_name and "
                        "receiver_designation in user_info."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        uploader_desig = (
            (user_info.get("uploader_designation") or "").strip()
            or _get_user_primary_designation(request.user)
            or ""
        )
        if not uploader_desig:
            return Response(
                {"detail": "Your designation could not be determined. Cannot submit."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                instance = serializer.save(created_by=request.user)
                leave_wf.append_workflow_event(
                    instance,
                    leave_wf.WF_SUBMITTED,
                    request.user.username,
                    "Form submitted",
                )
                create_form_file(
                    uploader=user_info.get("uploader_name", request.user.username),
                    uploader_designation=uploader_desig,
                    receiver=hod_username,
                    receiver_designation=hod_designation,
                    src_object_id=str(instance.id),
                    form_type=FormType.LEAVE,
                    file_extra_JSON={
                        "type": FormType.LEAVE,
                        "workflow_status": leave_wf.WF_SUBMITTED,
                        "leaveStartDate": str(instance.leaveStartDate)
                        if instance.leaveStartDate
                        else "",
                        "leaveEndDate": str(instance.leaveEndDate)
                        if instance.leaveEndDate
                        else "",
                    },
                )
        except Exception as e:
            logging.getLogger(__name__).error("Leave submit failed: %s", e)
            return Response(
                {"detail": f"Leave submission failed: {e!s}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        refreshed = LeaveForm.objects.get(pk=instance.pk)
        return Response(self.serializer_class(refreshed).data, status=status.HTTP_200_OK)


class LeaveFileHandle(Hr2AuthenticatedAPIView):
    """Handle a leave file action (hod_approve, hod_reject, hr_approve, hr_reject)."""
    serializer_class = Leave_serializer

    def post(self, request, file_id):
        # Verify the requesting user is the current file owner
        try:
            current_owner = get_current_file_owner(file_id)
            current_owner_designation = get_current_file_owner_designation(file_id)
        except Exception:
            return Response(
                {"detail": "Unable to verify current owner for this file."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if current_owner != request.user:
            return Response(
                {"detail": "Only the current owner can perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )

        action = request.data.get("action")
        remarks = (request.data.get("remarks") or "").strip()

        try:
            file_obj = File.objects.get(pk=file_id)
            form = LeaveForm.objects.get(pk=int(file_obj.src_object_id))
        except (File.DoesNotExist, LeaveForm.DoesNotExist, ValueError):
            return Response({"detail": "File or Form not found."}, status=status.HTTP_404_NOT_FOUND)

        if form.workflow_status in leave_wf.TERMINAL_STATUSES:
            return Response({"detail": "Workflow is already closed."}, status=status.HTTP_400_BAD_REQUEST)

        # Auto-resolve role from file tracking designation
        current_role = (
            current_owner_designation.name
            if current_owner_designation
            else (_get_user_primary_designation(request.user) or "")
        )

        if action == "accept":
            if form.workflow_status == leave_wf.WF_SUBMITTED:
                action = "hod_approve"
            elif form.workflow_status == leave_wf.WF_HOD_APPROVED:
                action = "hr_approve"
        elif action == "reject":
            if form.workflow_status == leave_wf.WF_SUBMITTED:
                action = "hod_reject"
            elif form.workflow_status == leave_wf.WF_HOD_APPROVED:
                action = "hr_reject"

        if action == "hod_approve":
            if not leave_wf.designation_is_hod(current_role):
                return Response({"detail": "Only HOD can approve at this step."}, status=status.HTTP_403_FORBIDDEN)
            if not leave_wf.hod_covers_applicant(current_role, form.created_by):
                return Response(
                    {"detail": "You are not the HOD for this applicant's department."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            hr_admin_user, hr_admin_desig = leave_wf.resolve_hr_admin()
            if not hr_admin_user:
                return Response(
                    {"detail": "HR Admin is not configured (no user holds the HR Admin designation)."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            with transaction.atomic():
                leave_wf.append_workflow_event(
                    form, leave_wf.WF_HOD_APPROVED, request.user.username, remarks or "Approved by HOD"
                )
                forward_form_file(
                    file_id=str(file_id),
                    receiver=hr_admin_user,
                    receiver_designation=hr_admin_desig,
                    remarks=remarks or "Approved by HOD — forwarded to HR Admin",
                    file_extra_JSON={"type": FormType.LEAVE, "workflow_status": leave_wf.WF_HOD_APPROVED},
                )
                file_obj.refresh_from_db()
                leave_wf.sync_file_extra_workflow(file_obj, leave_wf.WF_HOD_APPROVED)
            return Response(
                {
                    "detail": "Approved by HOD. Forwarded to HR Admin.",
                    "workflow_status": form.workflow_status,
                },
                status=status.HTTP_200_OK,
            )

        if action == "hod_reject":
            if not leave_wf.designation_is_hod(current_role):
                return Response({"detail": "Only HOD can reject at this step."}, status=status.HTTP_403_FORBIDDEN)
            if not leave_wf.hod_covers_applicant(current_role, form.created_by):
                return Response(
                    {"detail": "You are not the HOD for this applicant's department."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if not remarks:
                return Response(
                    {"detail": "Remarks are required when rejecting."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            with transaction.atomic():
                leave_wf.append_workflow_event(
                    form,
                    leave_wf.WF_HOD_REJECTED,
                    request.user.username,
                    remarks,
                    approved=False,
                )
                leave_wf.sync_file_extra_workflow(file_obj, leave_wf.WF_HOD_REJECTED)
                leave_wf.archive_tracked_file_if_workflow_closed(file_id, leave_wf.WF_HOD_REJECTED)
            return Response(
                {"detail": "Rejected by HOD. Workflow closed.", "workflow_status": form.workflow_status},
                status=status.HTTP_200_OK,
            )

        if action == "hr_approve":
            if not leave_wf.designation_is_hr_admin(current_role):
                return Response({"detail": "Only HR Admin can approve at this step."}, status=status.HTTP_403_FORBIDDEN)
            with transaction.atomic():
                success, message = _decrement_leave_balance_on_approval(form)
                if not success:
                    transaction.set_rollback(True)
                    return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)
                _decrement_legacy_leaves_count_on_approval(form)
                leave_wf.append_workflow_event(
                    form,
                    leave_wf.WF_HR_APPROVED,
                    request.user.username,
                    remarks or "Approved by HR Admin",
                    approved=True,
                    approved_by=request.user,
                    approvedDate=datetime.date.today(),
                )
                leave_wf.sync_file_extra_workflow(file_obj, leave_wf.WF_HR_APPROVED)
                leave_wf.archive_tracked_file_if_workflow_closed(file_id, leave_wf.WF_HR_APPROVED)
            return Response(
                {"detail": "Approved by HR Admin. Workflow closed.", "workflow_status": form.workflow_status},
                status=status.HTTP_200_OK,
            )

        if action == "hr_reject":
            if not leave_wf.designation_is_hr_admin(current_role):
                return Response({"detail": "Only HR Admin can reject at this step."}, status=status.HTTP_403_FORBIDDEN)
            if not remarks:
                return Response(
                    {"detail": "Remarks are required when rejecting."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            with transaction.atomic():
                leave_wf.append_workflow_event(
                    form,
                    leave_wf.WF_HR_REJECTED,
                    request.user.username,
                    remarks,
                    approved=False,
                )
                leave_wf.sync_file_extra_workflow(file_obj, leave_wf.WF_HR_REJECTED)
                leave_wf.archive_tracked_file_if_workflow_closed(file_id, leave_wf.WF_HR_REJECTED)
            return Response(
                {"detail": "Rejected by HR Admin. Workflow closed.", "workflow_status": form.workflow_status},
                status=status.HTTP_200_OK,
            )

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


class EmployeeDetail(Hr2AuthenticatedAPIView):
    """Get employee info by Django ``User`` primary key.

    Uses ``Hr2AuthenticatedAPIView`` so HOD/inbox handlers can resolve usernames without
    requiring HR module access (see ``ModuleAccessHRPermission`` on ``Hr2APIView``).
    """

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

