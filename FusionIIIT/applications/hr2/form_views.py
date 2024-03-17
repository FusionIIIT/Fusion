from .serializers import LTC_serializer, CPDAAdvance_serializer, Appraisal_serializer, CPDAReimbursement_serializer, Leave_serializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import LTCform, CPDAAdvanceform, CPDAReimbursementform, Leaveform, Appraisalform
from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned
from applications.filetracking.sdk.methods import *
from applications.globals.models import Designation, HoldsDesignation


class LTC(APIView):
    serializer_class = LTC_serializer
    permission_classes = (AllowAny, )

    def post(self, request):
        user_info = request.data[0]
        serializer = self.serializer_class(data=request.data[1])
        if serializer.is_valid():
            serializer.save()
            file_id = create_file(uploader=user_info['uploader_name'], uploader_designation=user_info['uploader_designation'], receiver="21BCS140",
                                  receiver_designation="hradmin", src_module="HR", src_object_id=str(serializer.data['id']), file_extra_JSON={"type": "LTC"}, attached_file=None)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        pk = request.query_params.get("name")
        print(pk)
        try:
            forms = LTCform.objects.get(name=pk)
            serializer = self.serializer_class(forms, many=False)
        except MultipleObjectsReturned:
            forms = LTCform.objects.filter(name=pk)
            serializer = self.serializer_class(forms, many=True)
        except LTCform.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        pk = request.query_params.get("id")
        print(pk)
        form = LTCform.objects.get(id=pk)
        print(form)
        serializer = self.serializer_class(form, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FormManagement(APIView):
    permission_classes = (AllowAny, )

    def get(self, request, *args, **kwargs):
        username = request.query_params.get("username")
        designation = request.query_params.get("designation")
        inbox = view_inbox(username=username,
                           designation=designation, src_module="HR")
        return Response(inbox, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        username = request.data['receiver']
        receiver_value = User.objects.get(username=username)
        receiver_value_designation = HoldsDesignation.objects.filter(
            user=receiver_value)
        lis = list(receiver_value_designation)
        obj = lis[0].designation
        forward_file(file_id=request.data['file_id'], receiver=request.data['receiver'], receiver_designation=obj.name,
                     remarks=request.data['remarks'], file_extra_JSON=request.data['file_extra_JSON'])
        return Response(status=status.HTTP_200_OK)


class CPDAAdvance(APIView):
    serializer_class = CPDAAdvance_serializer
    permission_classes = (AllowAny, )

    def post(self, request):
        print(request.data[1])
        user_info = request.data[1]
        serializer = self.serializer_class(data=request.data[0])
        if serializer.is_valid():
            serializer.save()
            file_id = create_file(uploader=user_info['uploader_name'], uploader_designation=user_info['uploader_designation'], receiver="21BCS077",
                                  receiver_designation="student", src_module="HR", src_object_id=str(serializer.data['id']), file_extra_JSON={"type": "CPDAAdvance"}, attached_file=None)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        pk = request.query_params.get("id")
        print(pk)
        try:
            forms = CPDAAdvanceform.objects.get(id=pk)
            serializer = self.serializer_class(forms, many=False)
        except MultipleObjectsReturned:
            forms = CPDAAdvanceform.objects.filter(id=pk)
            serializer = self.serializer_class(forms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        pk = request.query_params.get("id")
        print(pk)
        form = CPDAAdvanceform.objects.get(id=pk)
        print(form)
        serializer = self.serializer_class(form, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CPDAReimbursement(APIView):
    serializer_class = CPDAReimbursement_serializer
    permission_classes = (AllowAny, )

    def post(self, request):
        user_info = request.data[0]
        serializer = self.serializer_class(data=request.data[1])
        if serializer.is_valid():
            serializer.save()
            file_id = create_file(uploader=user_info['uploader_name'], uploader_designation=user_info['uploader_designation'], receiver="vkjain",
                                  receiver_designation="CSE HOD", src_module="HR", src_object_id=str(serializer.data['id']), file_extra_JSON={"type": "CPDAReimbursement"}, attached_file=None)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        pk = request.query_params.get("name")
        print(pk)
        try:
            forms = CPDAReimbursementform.objects.get(name=pk)
            serializer = self.serializer_class(forms, many=False)
        except MultipleObjectsReturned:
            forms = CPDAReimbursementform.objects.filter(name=pk)
            serializer = self.serializer_class(forms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        pk = request.query_params.get("id")
        print(pk)
        form = CPDAReimbursementform.objects.get(id=pk)
        print(form)
        serializer = self.serializer_class(form, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Leave(APIView):
    serializer_class = Leave_serializer
    permission_classes = (AllowAny, )

    def post(self, request):
        user_info = request.data[0]
        serializer = self.serializer_class(data=request.data[1])
        if serializer.is_valid():
            serializer.save()
            file_id = create_file(uploader=user_info['uploader_name'], uploader_designation=user_info['uploader_designation'], receiver="vkjain",
                                  receiver_designation="CSE HOD", src_module="HR", src_object_id=str(serializer.data['id']), file_extra_JSON={"type": "Leave"}, attached_file=None)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        pk = request.query_params.get("name")
        print(pk)
        try:
            forms = Leaveform.objects.get(name=pk)
            serializer = self.serializer_class(forms, many=False)
        except MultipleObjectsReturned:
            forms = Leaveform.objects.filter(name=pk)
            serializer = self.serializer_class(forms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        pk = request.query_params.get("id")
        print(pk)
        form = Leaveform.objects.get(id=pk)
        print(form)
        serializer = self.serializer_class(form, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Appraisal(APIView):
    serializer_class = Appraisal_serializer
    permission_classes = (AllowAny, )

    def post(self, request):
        user_info = request.data[0]
        serializer = self.serializer_class(data=request.data[1])
        if serializer.is_valid():
            serializer.save()
            file_id = create_file(uploader=user_info['uploader_name'], uploader_designation=user_info['uploader_designation'], receiver="vkjain",
                                  receiver_designation="CSE HOD", src_module="HR", src_object_id=str(serializer.data['id']), file_extra_JSON={"type": "Appraisal"}, attached_file=None)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        pk = request.query_params.get("name")
        print(pk)
        try:
            forms = Appraisalform.objects.get(name=pk)
            serializer = self.serializer_class(forms, many=False)
        except MultipleObjectsReturned:
            forms = Appraisalform.objects.filter(name=pk)
            serializer = self.serializer_class(forms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        pk = request.query_params.get("id")
        print(pk)
        form = Appraisalform.objects.get(id=pk)
        print(form)
        serializer = self.serializer_class(form, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssignerReviewer(APIView):
    def post(self, request, *args, **kwargs):
        forward_file(file_id=request.data['file_id'], receiver="21BCS140", receiver_designation='hradmin',
                     remarks=request.data['remarks'], file_extra_JSON=request.data['file_extra_JSON'])
        return Response(status=status.HTTP_200_OK)
