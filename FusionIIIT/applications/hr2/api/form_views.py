from .serializers import LTC_serializer, CPDAAdvance_serializer, Appraisal_serializer, CPDAReimbursement_serializer, Leave_serializer, LeaveBalanace_serializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
# from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated
from applications.hr2.models import LTCform, CPDAAdvanceform, CPDAReimbursementform, LeaveForm, Appraisalform, LeaveBalance
from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned
from applications.filetracking.sdk.methods import *
from applications.globals.models import Designation, HoldsDesignation, ExtraInfo
from applications.filetracking.models import *
# from django.contrib.auth.models import User


class LTC(APIView):
    serializer_class = LTC_serializer
    permission_classes = (IsAuthenticated, )

    def post(self, request):
        print("hello")
        user_info = request.data[1]
        print(request.data[1])
        serializer = self.serializer_class(data=request.data[0])
        if serializer.is_valid():
            serializer.save()
            fileId = create_file(uploader=user_info['uploader_name'], uploader_designation=user_info['uploader_designation'], receiver=user_info['receiver_name'],
                                 receiver_designation=user_info['receiver_designation'], src_module="HR", src_object_id=str(serializer.data['id']), file_extra_JSON={"type": "LTC"}, attached_file=None)
            # forwarded = forward_file(file_id=fileId, receiver=user_info['receiver_name'], receiver_designation=user_info['receiver_designation'],
            #  remarks="Forwarded to Receiver Inbox", file_extra_JSON={"type": "LTC"})
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        pk = request.query_params.get("name")
        try:
            forms = LTCform.objects.get(created_by=pk)
            serializer = self.serializer_class(forms, many=False)
        except MultipleObjectsReturned:
            forms = LTCform.objects.filter(created_by=pk)
            serializer = self.serializer_class(forms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        pk = request.query_params.get("id")
        receiver = request.data[0]
        # send_to = receiver['receiver']
        # receiver_value = User.objects.get(username=send_to)
        # receiver_value_designation = HoldsDesignation.objects.filter(
        #     user=receiver_value)
        # lis = list(receiver_value_designation)
        # obj = lis[0].designation
        form = LTCform.objects.get(id=pk)
        serializer = self.serializer_class(form, data=request.data[1])
        if serializer.is_valid():
            serializer.save()
            forward_file(file_id=receiver['file_id'], receiver=receiver['receiver'], receiver_designation=receiver['receiver_designation'],
                         remarks=receiver['remarks'], file_extra_JSON=receiver['file_extra_JSON'])
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        id = request.query_params.get("id")
        is_archived = archive_file(file_id=id)
        if (is_archived):
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class FormManagement(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        username = request.query_params.get("username")
        designation = request.query_params.get("designation")
        inbox = view_inbox(username=username,
                           designation=designation, src_module="HR")
        print(inbox)
        return Response(inbox, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        username = request.data['receiver']
        receiver_value = User.objects.get(username=username)
        receiver_value_designation = HoldsDesignation.objects.filter(
            user=receiver_value)
        lis = list(receiver_value_designation)
        obj = lis[0].designation
        forward_file(file_id=request.data['file_id'], receiver=request.data['receiver'], receiver_designation=request.data['receiver_designation'],
                     remarks=request.data['remarks'], file_extra_JSON=request.data['file_extra_JSON'])
        return Response(status=status.HTTP_200_OK)


class CPDAAdvance(APIView):
    serializer_class = CPDAAdvance_serializer
    permission_classes = (IsAuthenticated, )

    def post(self, request):
        print(request.data[0])
        user_info = request.data[1]
        # receiver_value = User.objects.get(username=user_info['receiver_name'])
        # receiver_value_designation = HoldsDesignation.objects.filter(
        #     user=receiver_value)
        # lis = list(receiver_value_designation)
        # obj = lis[0].designation
        serializer = self.serializer_class(data=request.data[0])
        if serializer.is_valid():
            serializer.save()
            print('1')
            fileId = create_file(uploader=user_info['uploader_name'], uploader_designation=user_info['uploader_designation'], receiver=user_info['receiver_name'],
                                 receiver_designation=user_info['receiver_designation'], src_module="HR", src_object_id=str(serializer.data['id']), file_extra_JSON={"type": "CPDAAdvance"}, attached_file=None)
            # forwarded = forward_file(file_id=fileId, receiver=user_info['receiver_name'], receiver_designation=user_info['receiver_designation'],
            #  remarks="Forwarded to Receiver Inbox", file_extra_JSON={"type": "CPDAAdvance"})
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        pk = request.query_params.get("name")
        try:
            forms = CPDAAdvanceform.objects.get(created_by=pk)
            serializer = self.serializer_class(forms, many=False)
        except MultipleObjectsReturned:
            forms = CPDAAdvanceform.objects.filter(created_by=pk)
            serializer = self.serializer_class(forms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        pk = request.query_params.get("id")
        receiver = request.data[0]
        print(request.data)
        send_to = receiver['receiver']
        print(send_to)
        receiver_value = User.objects.get(username=send_to)
        receiver_value_designation = HoldsDesignation.objects.filter(
            user=receiver_value)
        lis = list(receiver_value_designation)
        obj = lis[0].designation
        form = CPDAAdvanceform.objects.get(id=pk)
        serializer = self.serializer_class(form, data=request.data[1])
        if serializer.is_valid():
            serializer.save()
            forward_file(file_id=receiver['file_id'], receiver=receiver['receiver'], receiver_designation=receiver['receiver_designation'],
                         remarks=receiver['remarks'], file_extra_JSON=receiver['file_extra_JSON'])
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        id = request.query_params.get("id")
        is_archived = archive_file(file_id=id)
        if (is_archived):
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class CPDAReimbursement(APIView):
    serializer_class = CPDAReimbursement_serializer
    permission_classes = (IsAuthenticated, )

    def post(self, request):
        user_info = request.data[1]
        serializer = self.serializer_class(data=request.data[0])
        if serializer.is_valid():
            serializer.save()
            fileId = create_file(uploader=user_info['uploader_name'], uploader_designation=user_info['uploader_designation'], receiver=user_info['receiver_name'],
                                 receiver_designation=user_info['receiver_designation'], src_module="HR", src_object_id=str(serializer.data['id']), file_extra_JSON={"type": "CPDAReimbursement"}, attached_file=None)
            # forwarded = forward_file(file_id=fileId, receiver=user_info['receiver_name'], receiver_designation=user_info['receiver_designation'],
            #  remarks="Forwarded to Receiver Inbox", file_extra_JSON={"type": "CPDAReimbursement"})
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        pk = request.query_params.get("name")
        try:
            forms = CPDAReimbursementform.objects.get(created_by=pk)
            serializer = self.serializer_class(forms, many=False)
        except MultipleObjectsReturned:
            forms = CPDAReimbursementform.objects.filter(created_by=pk)
            serializer = self.serializer_class(forms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        pk = request.query_params.get("id")
        print(request.data)
        receiver = request.data[0]
        # send_to = receiver['receiver']
        # receiver_value = User.objects.get(username=send_to)
        # receiver_value_designation = HoldsDesignation.objects.filter(
        #     user=receiver_value)
        # lis = list(receiver_value_designation)
        # obj = lis[0].designation
        form = CPDAReimbursementform.objects.get(id=pk)
        serializer = self.serializer_class(form, data=request.data[1])
        if serializer.is_valid():
            serializer.save()
            forward_file(file_id=receiver['file_id'], receiver=receiver['receiver'], receiver_designation=receiver['receiver_designation'],
                         remarks=receiver['remarks'], file_extra_JSON=receiver['file_extra_JSON'])
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        id = request.query_params.get("id")
        is_archived = archive_file(file_id=id)
        if (is_archived):
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class Leave(APIView):
    serializer_class = Leave_serializer
    permission_classes = (IsAuthenticated, )

    def post(self, request):
        user_info = request.data[1]
        serializer = self.serializer_class(data=request.data[0])
        if serializer.is_valid():
            serializer.save()
            fileId = create_file(uploader=user_info['uploader_name'], uploader_designation=user_info['uploader_designation'], receiver=user_info['receiver_name'],
                                 receiver_designation=user_info['receiver_designation'], src_module="HR", src_object_id=str(serializer.data['id']), file_extra_JSON={"type": "Leave"}, attached_file=None)
            # forwarded = forward_file(file_id=fileId, receiver=user_info['receiver_name'], receiver_designation=user_info['receiver_designation'],
            #  remarks="Forwarded to Receiver Inbox", file_extra_JSON={"type": "Leave"})
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        pk = request.query_params.get("name")
        try:
            forms = LeaveForm.objects.get(created_by=pk)
            serializer = self.serializer_class(forms, many=False)
        except MultipleObjectsReturned:
            forms = LeaveForm.objects.filter(created_by=pk)
            serializer = self.serializer_class(forms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        pk = request.query_params.get("id")
        receiver = request.data[0]
        # send_to = receiver['receiver']
        # receiver_value = User.objects.get(username=send_to)
        # receiver_value_designation = HoldsDesignation.objects.filter(
        #     user=receiver_value)
        # lis = list(receiver_value_designation)
        # obj = lis[0].designation
        form = LeaveForm.objects.get(id=pk)
        serializer = self.serializer_class(form, data=request.data[1])
        if serializer.is_valid():
            serializer.save()
            forward_file(file_id=receiver['file_id'], receiver=receiver['receiver'], receiver_designation=receiver['receiver_designation'],
                         remarks=receiver['remarks'], file_extra_JSON=receiver['file_extra_JSON'])
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        id = request.query_params.get("id")
        is_archived = archive_file(file_id=id)
        if (is_archived):
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class Appraisal(APIView):
    serializer_class = Appraisal_serializer
    permission_classes = (IsAuthenticated, )

    def post(self, request):
        user_info = request.data[1]
        print(request.data)
        serializer = self.serializer_class(data=request.data[0])
        if serializer.is_valid():
            serializer.save()
            fileId = create_file(uploader=user_info['uploader_name'], uploader_designation=user_info['uploader_designation'], receiver=user_info['receiver_name'],
                                 receiver_designation=user_info['receiver_designation'], src_module="HR", src_object_id=str(serializer.data['id']), file_extra_JSON={"type": "Appraisal"}, attached_file=None)
            # forwarded = forward_file(file_id=fileId, receiver=user_info['receiver_name'], receiver_designation=user_info['receiver_designation'],
            #  remarks="Forwarded to Receiver Inbox", file_extra_JSON={"type": "Appraisal"})
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        pk = request.query_params.get("name")
        try:
            forms = Appraisalform.objects.get(created_by=pk)
            serializer = self.serializer_class(forms, many=False)
        except MultipleObjectsReturned:
            forms = Appraisalform.objects.filter(created_by=pk)
            serializer = self.serializer_class(forms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        pk = request.query_params.get("id")
        print(request.data)
        form = Appraisalform.objects.get(id=pk)
        receiver = request.data[0]
        send_to = receiver['receiver_name']
        receiver_value = User.objects.get(username=send_to)
        receiver_value_designation = HoldsDesignation.objects.filter(
            user=receiver_value)
        lis = list(receiver_value_designation)
        obj = lis[0].designation
        serializer = self.serializer_class(form, data=request.data[1])
        if serializer.is_valid():
            forward_file(file_id=receiver['file_id'], receiver=send_to, receiver_designation=receiver['receiver_designation'],
                         remarks=receiver['remarks'], file_extra_JSON=receiver['file_extra_JSON'])
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        id = request.query_params.get("id")
        is_archived = archive_file(file_id=id)
        if (is_archived):
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

# class Forward(APIView):
#     def post(self, request, *args, **kwargs):
#         forward_file(file_id = request.data['file_id'], receiver = request.data['receiver'], receiver_designation = 'hradmin', remarks = request.data['remarks'], file_extra_JSON = request.data['file_extra_JSON'])
#         return Response(status = status.HTTP_200_OK)


class GetFormHistory(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        print(request.query_params)
        form_type = request.query_params.get("type")
        id = request.query_params.get("id")
        person = User.objects.get(username=id)
        print(type(person))
        id = person
        if form_type == "LTC":
            try:
                forms = LTCform.objects.get(created_by=id)
                serializer = LTC_serializer(forms, many=False)
                return Response([serializer.data], status=status.HTTP_200_OK)
            except MultipleObjectsReturned:
                forms = LTCform.objects.filter(created_by=id)
                serializer = LTC_serializer(forms, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except LTCform.DoesNotExist:
                return Response([], status=status.HTTP_200_OK)
        elif form_type == "CPDAReimbursement":
            try:
                forms = CPDAReimbursementform.objects.get(created_by=id)
                serializer = CPDAReimbursement_serializer(forms, many=False)
                return Response([serializer.data], status=status.HTTP_200_OK)
            except MultipleObjectsReturned:
                forms = CPDAReimbursementform.objects.filter(created_by=id)
                serializer = CPDAReimbursement_serializer(forms, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except CPDAReimbursementform.DoesNotExist:
                return Response([], status=status.HTTP_200_OK)
        elif form_type == "CPDAAdvance":
            try:
                forms = CPDAAdvanceform.objects.get(created_by=id)
                serializer = CPDAAdvance_serializer(forms, many=False)
                return Response([serializer.data], status=status.HTTP_200_OK)
            except MultipleObjectsReturned:
                forms = CPDAAdvanceform.objects.filter(created_by=id)
                serializer = CPDAAdvance_serializer(forms, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except CPDAAdvanceform.DoesNotExist:
                return Response([], status=status.HTTP_200_OK)
        elif form_type == "Appraisal":
            try:
                forms = Appraisalform.objects.get(created_by=id)
                serializer = Appraisal_serializer(forms, many=False)
                return Response([serializer.data], status=status.HTTP_200_OK)
            except MultipleObjectsReturned:
                forms = Appraisalform.objects.filter(created_by=id)
                serializer = Appraisal_serializer(forms, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Appraisalform.DoesNotExist:
                return Response([], status=status.HTTP_200_OK)
        elif form_type == "Leave":
            try:
                forms = LeaveForm.objects.get(created_by=id)
                serializer = Leave_serializer(forms, many=False)
                return Response([serializer.data], status=status.HTTP_200_OK)
            except MultipleObjectsReturned:
                forms = LeaveForm.objects.filter(created_by=id)
                serializer = Leave_serializer(forms, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except LeaveForm.DoesNotExist:
                return Response([], status=status.HTTP_200_OK)


class TrackProgress(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        file_id = request.query_params.get("id")
        progress = view_history(file_id)
        return Response({"status": progress}, status=status.HTTP_200_OK)


class FormFetch(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        fileId = request.query_params.get("file_id")
        print(fileId)
        form_id = request.query_params.get("id")
        form_type = request.query_params.get("type")
        if form_type == "LTC":
            forms = LTCform.objects.get(id=form_id)
            serializer = LTC_serializer(forms, many=False)
            form = serializer.data
            user = User.objects.get(id=int(form["created_by"]))
            owner = Tracking.objects.filter(file_id=fileId)
            current_owner = owner.last()
            current_owner = current_owner.receiver_id
            current_owner = current_owner.username
        elif form_type == "CPDAReimbursement":
            forms = CPDAReimbursementform.objects.get(id=form_id)
            serializer = CPDAReimbursement_serializer(forms, many=False)
            form = serializer.data
            user = User.objects.get(id=int(form["created_by"]))
            owner = Tracking.objects.filter(file_id=fileId)
            current_owner = owner.last()
            current_owner = current_owner.receiver_id
            current_owner = current_owner.username
        elif form_type == "CPDAAdvance":
            forms = CPDAAdvanceform.objects.get(id=form_id)
            serializer = CPDAAdvance_serializer(forms, many=False)
            form = serializer.data
            user = User.objects.get(id=int(form["created_by"]))
            owner = Tracking.objects.filter(file_id=fileId)
            current_owner = owner.last()
            current_owner = current_owner.receiver_id
            current_owner = current_owner.username
        elif form_type == "Appraisal":
            forms = Appraisalform.objects.get(id=form_id)
            serializer = Appraisal_serializer(forms, many=False)
            form = serializer.data
            user = User.objects.get(id=int(form["created_by"]))
            owner = Tracking.objects.filter(file_id=fileId)
            current_owner = owner.last()
            current_owner = current_owner.receiver_id
            current_owner = current_owner.username
        elif form_type == "Leave":
            forms = LeaveForm.objects.get(id=form_id)
            serializer = Leave_serializer(forms, many=False)
            form = serializer.data
            user = User.objects.get(id=int(form["created_by"]))
            owner = Tracking.objects.filter(file_id=fileId)
            current_owner = owner.last()
            current_owner = current_owner.receiver_id
            current_owner = current_owner.username
        return Response({"form": serializer.data, "creator": user.username, "current_owner": current_owner}, status=status.HTTP_200_OK)


class CheckLeaveBalance(APIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = LeaveBalanace_serializer

    def get(self, request, *args, **kwargs):
        name = request.query_params.get("name")
        person = User.objects.get(username=name)
        extrainfo = ExtraInfo.objects.get(user=person)
        leave_balance = LeaveBalance.objects.get(employeeId=extrainfo)
        serializer = self.serializer_class(leave_balance, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)
        # return Response([], status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        name = request.query_params.get("name")
        # print(request.data)
        person = User.objects.get(username=name)
        extrainfo = ExtraInfo.objects.get(user=person)
        leave_balance = LeaveBalance.objects.get(employeeId=extrainfo)
        data1 = request.data
        data1['employeeId'] = extrainfo.id
        serializer = self.serializer_class(leave_balance, data=data1)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print(serializer.error_messages)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DropDown(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get("username")
        user = User.objects.get(username=user_id)
        designations = HoldsDesignation.objects.filter(user=user.id)
        designation_list = []

        for design in designations:
            design = design.designation
            design = design.name
            designation_list.append(design)
        # print(designation_list)
        return Response(designation_list, status=status.HTTP_200_OK)


class UserById(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get("id")
        user = User.objects.get(id=user_id)
        return Response({"username": user.username}, status=status.HTTP_200_OK)


class ViewArchived(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        user_name = request.query_params.get("username")
        user_designation = request.query_params.get("designation")
        archived_inbox = view_archived(
            username=user_name, designation=user_designation, src_module="HR")
        return Response(archived_inbox, status=status.HTTP_200_OK)


class GetOutbox(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        name = request.query_params.get("username")
        user_designation = request.query_params.get("designation")
        outbox = view_outbox(
            username=name, designation=user_designation, src_module="HR")
        return Response(outbox, status=status.HTTP_200_OK)
