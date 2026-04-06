"""Consolidated API views for HR2 module.

This module contains all REST API view classes for HR2 form operations,
including LTC, CPDA, Leave, Appraisal forms and management/workflow views.
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.contrib.auth import get_user_model

from applications.hr2.constants.form_types import FormType
from applications.hr2.api.serializers import (
    Appraisal_serializer,
    CPDAAdvance_serializer,
    CPDAReimbursement_serializer,
    Leave_serializer,
    LeaveBalanace_serializer,
    LTC_serializer,
)
from applications.hr2.models import ExtraInfo, LeaveBalance
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


User = get_user_model()

_FORM_TYPE_TO_SERIALIZER = {
    FormType.LTC: LTC_serializer,
    FormType.CPDA_ADVANCE: CPDAAdvance_serializer,
    FormType.CPDA_REIMBURSEMENT: CPDAReimbursement_serializer,
    FormType.LEAVE: Leave_serializer,
    FormType.APPRAISAL: Appraisal_serializer,
}


# ============================================================================
# Form CRUD Views
# ============================================================================

class LTC(APIView):
    """API view for LTC (Long Term Advance) form operations."""
    serializer_class = LTC_serializer
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
        form = get_form_for_type_and_id(FormType.LTC, form_id)
        serializer = self.serializer_class(form, data=request.data[1])
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
        form = get_form_for_type_and_id(FormType.CPDA_ADVANCE, form_id)
        serializer = self.serializer_class(form, data=request.data[1])
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
        form = get_form_for_type_and_id(FormType.CPDA_REIMBURSEMENT, form_id)
        serializer = self.serializer_class(form, data=request.data[1])
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
        form = get_form_for_type_and_id(FormType.LEAVE, form_id)
        serializer = self.serializer_class(form, data=request.data[1])
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
        form = get_form_for_type_and_id(FormType.APPRAISAL, form_id)
        serializer = self.serializer_class(form, data=request.data[1])
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
