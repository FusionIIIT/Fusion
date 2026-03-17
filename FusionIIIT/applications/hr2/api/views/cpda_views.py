from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from applications.hr2.constants.form_types import FormType
from applications.hr2.api.serializers import (
    CPDAAdvance_serializer,
    CPDAReimbursement_serializer,
)
from applications.hr2.services.file_workflow import (
    create_form_file,
    forward_form_file,
    archive_form_file,
)
from applications.hr2.services.form_services import (
    get_forms_for_user,
    get_form_for_type_and_id,
)


class CPDAAdvance(APIView):
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
