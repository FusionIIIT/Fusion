import logging, zipfile, io
from venv import logger
from django.core import serializers
from django.core.files.base import ContentFile
from django.forms import ValidationError
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication
from ..models import File, Tracking
from applications.globals.models import Designation
from ..sdk.methods import create_draft, create_file, view_drafts, view_file, delete_file, view_inbox, view_outbox, view_history, forward_file, get_designations, archive_file, view_archived, unarchive_file
from notification.views import file_tracking_notif
from applications.filetracking.api.serializers import FileSerializer

class CreateFileView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            current_user = request.user
            current_designation = request.data.get('designation')
            receiver_username = request.data.get('receiver_username')
            receiver_designation = request.data.get('receiver_designation')
            subject = request.data.get('subject')
            description = request.data.get('description')
            src_module = request.data.get('src_module')
            attached_files = request.FILES.getlist('files')
            remarks = request.data.get('remarks')
            # Check for missing required fields
            if None in [current_designation, receiver_username, receiver_designation, subject, description, src_module]:
                return Response({'error': 'One or more required fields are missing.'}, status=status.HTTP_400_BAD_REQUEST)

            zip_file = None
            if attached_files:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_archive:
                    for file in attached_files:
                        zip_archive.writestr(file.name, file.read())
                zip_buffer.seek(0)
                zip_filename=f"attachments_{subject}.zip"
                zip_file = ContentFile(zip_buffer.getvalue(), name=zip_filename)

            file_id = create_file(
                uploader=current_user,
                uploader_designation=current_designation,
                receiver=receiver_username,
                receiver_designation=receiver_designation,
                subject=subject,
                description=description,
                src_module=src_module,
                attached_file=zip_file,
                remarks=remarks,
            )


            receiver = User.objects.get(username=receiver_username)
            file_tracking_notif(current_user, receiver, "File Received from " + str(current_user))  # Call the notification function here

            return Response({'file_id': file_id}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ViewFileView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, file_id):
        try:
            file_details = view_file(int(file_id))
            return Response(file_details, status=status.HTTP_200_OK)
        except ValueError:
            return Response({'error': 'Invalid file ID format.'}, status=status.HTTP_400_BAD_REQUEST)
        except File.DoesNotExist:
            return Response({'error': 'File not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, file_id):
        try:
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
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        API endpoint to view inbox files.

        Expects query parameters:
            - username (required): User requesting the inbox.
            - designation (optional): Designation to filter files by.
            - src_module (required): Source module to filter files by.

        Returns:
            JSON response containing a list of serialized file data, including sender information.
        """
        username = request.query_params.get('username')
        designation = request.query_params.get('designation')
        src_module = request.query_params.get('src_module')


        # if not username or not src_module:
        #     return Response({'error': 'Missing required query parameters: username and src_module.'}, status=400)
        inbox_files = view_inbox(username, designation, src_module)
        return Response(inbox_files)

class ViewOutboxView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]


    def get(self, request):
        """
        API endpoint to view outbox files.

        Expects query parameters:
            - username (required): User requesting the outbox.
            - designation (optional): Designation to filter files by.
            - src_module (required): Source module to filter files by.

        Returns:
            JSON response containing a paginated list of serialized file data.
        """

        username = request.query_params.get('username')
        designation = request.query_params.get('designation')
        src_module = request.query_params.get('src_module')


        if not username or not src_module:
            return Response({'error': 'Missing required query parameters: username and src_module.'}, status=400)

        outbox_files = view_outbox(username, designation, src_module)
        return Response(outbox_files)


class ViewHistoryView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, file_id):
        """
        View history of a particular file with the given file_id.

        Args:
            request (rest_framework.request.Request): The incoming request object.
            file_id (int): Primary key of the file to retrieve history for.

        Returns:
            rest_framework.response.Response: JSON response containing serialized tracking history.
        """
        try:
           tracking_array = []
           histories = view_history(file_id)
           requested_file = File.objects.get(id=file_id)
           serializer = FileSerializer(requested_file)
           file_details = serializer.data
           prev_designation = file_details['designation']
           for history in reversed(histories): #iterating from the first user to the latest user.
               temp_obj_action = history.copy()
               temp_obj_action['receiver_id'] = User.objects.get(id=history['receiver_id']).username
               temp_obj_action['receive_design'] = Designation.objects.get(id=history['receive_design']).name
               temp_obj_action['sender_designation'] = Designation.objects.get(id=prev_designation).name
               prev_designation = int(history['receive_design'])
               tracking_array.append(temp_obj_action)
           return Response(tracking_array)
        except Tracking.DoesNotExist:
           return Response({'error': f'File with ID {file_id} not found.'}, status=404)
        except Exception as e:
           print("error: ", e)
           logger.error(f"An unexpected error occurred: {e}")
           return Response({'error': 'Internal server error.'}, status=500)
        
class ForwardFileView(APIView):
# #     # Authentication and permission classes (adjust based on your needs)
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, file_id):
#         # Extract data from request.data
        receiver = request.data.get('receiver')
        receiver_designation = request.data.get('receiver_designation')
        file_extra_JSON = request.data.get('file_extra_JSON', {})
        remarks = request.data.get('remarks', "")
        # Validate data
        if not receiver or not receiver_designation:
            raise ValidationError("Missing required fields: receiver and receiver_designation")
        attached_files = request.FILES.getlist('files')
        zip_file = None
        if attached_files:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_archive:
                for file in attached_files:
                    zip_archive.writestr(file.name, file.read())
            zip_buffer.seek(0)
            zip_filename=f"attachments_{receiver}.zip"
            zip_file = ContentFile(zip_buffer.getvalue(), name=zip_filename)
        try:
            new_tracking_id = forward_file(
                int(file_id),
                receiver,
                receiver_designation,
                file_extra_JSON,
                remarks,
                file_attachment = zip_file
            )
            receiver_user = User.objects.get(username=receiver)
            file_tracking_notif(request.user, receiver_user, "File Forwarded from " + str(request.user))
            logging.info(f"Successfully forwarded file {file_id} with tracking ID: {new_tracking_id}")
        except Exception as e:
            logging.error(f"Error forwarding file {file_id}: {str(e)}")
            raise ValidationError(str(e))  # Re-raise exception with a user-friendly message
        # Return response
        return Response({'tracking_ids': new_tracking_id}, status=status.HTTP_201_CREATED)
class CreateDraftFile(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        uploader = request.user
        uploader_designation = request.data.get("designation", "")
        src_module = request.data.get("src_module", "")
        src_object_id = request.data.get("src_object_id", "")
        file_extra_JSON = request.data.get("file_extra_JSON", {})
        uploaded_files = request.FILES.getlist("files", [])  # Retrieve multiple files
        subject = request.data.get("subject", "")  # Optional field
        description = request.data.get("description", "")  # Optional field
        remarks = request.data.get("remarks", "")  # Optional field
        if None in [uploader_designation, src_module]:
            return Response({'error': 'One or more required fields are missing.'}, status=status.HTTP_400_BAD_REQUEST)
        # Add optional fields to file_extra_JSON
        if subject:
            file_extra_JSON["subject"] = subject
        if description:
            file_extra_JSON["description"] = description
        if remarks:
            file_extra_JSON["remarks"] = remarks

        draft_file_ids = []
        try:
            for file in uploaded_files:
                # Debugging log for each file
                print(file.name)
                file_id = create_draft(
                    uploader=uploader,
                    uploader_designation=uploader_designation,
                    src_module=src_module,
                    src_object_id=src_object_id,
                    file_extra_JSON=file_extra_JSON,
                    attached_file=file
                )
                draft_file_ids.append(file_id)  # Collect created draft file IDs
            return Response({'file_ids': draft_file_ids}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class DraftFileView(APIView):
   authentication_classes = [TokenAuthentication]
   permission_classes = [permissions.IsAuthenticated]

   def get(self, request):
       username = request.query_params.get('username')
       designation = request.query_params.get('designation')
       src_module = request.query_params.get('src_module')

       try:
           draft_files = view_drafts(username, designation, src_module)
           return Response(draft_files, status=status.HTTP_200_OK)
       except Exception as e:
           return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       
class ArchiveFileView(APIView):
   authentication_classes = [TokenAuthentication]
   permission_classes = [permissions.IsAuthenticated]

   def get(self, request):
       username = request.query_params.get('username')
       designation = request.query_params.get('designation', '')
       src_module = request.query_params.get('src_module')
       try:
           archived_files = view_archived(username, designation, src_module)
           return Response(archived_files, status=status.HTTP_200_OK)
       except Exception as e:
           return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

     
class CreateArchiveFile(APIView):
   authentication_classes = [TokenAuthentication]
   permission_classes = [permissions.IsAuthenticated]

   def post(self, request):
       file_id = request.data.get('file_id', None)

       if file_id is None:
           return Response({'error': 'Missing file_id'}, status=status.HTTP_400_BAD_REQUEST)

       try:
           success = archive_file(file_id)
           if success:
               return Response({'success': True})
           else:
               return Response({'error': 'File does not exist'}, status=status.HTTP_404_NOT_FOUND)

       except Exception as e:
           return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UnArchiveFile(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
         file_id = request.data.get('file_id', None)
    
         if file_id is None:
              return Response({'error': 'Missing file_id'}, status=status.HTTP_400_BAD_REQUEST)
    
         try:
              success = unarchive_file(file_id)
              if success:
                return Response({'success': True})
              else:
                return Response({'error': 'File does not exist'}, status=status.HTTP_404_NOT_FOUND)
    
         except Exception as e:
              return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
class GetDesignationsView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, username, *args, **kwargs):
        user_designations = get_designations(username)
        return Response({'designations': user_designations})

class AjaxDropdownView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    """
    Returns usernames of receivers that match the search input.
    """

    def post(self, request):
        value = request.data.get('value', '')  # Default to empty string if missing
        users = User.objects.filter(username__startswith=value)
        users_json = serializers.serialize('json', users)
        return Response({"users": users_json})
