import json
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
from .serializers import Club_memberSerializer,Core_teamSerializer,Club_infoSerializer,Club_DetailsSerializer,Session_infoSerializer, Voting_choicesSerializer,event_infoserializer,club_budgetserializer,Club_reportSerializers,Fest_budgerSerializer,Registration_formSerializer,Voting_pollSerializer
from django.contrib.auth.models import User
from applications.gymkhana.views import *

class ActCalendarAPIView(APIView):
    """
    API endpoint to upload the activity calendar of a club.
    """

    def post(self, request):
        """
        Handles POST requests to upload the activity calendar.
        """
        try:
            # Getting form data
            club = request.data.get("club")
            act_calender = request.FILES.get("act_file")
            act_calender.name = f"{club}_act_calender.pdf"

            # Update club's activity calendar
            club_info = get_object_or_404(Club_info, club_name=club)
            club_info.activity_calender = act_calender
            club_info.save()

            message = f"Successfully uploaded the calendar for {club} !!!"

            # Prepare response JSON
            content = {
                'status': "success",
                'message': message,
            }
            return Response(content, status=201)  # HTTP 201 Created
        except Exception as e:
            error_message = "Some error occurred"
            logger.error(f"Error in uploading activity calendar: {e}")
            content = {
                'status': "error",
                'message': error_message,
            }
            return Response(content, status=500)
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
    for i in Club_info.objects.all():
        co = (str(i.co_ordinator)).split(" ")
        co_co=(str(i.co_coordinator)).split(" ")
        if co[0]==str(request.user) or co_co[0] == str(request.user):
            club_info.append(serializers.ClubInfoSerializer(i).data)
	
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

class ClubMemberAPIView(APIView):
    def get(self, request):
        club_members = Club_member.objects.all()
        serializer = Club_memberSerializer(club_members, many=True)
        return Response(serializer.data)        
    
class VotingPollAPIView(APIView):
    """
    API endpoint to create a new voting poll.
    """

    def post(self, request):
        """
        This method handles POST requests to create a new voting poll.
        """
        try:
            # Initialize serializers
            poll_serializer = Voting_pollSerializer(data=request.data)
            choices_serializer = Voting_choicesSerializer(data=request.data.get('choices'), many=True)

            # Validate both serializers
            poll_valid = poll_serializer.is_valid()
            choices_valid = choices_serializer.is_valid()

            if poll_valid and choices_valid:
                # Save the validated data
                poll_instance = poll_serializer.save()

                # Save choices associated with the poll
                choices_serializer.save(poll_event=poll_instance)

                # Print success message
                print("Voting poll created successfully")

                # Redirect to a different URL only if necessary
                # Modify this logic based on your requirements
                if request.accepted_renderer.format == 'html':
                    return redirect('/gymkhana/')
                else:
                    # Return serialized poll data along with choices
                    poll_data = poll_serializer.data
                    poll_data['choices'] = choices_serializer.data
                    return Response(poll_data, status=status.HTTP_201_CREATED)
            else:
                # If serializer validation fails, return errors
                errors = {}
                if not poll_valid:
                    errors['poll_errors'] = poll_serializer.errors
                if not choices_valid:
                    errors['choices_errors'] = choices_serializer.errors
                print(errors)  # Log errors to console
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log any exceptions that occur during the process
            print("Exception occurred:", str(e))
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


##logger = logging.getLogger(_NamedFuncPointer)

class NewSessionAPIView(APIView):
    """
    API endpoint to create a new session for a club.
    """

    def post(self, request):
        """
        Handle POST requests to create a new session.
        """
        try:
            serializer = Session_infoSerializer(data=request.data)
            if serializer.is_valid():
                # Save the validated data
                session_instance = serializer.save()

                # Check for conflicts with existing sessions
                result = conflict_algorithm_session(session_instance.date,
                                                     session_instance.start_time,
                                                     session_instance.end_time,
                                                     session_instance.venue)
                if result == "success":
                    # Notify users about the new session
                    getstudents = ExtraInfo.objects.select_related('user', 'department').filter(user_type='student')
                    recipients = User.objects.filter(extrainfo__in=getstudents)
                    gymkhana_session(request.user, recipients, 'new_session', session_instance.club,
                                     session_instance.details, session_instance.venue)

                    # Print success message
                    print("Session booked successfully")

                    # Redirect to a different URL only if necessary
                    # Modify this logic based on your requirements
                    if request.accepted_renderer.format == 'html':
                        return redirect('/gymkhana/')
                    else:
                        return Response(serializer.data, status=status.HTTP_201_CREATED)
                else:
                    return Response({"error": "The selected time slot for the given date and venue conflicts with an already booked session"},
                                    status=status.HTTP_409_CONFLICT)
            else:
                # If serializer validation fails, return errors
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log any exceptions that occur during the process
            logger.exception("Exception occurred: %s", str(e))
            return Response({"error": "Some error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteEventsView(APIView):
    """
    API endpoint to delete events.
    """

    def post(self, request):
        """
        Handle POST requests to delete events.
        """
        try:
            events_deleted = []
            events_not_found = []
            
            # Ensure that request.data is a dictionary
            event_data_list = request.data if isinstance(request.data, list) else []

            for event_data in event_data_list:
                name = event_data.get('event_name')
                venue = event_data.get('venue')
                incharge = event_data.get('incharge')
                date = event_data.get('date')

                # Query Event_info based on the provided parameters
                event = Event_info.objects.filter(
                    event_name=name,
                    venue=venue,
                    incharge=incharge,
                    date=date
                ).first()

                if event:
                    event.delete()
                    events_deleted.append(event_data)
                else:
                    events_not_found.append(event_data)

            response_data = {
                "events_deleted": events_deleted,
                "events_not_found": events_not_found
            }

            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)



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
                details = session_data.get('details')

                # Query Session_info based on the provided parameters
                session = Session_info.objects.filter(
                    venue=venue,
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                    details=details
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
