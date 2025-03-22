import genericpath
import json
import tempfile
from datetime import datetime, timedelta
from venv import logger
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import render
from applications.gymkhana.models import (
    Registration_form,
    Student,
    Club_info,
    Club_member,
    Session_info,
    Event_info,
    Club_budget,
    Club_report,
    Fest_budget,
    Registration_form,
    Budget,
    Achievements,
    ClubPosition,
    Fest,
)
from .serializers import (
    Club_memberSerializer,
    Club_DetailsSerializer,
    Session_infoSerializer,
    event_infoserializer,
    club_budgetserializer,
    Club_reportSerializers,
    Fest_budgerSerializer,
    Registration_formSerializer,
    Club_infoSerializer,
    BudgetSerializer,
    AchievementsSerializer,
    Event_CommentsSerializer,
    Budget_CommentsSerializer,
    ClubPositionSerializer,
    FestSerializer,
    EventInputSerializer
)

from io import BytesIO
from django.http import FileResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, HRFlowable, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.contrib.auth.models import User
from applications.gymkhana.views import *
from rest_framework import generics
from django.core.files.base import ContentFile
import base64

from rest_framework.parsers import MultiPartParser


class Budgetinfo(APIView):
    def get(self, request):
        budgets = Budget.objects.all()
        serializer = BudgetSerializer(budgets, many=True)
        return Response(serializer.data)


