import genericpath
import json
import tempfile
from datetime import datetime
from venv import logger
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import render
from applications.gymkhana.models import Voting_choices, Registration_form, Student ,Club_info,Club_member,Core_team,Session_info,Event_info,Club_budget,Club_report,Fest_budget,Registration_form,Voting_polls
from .serializers import Club_memberSerializer,Core_teamSerializer,Club_DetailsSerializer,Session_infoSerializer, Voting_choicesSerializer,event_infoserializer,club_budgetserializer,Club_reportSerializers,Fest_budgerSerializer,Registration_formSerializer,Voting_pollSerializer, Club_infoSerializer

from django.contrib.auth.models import User
from applications.gymkhana.views import *
from rest_framework import generics
from django.core.files.base import ContentFile
import base64

from rest_framework.parsers import MultiPartParser

class UploadActivityCalendarAPIView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, format=None):
        # Get the club name from the request data
        club_name = request.data.get('club_name')

        # Retrieve the club object from the database
        try:
            club = Club_info.objects.get(club_name=club_name)
        except Club_info.DoesNotExist:
            return Response({'error': f'Club with name {club_name} does not exist'}, status=status.HTTP_404_NOT_FOUND)

        # Update the activity calendar file
        club.activity_calender = request.data.get('activity_calender')

        # Save the updated club object
        club.save()

        return Response({'message': 'Activity calendar updated successfully'}, status=status.HTTP_200_OK)


