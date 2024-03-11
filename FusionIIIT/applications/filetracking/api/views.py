from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication
from ..sdk.methods import create_file, view_file, delete_file, view_inbox, view_outbox, view_history, forward_file, get_designations


class CreateFileView(APIView):
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        file_id = create_file(**request.data)
        return Response({'file_id': file_id}, status=status.HTTP_201_CREATED)


class ViewFileView(APIView):
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [permissions.IsAuthenticated]

    def get(self, request, file_id, *args, **kwargs):
        file_details = view_file(int(file_id))
        return Response(file_details)


class DeleteFileView(APIView):
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, file_id, *args, **kwargs):
        success = delete_file(int(file_id))
        if success:
            return Response({'message': 'File deleted successfully'},
                            status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'error': 'File not found'},
                            status=status.HTTP_404_NOT_FOUND)


class ViewInboxView(APIView):
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        inbox_files = view_inbox(
            request.user.username,
            request.query_params.get('designation'),
            request.query_params.get('src_module'))
        return Response(inbox_files)


class ViewOutboxView(APIView):
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        outbox_files = view_outbox(
            request.user.username,
            request.query_params.get('designation'),
            request.query_params.get('src_module'))
        return Response(outbox_files)


class ViewHistoryView(APIView):
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [permissions.IsAuthenticated]

    def get(self, request, file_id, *args, **kwargs):
        history = view_history(int(file_id))
        return Response(history)


class ForwardFileView(APIView):
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [permissions.IsAuthenticated]

    def post(self, request, file_id, *args, **kwargs):
        new_tracking_id = forward_file(int(file_id), **request.data)
        return Response({'tracking_id': new_tracking_id},
                        status=status.HTTP_201_CREATED)


class GetDesignationsView(APIView):
    #authentication_classes = [TokenAuthentication]
    #permission_classes = [permissions.IsAuthenticated]

    def get(self, request, username, *args, **kwargs):
        user_designations = get_designations(username)
        return Response({'designations': user_designations})