class Club_Detail(APIView):
    def post(self, request):
        club_name = request.data.get("club_name")
        if not club_name:
            return Response(
                {"error": "club_name is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        clubdetail = get_object_or_404(Club_info, club_name=club_name)
        serializer = Club_DetailsSerializer(clubdetail)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpcomingEventsAPIView(APIView):
    def get(self, request):
        events = Event_info.objects.filter(
            start_date__gte=datetime.datetime.now()
        ).order_by("start_date")
        serializer = event_infoserializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PastEventsAPIView(APIView):
    def get(self, request):
        events = Event_info.objects.filter(
            end_date__lt=datetime.datetime.now()
        ).order_by("end_date")
        serializer = event_infoserializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UploadActivityCalendarAPIView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, format=None):
        # Get the club name from the request data
        club_name = request.data.get("club_name")

        # Retrieve the club object from the database
        try:
            club = Club_info.objects.get(club_name=club_name)
        except Club_info.DoesNotExist:
            return Response(
                {"error": f"Club with name {club_name} does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Update the activity calendar file
        club.activity_calender = request.data.get("activity_calender")

        # Save the updated club object
        club.save()

        return Response(
            {"message": "Activity calendar updated successfully"},
            status=status.HTTP_200_OK,
        )


# class VoteIncrementAPIView(APIView):
#     def post(self, request):
#         serializer = Voting_choicesSerializer(data=request.data, many=True)
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         data = serializer.validated_data
#         for choice_data in data:
#             poll_event_id = choice_data.get('poll_event')
#             title = choice_data.get('title')
#             try:
#                 choice_instance = Voting_choices.objects.get(poll_event_id=poll_event_id, title=title)
#                 choice_instance.votes += 1
#                 choice_instance.save()
#             except Voting_choices.DoesNotExist:
#                 pass  # Do nothing if the choice with the given poll_event and title doesn't exist

# return Response({'message': 'Votes incremented successfully'}, status=status.HTTP_200_OK)


# class VotingPollsDeleteAPIView(APIView):
#    def post(self, request):
#         Voting_poll_id = request.data.get('id')  # Assuming the ID is sent in the request body
#         try:
#             Voting_poll  = Voting_polls.objects.get(id=Voting_poll_id)
#         except Voting_polls.DoesNotExist:
#             return Response({"error": "Voting Poll not found."}, status=status.HTTP_404_NOT_FOUND)

#         # Delete the club member object
#         Voting_poll.delete()

#         return Response({"message": "POll deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


# class ShowVotingChoicesAPIView(APIView):
#     def get(self, request):
#         voting_choices = Voting_choices.objects.all()
#         serializer = Voting_choicesSerializer(voting_choices, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)


class ClubMemberApproveView(generics.UpdateAPIView):
    def post(self, request):
        club_member_id = request.data.get(
            "id"
        )  # Assuming the ID is sent in the request body
        try:
            club_member = Club_member.objects.get(id=club_member_id)
        except Club_member.DoesNotExist:
            return Response(
                {"error": "Club member not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Update the status of the club member
        club_member.status = "member"  # Assuming 'member' is the status for approval
        club_member.save()

        return Response(
            {"message": "Status updated successfully."}, status=status.HTTP_200_OK
        )


class ClubMemberDeleteAPIView(APIView):
    def post(self, request):
        club_member_id = request.data.get(
            "id"
        )  # Assuming the ID is sent in the request body
        try:
            club_member = Club_member.objects.get(id=club_member_id)
        except Club_member.DoesNotExist:
            return Response(
                {"error": "Club member not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Delete the club member object
        club_member.delete()

        return Response(
            {"message": "Club member deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )


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
        co_ordinator = request.data.get("co_ordinator")
        co_coordinator = request.data.get("co_coordinator")

        if not club or (not co_ordinator and not co_coordinator):
            return JsonResponse(
                {"status": "error", "message": "Invalid request parameters"}
            )

        try:
            club_info = Club_info.objects.get(club_name=club)
        except Club_info.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Club not found"})

        message = ""

        if co_ordinator:
            if not Club_member.objects.filter(
                club_id=club, member_id=co_ordinator
            ).exists():
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "Selected student is not a member of the club",
                    }
                )

            try:
                co_ordinator_student = Student.objects.get(id_id=co_ordinator)
                old_co_ordinator = club_info.co_ordinator_id
                club_info.co_ordinator_id = co_ordinator_student

                new_co_ordinator = HoldsDesignation(
                    user=User.objects.get(username=co_ordinator),
                    working=User.objects.get(username=co_ordinator),
                    designation=Designation.objects.get(name="co-ordinator"),
                )
                new_co_ordinator.save()

                HoldsDesignation.objects.filter(
                    user__username=old_co_ordinator,
                    designation=Designation.objects.get(name="co-ordinator"),
                ).delete()

                message += "Successfully changed co-ordinator !!!"
            except Student.DoesNotExist:
                return JsonResponse(
                    {"status": "error", "message": "Selected student not found"}
                )

        if co_coordinator:
            if not Club_member.objects.filter(
                club_id=club, member_id=co_coordinator
            ).exists():
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "Selected student is not a member of the club",
                    }
                )

            try:
                co_coordinator_student = Student.objects.get(id_id=co_coordinator)
                old_co_coordinator = club_info.co_coordinator_id
                club_info.co_coordinator_id = co_coordinator_student

                new_co_coordinator = HoldsDesignation(
                    user=User.objects.get(username=co_coordinator),
                    working=User.objects.get(username=co_coordinator),
                    designation=Designation.objects.get(name="co co-ordinator"),
                )
                new_co_coordinator.save()

                HoldsDesignation.objects.filter(
                    user__username=old_co_coordinator,
                    designation=Designation.objects.get(name="co co-ordinator"),
                ).delete()

                message += "Successfully changed co-coordinator !!!"
            except Student.DoesNotExist:
                return JsonResponse(
                    {"status": "error", "message": "Selected student not found"}
                )

        club_info.head_changed_on = timezone.now()
        club_info.save()

        return JsonResponse({"status": "success", "message": message})


class AddMemberToClub(APIView):
    def post(self, request):
        data = {
            "member": request.data.get("member"),
            "club": request.data.get("club"),
            "description": request.data.get("description"),
            "status": "open",
        }
        serializer = Club_memberSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClubMemberAPIView(APIView):
    def post(self, request):
        club_member_id = request.data.get("club_name")
        club_members = Club_member.objects.filter(club_id=club_member_id)
        serializer = Club_memberSerializer(club_members, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
            registration = Registration_form(
                user_name=user_name,
                branch=branch,
                roll=roll,
                cpi=cpi,
                programme=programme,
            )
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
            return Response(
                {"status": "error", "message": error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


def coordinator_club(request):
    club_info = []
    for club in Club_info.objects.all():
        if str(request.user) in [club.co_ordinator, club.co_coordinator]:
            serialized_club = Club_infoSerializer(club).data
            club_info.append(serialized_club)
            return club_info


# class core(APIView):
#     def get(self,request):
#         co=Core_team.objects.all()
#         serializer=Core_teamSerializer(co, many=True)
#         print(serializer.data)
#         return Response(serializer.data)


class clubname(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        authentication_classes = [TokenAuthentication]
        clubname1 = Club_info.objects.all()
        serializer = Club_infoSerializer(clubname1, many=True)
        return Response(serializer.data)


class Club_Details(APIView):

    def get(self, respect):
        clubdetail = Club_info.objects.all()
        serializer = Club_DetailsSerializer(clubdetail, many=True)
        return Response(serializer.data)


class session_details(APIView):
    def get(self, respect):
        session = Session_info.objects.all()
        serializer = Session_infoSerializer(session, many=True)
        return Response(serializer.data)


class club_events(APIView):
    def get(self, respect):
        clubevents = Event_info.objects.all()
        serializer = event_infoserializer(clubevents, many=True)
        return Response(serializer.data)


class club_budgetinfo(APIView):
    def get(self, respect):
        clubbudget = Club_budget.objects.all()
        serializer = club_budgetserializer(clubbudget, many=True)
        return Response(serializer.data)


class club_report(APIView):
    def get(self, respect):
        clubreport = Club_report.objects.all()
        serializer = Club_reportSerializers(clubreport, many=True)
        return Response(serializer.data)


class Fest_Budget(APIView):

    def get(self, respect):
        festbudget = Fest_budget.objects.all()
        serializer = Fest_budgerSerializer(festbudget, many=True)
        return Response(serializer.data)


class Registraion_form(APIView):

    def get(self, respect):
        registration = Registration_form.objects.all()
        serializer = Registration_formSerializer(registration, many=True)
        return Response(serializer.data)
class FestListView(APIView):
    def get(self,respect):
        fests=Fest.objects.all();
        serializer=FestSerializer(fests, many=True)
        return Response(serializer.data)

# class Voting_Polls(APIView):

#     def get(self,respect):
#         votingpolls=Voting_polls.objects.all()
#         serializer=Voting_pollSerializer(votingpolls, many=True)
#         return Response(serializer.data)


##logger = logging.getLogger(_NamedFuncPointer)
class NewSessionAPIView(APIView):
    def get(self, request):
        sessions = Session_info.objects.all()
        serializer = Session_infoSerializer(sessions, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = Session_infoSerializer(data=request.data)
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

class NewFestAPIView(APIView):
    def get(self, request):
        fests = Fest.objects.all()
        serializer = FestSerializer(fests, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = FestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
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
        if "id" not in event_data:
            return Response(
                {"error": 'The "id" parameter is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get the event by id
        event_id = event_data["id"]
        try:
            event = Event_info.objects.get(id=event_id)
        except Event_info.DoesNotExist:
            return Response(
                {"error": "Event not found with the provided id"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Delete the event
        event.delete()

        return Response(
            {"message": "Event deleted successfully"}, status=status.HTTP_200_OK
        )


class SessionUpdateAPIView(APIView):
    def post(self, request):
        session_id = request.data.get("id")
        if session_id is None:
            return Response(
                {"error": "Session ID not provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            session_instance = Session_info.objects.get(id=session_id)
        except Session_info.DoesNotExist:
            return Response(
                {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = Session_infoSerializer(
            instance=session_instance, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventUpdateAPIView(APIView):
    def post(self, request):
        event_id = request.data.get("id")
        if event_id is None:
            return Response(
                {"error": "Event ID not provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            event_instance = Event_info.objects.get(id=event_id)
        except Event_info.DoesNotExist:
            return Response(
                {"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = event_infoserializer(
            instance=event_instance, data=request.data, partial=True
        )
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
                venue = session_data.get("venue")
                date = session_data.get("date")
                start_time = session_data.get("start_time")
                end_time = session_data.get("end_time")

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
                "sessions_not_found": sessions_not_found,
            }

            return JsonResponse(response_data, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


# class CreateVotingPollAPIView(APIView):
#     def post(self, request):
#         voting_poll_serializer = Voting_pollSerializer(data=request.data)
#         if voting_poll_serializer.is_valid():
#             voting_poll_instance = voting_poll_serializer.save()

#             # Extract ID of the created Voting_poll instance
#             voting_poll_id = voting_poll_instance.id

#             # Modify the request data to include poll_event ID for each choice
#             choices_data = request.data.get('choices', [])
#             for choice_data in choices_data:
#                 choice_data['poll_event'] = voting_poll_id

#             voting_choices_serializer = Voting_choicesSerializer(data=choices_data, many=True)
#             if voting_choices_serializer.is_valid():
#                 voting_choices_serializer.save()
#                 return Response({'message': 'Voting poll created successfully'}, status=status.HTTP_201_CREATED)
#             else:
#                 return Response({'voting_choices_errors': voting_choices_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             return Response({'voting_poll_errors': voting_poll_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UpdateClubBudgetAPIView(APIView):
    def post(self, request):
        budget_id = request.data.get("id")
        if budget_id is None:
            return Response(
                {"error": "Club budget ID not provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            budget_instance = Club_budget.objects.get(pk=budget_id)
        except Club_budget.DoesNotExist:
            return Response(
                {"error": "Club budget not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = club_budgetserializer(
            instance=budget_instance, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddClub_BudgetAPIView(APIView):
    def post(self, request):
        # Get the string representation of the file content
        budget_file_content = request.data.get("budget_file")

        # Convert the string to a file object
        file_obj = None
        if budget_file_content:
            # Create a ContentFile object
            file_obj = ContentFile(budget_file_content.encode(), name="temp_file.txt")

            # Update the request data with the File object
            request.data["budget_file"] = file_obj

        # Update the request data with the file object
        request.data["budget_file"] = file_obj

        # Initialize the serializer with the modified request data
        serializer = club_budgetserializer(data=request.data)

        # Validate and save the serializer data
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteClubBudgetAPIView(APIView):
    def post(self, request):
        budget_id = request.data.get("id")
        if budget_id is None:
            return Response(
                {"error": "Club budget ID not provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            budget_instance = Club_budget.objects.get(pk=budget_id)
        except Club_budget.DoesNotExist:
            return Response(
                {"error": "Club budget not found"}, status=status.HTTP_404_NOT_FOUND
            )

        budget_instance.delete()
        return Response(
            {"message": "Club budget deleted successfully"}, status=status.HTTP_200_OK
        )


class DeleteClubAPIView(APIView):
    def post(self, request):
        # Retrieve data from request
        club_data = request.data

        # Extract fields for filtering
        club_name = club_data.get("club_name")
        category = club_data.get("category")
        co_ordinator = club_data.get("co_ordinator")
        co_coordinator = club_data.get("co_coordinator")
        faculty_incharge = club_data.get("faculty_incharge")

        # Check if all required fields are provided
        if not all(
            [club_name, category, co_ordinator, co_coordinator, faculty_incharge]
        ):
            return Response(
                {"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Try to find the club based on provided fields
        try:
            club = Club_info.objects.get(
                club_name=club_name,
                category=category,
                co_ordinator=co_ordinator,
                co_coordinator=co_coordinator,
                faculty_incharge=faculty_incharge,
            )
        except Club_info.DoesNotExist:
            return Response(
                {"error": "Club not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Delete the club from the database
        club.delete()

        return Response(
            {"message": "Club deleted successfully"}, status=status.HTTP_200_OK
        )


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
        club_file_content = request.data.get("club_file")

        # Convert the string to a file object for club_file
        club_file_obj = None
        if club_file_content:
            club_file_obj = ContentFile(
                club_file_content.encode(), name="club_file.txt"
            )

        # Update the request data with the file object for club_file
        request.data["club_file"] = club_file_obj

        # Get the string representation of the file content for activity_calendar
        description = request.data.get("description")

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
        club_name = club_data.get("club_name")
        co_ordinator = club_data.get("co_ordinator")
        co_coordinator = club_data.get("co_coordinator")
        faculty_incharge = club_data.get("faculty_incharge")

        # Check if all required fields are provided
        if not all([club_name, co_ordinator, co_coordinator, faculty_incharge]):
            return Response(
                {"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Try to find the club based on provided fields
        try:
            club = Club_info.objects.get(
                club_name=club_name,
                co_ordinator=co_ordinator,
                co_coordinator=co_coordinator,
                faculty_incharge=faculty_incharge,
            )
        except Club_info.DoesNotExist:
            return Response(
                {"error": "Club not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Update the status of the club
        club.status = "confirmed"
        club.save()

        return Response(
            {"message": "Club status updated to 'confirmed' successfully"},
            status=status.HTTP_200_OK,
        )


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
        club_name = club_data.get("club_name")
        co_ordinator = club_data.get("co_ordinator")
        co_coordinator = club_data.get("co_coordinator")
        faculty_incharge = club_data.get("faculty_incharge")
        new_club = club_data.get("new_club")

        # Check if all required fields are provided
        if not all(
            [club_name, co_ordinator, co_coordinator, faculty_incharge, new_club]
        ):
            return Response(
                {"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Try to find the club based on provided fields
        try:
            club = Club_info.objects.get(
                club_name=club_name,
                co_ordinator=co_ordinator,
                co_coordinator=co_coordinator,
                faculty_incharge=faculty_incharge,
            )
        except Club_info.DoesNotExist:
            return Response(
                {"error": "Club not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if a club with the new name already exists
        if Club_info.objects.filter(club_name=new_club).exists():
            return Response(
                {"error": f"A club with the name '{new_club}' already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update the status of the club
        club.club_name = new_club
        club.save()

        # Delete the original club entry
        Club_info.objects.filter(club_name=club_name).delete()

        return Response(
            {"message": "Club name updated successfully"}, status=status.HTTP_200_OK
        )


class ApproveEvent(APIView):
    def post(self, request):
        event_data = request.data
        event_name = event_data.get("event_name")
        incharge = event_data.get("incharge")
        date = event_data.get("date")
        venue = event_data.get("venue")
        event_id = event_data.get("id")
        if not all([event_name, incharge, date, venue, event_id]):
            return Response(
                {"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            event = Event_info.objects.get(
                event_name=event_name,
                incharge=incharge,
                date=date,
                venue=venue,
                id=event_id,
            )
        except Event_info.DoesNotExist:
            return Response(
                {"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND
            )
        event.status = "confirmed"
        event.save()
        return Response(
            {"message": "event status updated successfully"}, status=status.HTTP_200_OK
        )


class AddClubAPI(APIView):
    def post(self, request):
        serializer = Club_infoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Club added successfully!"}, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NewEventAPIView(APIView):
    def put(self, request):
        request.data["status"] = "FIC"
        serializer = event_infoserializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FICApproveEventAPIView(APIView):
    def put(self, request):
        event_id = request.data.get("id")
        event = get_object_or_404(Event_info, id=event_id)
        if event.status != "FIC":
            return Response(
                {"error": "Event is not under FIC review."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        event.status = "COUNSELLOR"
        event.save()

        return Response(
            {"message": "Event status changed to 'Counsellor Review'."},
            status=status.HTTP_200_OK,
        )


class CounsellorApproveEventAPIView(APIView):
    def put(self, request):
        event_id = request.data.get("id")
        event = get_object_or_404(Event_info, id=event_id)
        if event.status != "COUNSELLOR":
            return Response(
                {"error": "Event is not under Counsellor review."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        event.status = "DEAN"
        event.save()

        return Response(
            {"message": "Event status changed to 'Dean Review'."},
            status=status.HTTP_200_OK,
        )


class DeanApproveEventAPIView(APIView):
    def put(self, request):
        event_id = request.data.get("id")
        event = get_object_or_404(Event_info, id=event_id)
        if event.status != "DEAN":
            return Response(
                {"error": "Event is not under Dean review."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        event.status = "ACCEPT"
        event.save()

        return Response(
            {"message": "Event status changed to 'Accepted'."},
            status=status.HTTP_200_OK,
        )


class NewBudgetAPIView(APIView):
    def put(self, request):
        request.data["status"] = "FIC"
        serializer = BudgetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FICApproveBudgetAPIView(APIView):
    def put(self, request):
        budget_id = request.data.get("id")
        budget = get_object_or_404(Budget, id=budget_id)
        if budget.status != "FIC":
            return Response(
                {"error": "Budget is not under FIC review."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        budget.status = "COUNSELLOR"
        budget.save()
        return Response(
            {"message": "Budget status changed to 'Counsellor Review'."},
            status=status.HTTP_200_OK,
        )


class CounsellorApproveBudgetAPIView(APIView):
    def put(self, request):
        budget_id = request.data.get("id")
        budget = get_object_or_404(Budget, id=budget_id)
        if budget.status != "COUNSELLOR":
            return Response(
                {"error": "Budget is not under Counsellor review."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        budget.status = "DEAN"
        budget.save()
        return Response(
            {"message": "Budget status changed to 'Dean Review'."},
            status=status.HTTP_200_OK,
        )


class DeanApproveBudgetAPIView(APIView):
    def put(self, request):
        budget_id = request.data.get("id")
        budget = get_object_or_404(Budget, id=budget_id)
        if budget.status != "DEAN":
            return Response(
                {"error": "Budget is not under Dean review."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        budget.status = "ACCEPT"
        budget.save()
        return Response(
            {"message": "Budget status changed to 'Accepted'."},
            status=status.HTTP_200_OK,
        )


class RejectBudgetAPIView(APIView):
    def put(self, request):
        budget_id = request.data.get("id")
        budget = get_object_or_404(Budget, id=budget_id)
        budget.status = "REJECT"
        budget.save()
        return Response(
            {"message": "Budget status changed to 'Rejected'."},
            status=status.HTTP_200_OK,
        )


class RejectEventAPIView(APIView):
    def put(self, request):
        event_id = request.data.get("id")
        event = get_object_or_404(Event_info, id=event_id)
        event.status = "REJECT"
        event.save()
        return Response(
            {"message": "Event status changed to 'Rejected'."},
            status=status.HTTP_200_OK,
        )


class AchievementsAPIView(APIView):
    def post(self, request):
        club_name = request.data.get("club_name")
        achievements = Achievements.objects.filter(club_name=club_name)
        if not achievements.exists():
            return Response(
                {"message": "No achievements found for this club."}, status=404
            )

        serializer = AchievementsSerializer(achievements, many=True)
        return Response(serializer.data, status=200)


class AddAchievementAPIView(APIView):
    def post(self, request):
        serializer = AchievementsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateBudgetCommentAPIView(APIView):
    def post(self, request):
        data = request.data.copy()
        data["comment_date"] = timezone.now().date()
        data["comment_time"] = timezone.now().time()

        serializer = Budget_CommentsSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateEventCommentAPIView(APIView):
    def post(self, request):
        data = request.data.copy()
        data["comment_date"] = timezone.now().date()
        data["comment_time"] = timezone.now().time()

        serializer = Event_CommentsSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListBudgetCommentsAPIView(APIView):
    def post(self, request):
        budget_id = request.data.get("budget_id")
        if not budget_id:
            return Response(
                {"error": "Budget ID is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        comments = Budget_Comments.objects.filter(budget_id=budget_id).order_by(
            "comment_date", "comment_time"
        )
        serializer = Budget_CommentsSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ListEventCommentsAPIView(APIView):
    def post(self, request):
        event_id = request.data.get("event_id")
        if not event_id:
            return Response(
                {"error": "Event ID is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        comments = Event_Comments.objects.filter(event_id=event_id).order_by(
            "comment_date", "comment_time"
        )
        serializer = Event_CommentsSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RejectEventAPIView(APIView):
    def put(self, request):
        event_id = request.data.get("id")
        event = get_object_or_404(Event_info, id=event_id)
        event.status = "REJECT"
        event.save()
        return Response(
            {"message": "Event status changed to 'Rejected'."},
            status=status.HTTP_200_OK,
        )


class ModifyEventAPIView(APIView):
    def put(self, request):
        event_id = request.data.get("id")
        event = get_object_or_404(Event_info, id=event_id)
        event.status = "COORDINATOR"
        event.save()
        return Response(
            {"message": "Event status changed to 'Coordinator review'."},
            status=status.HTTP_200_OK,
        )


class ModifyBudgetAPIView(APIView):
    def put(self, request):
        budget_id = request.data.get("id")
        budget = get_object_or_404(Budget, id=budget_id)
        budget.status = "COORDINATOR"
        budget.save()
        return Response(
            {"message": "Budget status changed to 'Coordinator Review'."},
            status=status.HTTP_200_OK,
        )


class RejectMemberAPIView(APIView):
    def put(self, request):
        member_id = request.data.get("id")
        member = get_object_or_404(Club_member, id=member_id)
        member.status = "rejected"
        member.save()
        return Response(
            {"message": "Member status changed to 'rejected'."},
            status=status.HTTP_200_OK,
        )


class AddClubPositionAPIView(APIView):
    def post(self, request):
        serializer = ClubPositionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListClubPositionAPIView(APIView):
    def post(self, request):
        name = request.data.get("name")
        positions = ClubPosition.objects.filter(name=name)
        serializer = ClubPositionSerializer(positions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdateEventAPIView(APIView):
    def put(self, request):
        try:
            # Fetch the event to be updated
            pk = request.data.get("id")
            event = Event_info.objects.get(pk=pk)
        except Event_info.DoesNotExist:
            return Response(
                {"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Partial update for 'details' and 'event_poster'
        data = {}
        if "details" in request.data:
            data["details"] = request.data["details"]
        if "event_poster" in request.FILES:
            data["event_poster"] = request.FILES["event_poster"]
        data["status"] = "FIC"

        # Create serializer instance with partial=True to allow partial updates
        serializer = event_infoserializer(event, data=data, partial=True)

        # Validate and update
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateBudgetAPIView(APIView):
    def put(self, request):
        try:
            # Fetch the event to be updated
            pk = request.data.get("id")
            budget = Budget.objects.get(pk=pk)
        except Budget.DoesNotExist:
            return Response(
                {"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Partial update for 'details' and 'event_poster'
        data = {}
        if "budget_amt" in request.data:
            data["budget_amt"] = request.data["budget_amt"]
        if "remarks" in request.data:
            data["remarks"] = request.data["remarks"]
        if "budget_file" in request.FILES:
            data["budget_file"] = request.FILES["budget_file"]
        data["status"] = "FIC"

        # Create serializer instance with partial=True to allow partial updates
        serializer = BudgetSerializer(budget, data=data, partial=True)

        # Validate and update
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FreeMembersForClubAPIView(APIView):
    def get(self, request):
        club_id = request.data.get('club_id')  # Use query_params for GET request
        if not club_id:
            return Response({"error": "Club id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get upcoming events for the club
            events = Event_info.objects.filter(club_id=club_id, start_date__gte =timezone.now().date())

            # Map incharge members to their events
            incharge_map = {}
            for event in events:
                if event.incharge:  # Ensure incharge is not None
                    incharge_map[str(event.incharge)] = event.event_name

            # Get all club members
            members = Club_member.objects.filter(club_id=club_id)

            # Prepare the response data
            response_data = []
            for memb in members:
                roll_no = str(memb.member_id)  # Ensure same type as incharge_map keys
                response_data.append({
                    "roll_no": roll_no,
                    "event_name": incharge_map.get(roll_no, None)  # Set event_name or None
                })

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CoordinatorEventsAPIView(APIView):
    """
    API View to fetch events for clubs where the given person (by roll number) is a coordinator.
    Filters by accepted events and those in the current month.
    """

    def post(self, request):
        # Extract roll number from the request data
        roll_number = request.data.get("roll_number")
        if not roll_number:
            return Response(
                {"error": "Roll number is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            clubs = Club_info.objects.filter(co_ordinator=roll_number)
            # Get the current month and year
            current_month = datetime.datetime.now().month
            current_year = datetime.datetime.now().year

            # Fetch events associated with those clubs, with status 'accepted' and within the same month
            events = Event_info.objects.filter(
                club__in=clubs,
                # status="Accepted",  # Replace with your actual status choice
                # start_date__year=current_year,
                # start_date__month=current_month,
            )

            # Serialize and return the events
            serializer = event_infoserializer(events, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Student.DoesNotExist:
            return Response(
                {"error": "Student not found with the given roll number."},
                status=status.HTTP_404_NOT_FOUND,
            )

class EventInputAPIView(APIView):
    def get(self, request):
        """
        Returns a list of all Event_info objects (dropdown options).
        """
        events = Event_info.objects.all()
        events_data = [{"id": event.id, "name": event.event_name} for event in events]  # Adjust fields as needed
        return Response(events_data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Creates a new EventInput instance.
        """
        # print(request.data["event"])
        # request.data["images"]=None
        print(request.data)
        serializer = EventInputSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#helper
def add_page_decorations(canvas, doc):
    canvas.saveState()
    page_num = canvas.getPageNumber()
    canvas.setFont('Helvetica', 10)
    canvas.drawCentredString(letter[0] / 2.0, 20, f"Page {page_num}")
    canvas.restoreState()

class NewsletterPDFAPIView(APIView):
    def get(self, request):
        # Determine timeframe filter based on query parameter
        timeframe = request.GET.get('timeframe', '').lower()
        now = timezone.now()
        if timeframe == 'weekly':
            time_threshold = now - timedelta(weeks=1)
        elif timeframe == 'monthly':
            time_threshold = now - timedelta(days=30)
        elif timeframe == '6 months':
            time_threshold = now - timedelta(days=182)  # Approximation for half a year
        else:
            time_threshold = None
        print(time_threshold)
        # Fetch all unique clubs
        clubs = Event_info.objects.values_list('club', flat=True).distinct()
        has_events = False
        for club in clubs:
            club_events = EventInput.objects.filter(event__club=club)
            if time_threshold:
                club_events = club_events.filter(event__end_date__range=(time_threshold, now))
            if club_events.exists():
                has_events = True
                break

        if not has_events:
            return Response({"message": "No events found for the selected timeframe."}, status=status.HTTP_404_NOT_FOUND)

        # Create an in-memory file
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)

        # Get the default style sheet and create custom styles
        styles = getSampleStyleSheet()
        story = []

        # --- Banner Section ---
        banner_path = "path/to/your/banner.jpg"  # Update this path to your banner image
        try:
            banner = Image(banner_path, width=letter[0], height=150)
            story.append(banner)
        except Exception:
            pass

        story.append(Spacer(1, 20))

        # Catchy Title and Tagline
        title_style = ParagraphStyle(
            name='TitleStyle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=26,
            leading=30,
            alignment=1,
            textColor=colors.darkblue
        )
        tagline_style = ParagraphStyle(
            name='Tagline',
            parent=styles['BodyText'],
            fontName='Helvetica-Oblique',
            fontSize=14,
            leading=18,
            alignment=1,
            textColor=colors.darkgray
        )

        story.append(Paragraph("IIITDM Jabalpur Gymkhana Newsletter", title_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph("Stay tuned for the latest happenings and exclusive updates!", tagline_style))
        story.append(Spacer(1, 30))

        # Introductory paragraph
        intro_style = ParagraphStyle(
            name='Intro',
            parent=styles['BodyText'],
            fontSize=12,
            leading=16,
            alignment=1,
            textColor=colors.black
        )
        intro_text = (
            "Welcome to our monthly newsletter where we bring you the most exciting events from various clubs. "
            "Dive into details, get inspired, and mark your calendars for a memorable experience!"
        )
        story.append(Paragraph(intro_text, intro_style))
        story.append(Spacer(1, 40))

        # --- Newsletter Content ---
        club_header_style = ParagraphStyle(
            name='ClubHeader',
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.darkred,
            backColor=colors.whitesmoke,
            spaceAfter=10,
            borderPadding=(5, 5, 5, 5)
        )

        event_heading_style = ParagraphStyle(
            name='EventHeading',
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            textColor=colors.darkgreen
        )

        body_text_style = ParagraphStyle(
            name='BodyText',
            parent=styles['BodyText'],
            fontSize=12,
            leading=15,
            textColor=colors.black
        )

        italic_style = ParagraphStyle(
            name='Italic',
            parent=styles['BodyText'],
            fontName='Helvetica-Oblique',
            fontSize=12,
            leading=15,
            textColor=colors.gray
        )

        for club in clubs:
            story.append(Paragraph(f"Club: {club}", club_header_style))
            story.append(Spacer(1, 20))

            club_events = EventInput.objects.filter(event__club=club)
            if time_threshold:
                club_events = club_events.filter(event__end_date__range=(time_threshold, now))

            for event in club_events:
                event_info = event.event

                story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
                story.append(Spacer(1, 10))
                story.append(Paragraph("Event Details", event_heading_style))
                story.append(Spacer(1, 10))

                story.append(Paragraph(f"<b>Event:</b> {event_info.event_name}", body_text_style))
                story.append(Spacer(1, 10))

                story.append(Paragraph(
                    f"<b>Start Date:</b> {event_info.start_date.strftime('%B %d, %Y')}",
                    body_text_style))
                story.append(Spacer(1, 10))

                story.append(Paragraph(
                    f"<b>Start Time:</b> {event_info.start_time.strftime('%I:%M %p')}",
                    body_text_style))
                story.append(Spacer(1, 10))

                story.append(Paragraph(
                    f"<b>Venue:</b> {event_info.venue}",
                    body_text_style))
                story.append(Spacer(1, 10))

                story.append(Paragraph("<b>Description:</b>", event_heading_style))
                story.append(Paragraph(f"{event.description}", body_text_style))
                story.append(Spacer(1, 10))

                if event.images:
                    image_path = event.images.path
                    try:
                        story.append(Image(image_path, width=200, height=150))
                    except Exception:
                        story.append(Paragraph("[Image could not be loaded]", body_text_style))
                else:
                    story.append(Paragraph("[Image Placeholder]", body_text_style))

                story.append(Spacer(1, 10))
                story.append(Paragraph(
                    "Additional Information: Stay tuned for more updates and behind-the-scenes insights!",
                    italic_style))
                story.append(Spacer(1, 30))

            story.append(PageBreak())

        doc.build(story, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)
        buffer.seek(0)

        return FileResponse(buffer, as_attachment=True, filename="newsletter.pdf")