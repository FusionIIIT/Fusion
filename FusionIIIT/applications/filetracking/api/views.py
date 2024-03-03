from venv import logger
from django.forms import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication
from ..models import File
from ..sdk.methods import create_file, view_file, delete_file, view_inbox, view_outbox, view_history, forward_file, get_designations

class CreateFileView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            current_user = request.user.username
            current_designation = request.data.get('designation')
            receiver_username = request.data.get('receiver_username')
            receiver_designation = request.data.get('receiver_designation')
            subject = request.data.get('subject')
            description = request.data.get('description')

            if None in [current_designation, receiver_username, receiver_designation, subject, description]:
                return Response({'error': 'One or more required fields are missing.'}, status=status.HTTP_400_BAD_REQUEST)

            file_id = create_file(uploader=current_user, uploader_designation=current_designation,
                                  receiver=receiver_username, receiver_designation=receiver_designation, subject=subject, description=description)

            return Response({'file_id': file_id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ViewFileView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, file_id):
        try:
            file_details = view_file(int(file_id))
            # print(file_details)
            return Response(file_details, status=status.HTTP_200_OK)
        except ValueError:
            return Response({'error': 'Invalid file ID format.'}, status=status.HTTP_400_BAD_REQUEST)
        except File.DoesNotExist:
            return Response({'error': 'File not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, file_id):
        try:
            # file_details = view_file(int(file_id))
            # print(file_details)
            success = delete_file(int(file_id))
            if success:
                return Response({'message': 'File deleted successfully'},
                                status=status.HTTP_204_NO_CONTENT)
            else :
                return

        except ValueError:
            return Response({'error': 'Invalid file ID format'},
                            status=status.HTTP_400_BAD_REQUEST)
        except File.DoesNotExist:
            return Response({'error': 'File not found'},
                            status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)  # Handle ValidationError specifically
        except Exception as e:  # Catch unexpected errors
            logger.error(f"Unexpected error in DeleteFileView: {e}")
            return Response({'error': 'An internal server error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