class VoteIncrementAPIView(APIView):
    def post(self, request):
        serializer = Voting_choicesSerializer(data=request.data, many=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        for choice_data in data:
            poll_event_id = choice_data.get('poll_event')
            title = choice_data.get('title')
            try:
                choice_instance = Voting_choices.objects.get(poll_event_id=poll_event_id, title=title)
                choice_instance.votes += 1
                choice_instance.save()
            except Voting_choices.DoesNotExist:
                pass  # Do nothing if the choice with the given poll_event and title doesn't exist
        
        return Response({'message': 'Votes incremented successfully'}, status=status.HTTP_200_OK)


class VotingPollsDeleteAPIView(APIView):
   def post(self, request):
        Voting_poll_id = request.data.get('id')  # Assuming the ID is sent in the request body
        try:
            Voting_poll  = Voting_polls.objects.get(id=Voting_poll_id)
        except Voting_polls.DoesNotExist:
            return Response({"error": "Voting Poll not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Delete the club member object
        Voting_poll.delete()

        return Response({"message": "POll deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


class ShowVotingChoicesAPIView(APIView):
    def get(self, request):
        voting_choices = Voting_choices.objects.all()
        serializer = Voting_choicesSerializer(voting_choices, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ClubMemberApproveView(generics.UpdateAPIView):
    def post(self, request):
        club_member_id = request.data.get('id')  # Assuming the ID is sent in the request body
        try:
            club_member = Club_member.objects.get(id=club_member_id)
        except Club_member.DoesNotExist:
            return Response({"error": "Club member not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Update the status of the club member
        club_member.status = 'confirmed'  # Assuming 'confirmed' is the status for approval
        club_member.save()

        return Response({"message": "Status updated successfully."}, status=status.HTTP_200_OK)


class ClubMemberDeleteAPIView(APIView):
    def post(self, request):
        club_member_id = request.data.get('id')  # Assuming the ID is sent in the request body
        try:
            club_member = Club_member.objects.get(id=club_member_id)
        except Club_member.DoesNotExist:
            return Response({"error": "Club member not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Delete the club member object
        club_member.delete()

        return Response({"message": "Club member deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

# class UpdateClubDetailsAPIView(APIView):
#     def post(self, request, *args, **kwargs):
#         club_name = request.data.get('club_name')
#         co_coordinator = request.data.get('co_coordinator')
#         co_ordinator = request.data.get('co_ordinator')
        
#         print(f"Received request data: club_name={club_name}, co_coordinator={co_coordinator}, co_ordinator={co_ordinator}")

#         # Retrieve the Club_info object by club_name
#         try:
#             club_info = Club_info.objects.get(club_name=club_name)
#         except Club_info.DoesNotExist:
#             return Response({"message": "Club not found"}, status=status.HTTP_404_NOT_FOUND)
        
#         print(f"Found Club_info object: {club_info}")
        
#         # Update the details provided in the request
#         serializer = Club_infoSerializer(instance=club_info, data={'co_coordinator': co_coordinator, 'co_ordinator': co_ordinator}, partial=True)
#         if serializer.is_valid():
#             print("Serializer is valid. Saving...")
#             serializer.save()
#             print("Data saved successfully.")
#             return Response(serializer.data)
#         else:
#             print(f"Serializer errors: {serializer.errors}")
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangeHeadAPIView(APIView):
    def post(self, request):
        club = request.data.get("club_name")
        co_ordinator = request.data.get('co_ordinator')
        co_coordinator = request.data.get('co_coordinator')

        if not club or (not co_ordinator and not co_coordinator):
            return JsonResponse({'status': 'error', 'message': 'Invalid request parameters'})

        try:
            club_info = Club_info.objects.get(club_name=club)
        except Club_info.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Club not found'})

        message = ""

        if co_ordinator:
            if not Club_member.objects.filter(club_id=club, member_id=co_ordinator).exists():
                return JsonResponse({'status': 'error', 'message': 'Selected student is not a member of the club'})
            
            try:
                co_ordinator_student = Student.objects.get(id_id=co_ordinator)
                old_co_ordinator = club_info.co_ordinator_id
                club_info.co_ordinator_id = co_ordinator_student
                
                new_co_ordinator = HoldsDesignation(
                    user=User.objects.get(username=co_ordinator),
                    working=User.objects.get(username=co_ordinator),
                    designation=Designation.objects.get(name="co-ordinator")
                )
                new_co_ordinator.save()

                HoldsDesignation.objects.filter(
                    user__username=old_co_ordinator,
                    designation=Designation.objects.get(name="co-ordinator")
                ).delete()

                message += "Successfully changed co-ordinator !!!"
            except Student.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Selected student not found'})

        if co_coordinator:
            if not Club_member.objects.filter(club_id=club, member_id=co_coordinator).exists():
                return JsonResponse({'status': 'error', 'message': 'Selected student is not a member of the club'})

            try:
                co_coordinator_student = Student.objects.get(id_id=co_coordinator)
                old_co_coordinator = club_info.co_coordinator_id
                club_info.co_coordinator_id = co_coordinator_student
                
                new_co_coordinator = HoldsDesignation(
                    user=User.objects.get(username=co_coordinator),
                    working=User.objects.get(username=co_coordinator),
                    designation=Designation.objects.get(name="co co-ordinator")
                )
                new_co_coordinator.save()

                HoldsDesignation.objects.filter(
                    user__username=old_co_coordinator,
                    designation=Designation.objects.get(name="co co-ordinator")
                ).delete()

                message += "Successfully changed co-coordinator !!!"
            except Student.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Selected student not found'})

        club_info.head_changed_on = timezone.now()
        club_info.save()

        return JsonResponse({'status': "success", 'message': message})
class AddMemberToClub(APIView):
    def post(self, request):
        serializer = Club_memberSerializer(data=request.data)
        if serializer.is_valid():
            club_id = request.data.get('club')  # Assuming 'club_id' is passed in the request data
            try:
                club_member = serializer.save()
                # Implement logic to add member to the club here
                # For example, you can retrieve the club instance and add the member to it
                # club = Club.objects.get(pk=club_id)
                # club.members.add(club_member)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClubMemberAPIView(APIView):
    def get(self, request):
        club_members = Club_member.objects.all()
        serializer = Club_memberSerializer(club_members, many=True)
        return Response(serializer.data)
    
class RegistrationFormAPIView(APIView):
    """
    API endpoint to handle registration form submissions.
    """

    def post(self, request):
        """
        Handles POST requests to save registration form data.
        """
        try:
            # Getting form data
            user_name = request.data.get("user_name")
            print(user_name)
            roll = request.data.get("roll")
            cpi = request.data.get("cpi")
            branch = request.data.get("branch")
            programme = request.data.get("programme")
            print(programme)
            
            # Check if the user has already submitted the form
            if Registration_form.objects.filter(user_name=user_name).exists():
                raise Exception("User has already filled the form.")

            # Saving data to the database
            registration = Registration_form(user_name=user_name, branch=branch, roll=roll, cpi=cpi, programme=programme)
            try:
                registration.save()
    # If no exception occurred, the save operation was successful
                print("Save operation successful")
                serializer = Registration_formSerializer(registration)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
    # If an exception occurred, print the error message or log it
                 print(f"Error occurred while saving registration: {e}")

            print(registration.user_name)

            # Serialize the response
           
        except Exception as e:
            error_message = "Some error occurred"
            logger.error(f"Error in registration form submission: {e}")
            return Response({"status": "error", "message": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
def coordinator_club(request):
    club_info = []
    for club in Club_info.objects.all():
        if str(request.user) in [club.co_ordinator, club.co_coordinator]:
            serialized_club = Club_infoSerializer(club).data
            club_info.append(serialized_club)
    return club_info

class core(APIView):
    def get(self,request):
        co=Core_team.objects.all()
        serializer=Core_teamSerializer(co, many=True)
        print(serializer.data)
        return Response(serializer.data)

class clubname(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        authentication_classes = [TokenAuthentication]
        clubname1 = Club_info.objects.all()
        serializer = Club_infoSerializer(clubname1, many = True)
        return Response(serializer.data)

class  Club_Details(APIView):

    def get(self,respect):
        clubdetail=Club_info.objects.all()
        serializer=Club_DetailsSerializer(clubdetail, many=True)
        return Response(serializer.data)

class session_details(APIView):
    def get(self,respect):
        session = Session_info.objects.all()
        serializer = Session_infoSerializer(session, many = True)
        return Response(serializer.data)

class club_events(APIView):
    def get(self,respect):
        clubevents=Event_info.objects.all()
        serializer=event_infoserializer(clubevents, many = True)
        return Response(serializer.data)

class club_budgetinfo(APIView):
    def get(self,respect):
        clubbudget=Club_budget.objects.all()
        serializer=club_budgetserializer(clubbudget, many=True)
        return Response(serializer.data)

class club_report(APIView):
    def get(self,respect):
        clubreport = Club_report.objects.all()
        serializer = Club_reportSerializers(clubreport , many=True)
        return Response(serializer.data)

class Fest_Budget(APIView):

    def get(self,respect):
        festbudget=Fest_budget.objects.all()
        serializer=Fest_budgerSerializer(festbudget, many=True)
        return Response(serializer.data)

class Registraion_form(APIView):

    def get(self,respect):
        registration=Registration_form.objects.all()
        serializer=Registration_formSerializer(registration, many=True)
        return Response(serializer.data)


class Voting_Polls(APIView):

    def get(self,respect):
        votingpolls=Voting_polls.objects.all()
        serializer=Voting_pollSerializer(votingpolls, many=True)
        return Response(serializer.data)

##logger = logging.getLogger(_NamedFuncPointer)
class NewSessionAPIView(APIView):
    def get(self, request):
        sessions = Session_info.objects.all()
        serializer = Session_infoSerializer(sessions, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer =Session_infoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NewEventAPIView(APIView):
    def get(self, request):
        events = Event_info.objects.all()
        serializer = event_infoserializer(events, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = event_infoserializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    


# class DeleteEventsView(APIView):
#     """
#     API endpoint to delete events.
#     """

#     def post(self, request):
#         """
#         Handle POST requests to delete events.
#         """
#         try:
#             events_deleted = []
#             events_not_found = []
            
#             # Ensure that request.data is a dictionary
#             event_data_list = request.data if isinstance(request.data, list) else []

#             for event_data in event_data_list:
#                 name = event_data.get('event_name')
#                 venue = event_data.get('venue')
#                 incharge = event_data.get('incharge')
#                 date = event_data.get('date')
#                 event_id = event_data.get('id')

#                 # Query Event_info based on the provided parameters
#                 event = Event_info.objects.filter(
#                     event_name=name,
#                     venue=venue,
#                     incharge=incharge,
#                     date=date,
#                     event_id=id,
#                 ).first()

#                 if event:
#                     event.delete()
#                     events_deleted.append(event_data)
#                 else:
#                     events_not_found.append(event_data)

#             response_data = {
#                 "events_deleted": events_deleted,
#                 "events_not_found": events_not_found
#             }

#             return Response(response_data, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EventDeleteAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Retrieve data from request
        event_data = request.data

        # Check if 'id' parameter is provided
        if 'id' not in event_data:
            return Response({'error': 'The "id" parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Get the event by id
        event_id = event_data['id']
        try:
            event = Event_info.objects.get(id=event_id)
        except Event_info.DoesNotExist:
            return Response({'error': 'Event not found with the provided id'}, status=status.HTTP_404_NOT_FOUND)

        # Delete the event
        event.delete()

        return Response({'message': 'Event deleted successfully'}, status=status.HTTP_200_OK)


class SessionUpdateAPIView(APIView):
    def post(self, request):
        session_id = request.data.get('id')
        if session_id is None:
            return Response({'error': 'Session ID not provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            session_instance = Session_info.objects.get(id=session_id)
        except Session_info.DoesNotExist:
            return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = Session_infoSerializer(instance=session_instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class EventUpdateAPIView(APIView):
    def post(self, request):
        event_id = request.data.get('id')
        if event_id is None:
            return Response({'error': 'Event ID not provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            event_instance = Event_info.objects.get(id=event_id)
        except Event_info.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = event_infoserializer(instance=event_instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteSessionsView(APIView):
    """
    API endpoint to delete sessions.
    """

    def post(self, request):
        """
        Handle POST requests to delete sessions.
        """
        try:
            # Get the list of session data from the request
            session_data_list = json.loads(request.body)

            sessions_deleted = []
            sessions_not_found = []

            # Iterate over each session data
            for session_data in session_data_list:
                venue = session_data.get('venue')
                date = session_data.get('date')
                start_time = session_data.get('start_time')
                end_time = session_data.get('end_time')

                # Query Session_info based on the provided parameters
                session = Session_info.objects.filter(
                    venue=venue,
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                ).first()

                if session:
                    session.delete()
                    sessions_deleted.append(session_data)
                else:
                    sessions_not_found.append(session_data)

            response_data = {
                "sessions_deleted": sessions_deleted,
                "sessions_not_found": sessions_not_found
            }

            return JsonResponse(response_data, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class CreateVotingPollAPIView(APIView):
    def post(self, request):
        voting_poll_serializer = Voting_pollSerializer(data=request.data)
        if voting_poll_serializer.is_valid():
            voting_poll_instance = voting_poll_serializer.save()

            # Extract ID of the created Voting_poll instance
            voting_poll_id = voting_poll_instance.id

            # Modify the request data to include poll_event ID for each choice
            choices_data = request.data.get('choices', [])
            for choice_data in choices_data:
                choice_data['poll_event'] = voting_poll_id

            voting_choices_serializer = Voting_choicesSerializer(data=choices_data, many=True)
            if voting_choices_serializer.is_valid():
                voting_choices_serializer.save()
                return Response({'message': 'Voting poll created successfully'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'voting_choices_errors': voting_choices_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'voting_poll_errors': voting_poll_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
class UpdateClubBudgetAPIView(APIView):
    def post(self, request):
        budget_id = request.data.get('id')
        if budget_id is None:
            return Response({'error': 'Club budget ID not provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            budget_instance = Club_budget.objects.get(pk=budget_id)
        except Club_budget.DoesNotExist:
            return Response({'error': 'Club budget not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = club_budgetserializer(instance=budget_instance, data=request.data, partial = True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    

class AddClub_BudgetAPIView(APIView):
    def post(self, request):
        # Get the string representation of the file content
        budget_file_content = request.data.get('budget_file')

        # Convert the string to a file object
        file_obj = None
        if budget_file_content:
    # Create a ContentFile object
            file_obj = ContentFile(budget_file_content.encode(), name='temp_file.txt')

# Update the request data with the File object
            request.data['budget_file'] = file_obj

        # Update the request data with the file object
        request.data['budget_file'] = file_obj

        # Initialize the serializer with the modified request data
        serializer = club_budgetserializer(data=request.data)

        # Validate and save the serializer data
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  


class DeleteClubBudgetAPIView(APIView):
    def post(self, request):
        budget_id = request.data.get('id')
        if budget_id is None:
            return Response({'error': 'Club budget ID not provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            budget_instance = Club_budget.objects.get(pk=budget_id)
        except Club_budget.DoesNotExist:
            return Response({'error': 'Club budget not found'}, status=status.HTTP_404_NOT_FOUND)

        budget_instance.delete()
        return Response({'message': 'Club budget deleted successfully'}, status=status.HTTP_200_OK)    


class DeleteClubAPIView(APIView):
    def post(self, request):
        # Retrieve data from request
        club_data = request.data

        # Extract fields for filtering
        club_name = club_data.get('club_name')
        category = club_data.get('category')
        co_ordinator = club_data.get('co_ordinator')
        co_coordinator = club_data.get('co_coordinator')
        faculty_incharge = club_data.get('faculty_incharge')

        # Check if all required fields are provided
        if not all([club_name, category, co_ordinator, co_coordinator, faculty_incharge]):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        # Try to find the club based on provided fields
        try:
            club = Club_info.objects.get(
                club_name=club_name,
                category=category,
                co_ordinator=co_ordinator,
                co_coordinator=co_coordinator,
                faculty_incharge=faculty_incharge
            )
        except Club_info.DoesNotExist:
            return Response({"error": "Club not found"}, status=status.HTTP_404_NOT_FOUND)

        # Delete the club from the database
        club.delete()

        return Response({"message": "Club deleted successfully"}, status=status.HTTP_200_OK)
    

# class ClubCreateAPIView(APIView):
#     def post(self, request, format=None):
#         data = {
#             'club_name': request.data.get('club_name'),
#             'category': request.data.get('category'),
#             'co_ordinator': request.data.get('co_ordinator'),
#             'co_coordinator': request.data.get('co_coordinator'),
#             'faculty_incharge': request.data.get('faculty_incharge'),
#             'club_file': request.data.get('club_file'),
#             'activity_calender': request.data.get('activity_calender'),
#             'description': request.data.get('description'),
#             'status': request.data.get('status'),
#             'head_changed_on': request.data.get('head_changed_on'),
#             'created_on': request.data.get('created_on'),
#         }
#         serializer = Club_infoSerializer(data=data,partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateClubAPIView(APIView):
    def post(self, request):
        # Get the string representation of the file content for club_file
        club_file_content = request.data.get('club_file')

        # Convert the string to a file object for club_file
        club_file_obj = None
        if club_file_content:
            club_file_obj = ContentFile(club_file_content.encode(), name='club_file.txt')

        # Update the request data with the file object for club_file
        request.data['club_file'] = club_file_obj

        # Get the string representation of the file content for activity_calendar
        description = request.data.get('description')

        # Initialize the serializer with the modified request data
        serializer = Club_infoSerializer(data=request.data)

        # Validate and save the serializer data
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class UpdateClubStatusAPIView(APIView):
    def post(self, request):
        # Retrieve data from request
        club_data = request.data

        # Extract fields for filtering
        club_name = club_data.get('club_name')
        co_ordinator = club_data.get('co_ordinator')
        co_coordinator = club_data.get('co_coordinator')
        faculty_incharge = club_data.get('faculty_incharge')

        # Check if all required fields are provided
        if not all([club_name, co_ordinator, co_coordinator, faculty_incharge]):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        # Try to find the club based on provided fields
        try:
            club = Club_info.objects.get(
                club_name=club_name,
                co_ordinator=co_ordinator,
                co_coordinator=co_coordinator,
                faculty_incharge=faculty_incharge
            )
        except Club_info.DoesNotExist:
            return Response({"error": "Club not found"}, status=status.HTTP_404_NOT_FOUND)

        # Update the status of the club
        club.status = 'confirmed'
        club.save()

        return Response({"message": "Club status updated to 'confirmed' successfully"}, status=status.HTTP_200_OK)
    

 



# class UpdateClubNameAPIView(APIView):
#     def post(self, request):
#         # Retrieve data from request
#         club_data = request.data

#         # Extract fields for filtering
#         club_name = club_data.get('club_name')
#         co_ordinator = club_data.get('co_ordinator')
#         co_coordinator = club_data.get('co_coordinator')
#         faculty_incharge = club_data.get('faculty_incharge')
#         new_club = club_data.get('new_club')

#         # Check if all required fields are provided
#         if not all([club_name, co_ordinator, co_coordinator, faculty_incharge]):
#             return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

#         # Try to find the club based on provided fields
#         try:
#             club = Club_info.objects.get(
#                 club_name=club_name,
#                 co_ordinator=co_ordinator,
#                 co_coordinator=co_coordinator,
#                 faculty_incharge=faculty_incharge
#             )
#         except Club_info.DoesNotExist:
#             return Response({"error": "Club not found"}, status=status.HTTP_404_NOT_FOUND)

#         # Update the status of the club
#         club.club_name = new_club
#         club.save()

#         return Response({"message": "Club name updated  successfully"}, status=status.HTTP_200_OK)



class UpdateClubNameAPIView(APIView):
    def post(self, request):
        # Retrieve data from request
        club_data = request.data

        # Extract fields for filtering
        club_name = club_data.get('club_name')
        co_ordinator = club_data.get('co_ordinator')
        co_coordinator = club_data.get('co_coordinator')
        faculty_incharge = club_data.get('faculty_incharge')
        new_club = club_data.get('new_club')

        # Check if all required fields are provided
        if not all([club_name, co_ordinator, co_coordinator, faculty_incharge, new_club]):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        # Try to find the club based on provided fields
        try:
            club = Club_info.objects.get(
                club_name=club_name,
                co_ordinator=co_ordinator,
                co_coordinator=co_coordinator,
                faculty_incharge=faculty_incharge
            )
        except Club_info.DoesNotExist:
            return Response({"error": "Club not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if a club with the new name already exists
        if Club_info.objects.filter(club_name=new_club).exists():
            return Response({"error": f"A club with the name '{new_club}' already exists"}, status=status.HTTP_400_BAD_REQUEST)

        # Update the status of the club
        club.club_name = new_club
        club.save()

        # Delete the original club entry
        Club_info.objects.filter(club_name=club_name).delete()

        return Response({"message": "Club name updated successfully"}, status=status.HTTP_200_OK)
    


class ApproveEvent(APIView):
    def post(self, request):
        # Retrieve data from request
        event_data = request.data

        # Extract fields for filtering
        event_name = event_data.get('event_name')
        incharge = event_data.get('incharge')
        date = event_data.get('date')
        venue = event_data.get('venue')
        event_id = event_data.get('id')
        # status = event_data.get('status')

        # Check if all required fields are provided
        if not all([event_name, incharge, date, venue, event_id]):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        # Try to find the event based on provided fields
        try:
            event = Event_info.objects.get(
                event_name=event_name,
                incharge=incharge,
                date=date,
                venue=venue,
                id=event_id
            )
        except Event_info.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        # Update the status of the event
        event.status = 'confirmed'
        event.save()

        return Response({"message": "event status updated successfully"}, status=status.HTTP_200_OK)   