from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from applications.scholarships.models import Previous_winner, Award_and_scholarship,Mcm,Director_gold,Notional_prize,Director_silver,Proficiency_dm,Release
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import DirectorSilverDecisionSerializer, DMProficiencyDecisionSerializer
from rest_framework import status
from applications.academic_information.models import Spi, Student
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation)
from rest_framework import viewsets
from applications.scholarships.api.serializers import PreviousWinnerSerializer,AwardAndScholarshipSerializer,McmSerializer,NotionalPrizeSerializer,DirectorGoldSerializer,DirectorSilverSerializer,ProficiencyDmSerializer,ReleaseSerializer,McmStatusUpdateSerializer
from django.shortcuts import get_object_or_404
import datetime

#This api is for invite application 
class ReleaseCreateView(APIView):
    def post(self, request):
        serializer = ReleaseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # Save the data to the database
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CheckApplicationWindowView(APIView):
    def post(self, request):
        award_name = request.data.get('award')
        current_date = datetime.date.today()

        if not award_name:
            return Response({'result': 'Failure', 'error': 'Award is a required field'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            #Get all the rows with the award name
            releases = Release.objects.filter(award=award_name)
        except Release.DoesNotExist:
            return Response({'result': 'Failure', 'error': 'No release found for the specified award'}, status=status.HTTP_404_NOT_FOUND)
        for release in releases:
            # Check if the current date is within the start and end dates of the release
            if release.startdate <= current_date <= release.enddate:
                return Response({'result': 'Success', 'message': 'Application window is open.'}, status=status.HTTP_200_OK)
            
        # If the current date is outside the start and end dates
        return Response({'result': 'Failure', 'error': 'Application window is closed.'}, status=status.HTTP_400_BAD_REQUEST)

#This API is for editing the catalogue by convenor and assistant and saving in the database
class AwardAndScholarshipCreateView(APIView):
    def post(self, request, pk=None):
        # Check if pk is provided, if yes, try to update the existing entry
        pk=request.data.get("id")
        if pk is not None:
            award = get_object_or_404(Award_and_scholarship, pk=pk)
            # Update the existing entry
            serializer = AwardAndScholarshipSerializer(award, data=request.data, partial=True)
        else:
            # If pk is not provided, create a new entry
            serializer = AwardAndScholarshipSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)  # 201 Created response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # 400 Bad Request if data is invalid

#This api for fetching the award and scholarship catalogue from the database
class create_award(APIView):

    def get(self, request, *args, **kwargs):
        awards = Award_and_scholarship.objects.all()  # Fetch all awards
        serializer = AwardAndScholarshipSerializer(awards, many=True)  # Serialize the awards
        return Response(serializer.data, status=status.HTTP_200_OK)  

#This api is for Previous Winner 
class GetWinnersView(APIView):

    def post(self, request, *args, **kwargs):
        award_id = request.data.get('award_id')
        batch_year = int(request.data.get('batch'))
        programme_name = request.data.get('programme')

        try:
            award = Award_and_scholarship.objects.get(id=award_id)
        except Award_and_scholarship.DoesNotExist:
            return Response({'result': 'Failure', 'error': 'Award not found'}, status=status.HTTP_404_NOT_FOUND)

        winners = Previous_winner.objects.select_related('student', 'award_id').filter(
            year=batch_year, award_id=award, programme=programme_name
        )
        
        context = {
            'student_name': [],
            'student_program': [],
            'roll': []
        }

        if winners.exists():
            for winner in winners:
                extra_info = ExtraInfo.objects.get(id=winner.student_id)
                student_id = Student.objects.get(id=extra_info)
                student_name = extra_info.user.first_name
                student_roll = winner.student_id
                student_program = student_id.programme

                context['student_name'].append(student_name)
                context['roll'].append(student_roll)
                context['student_program'].append(student_program)
                print(student_roll)

            context['result'] = 'Success'
            return Response(context, status=status.HTTP_200_OK)

        else:
            return Response({'result': 'Failure', 'error': 'No winners found'}, status=status.HTTP_404_NOT_FOUND)

class McmUpdateView(APIView):
    def post(self, request):
        print(request.data)
        request.data['student']=request.user.username
        serializer = McmSerializer(data=request.data)
        if serializer.is_valid():
            mcm_instance = serializer.save()
            return Response(McmSerializer(mcm_instance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class McmRetrieveView(APIView):
    def post(self, request):
        roll_number = request.user.username
        
        if not roll_number:
            return Response({"detail": "Roll number is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        mcm_data = Mcm.objects.filter(student=roll_number)
        
        if not mcm_data.exists():
            return Response({"detail": "No Mcm data found for this roll number."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = McmSerializer(mcm_data, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

class DirectorSilverRetrieveView(APIView):
    def post(self, request):
        roll_number = request.user.username
        
        if not roll_number:
            return Response({"detail": "Roll number is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        director_silver_data = Director_silver.objects.filter(student=roll_number)
        
        if not director_silver_data.exists():
            return Response({"detail": "No Director Silver data found for this roll number."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = DirectorSilverSerializer(director_silver_data, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

class DirectorSilverUpdateView(APIView):
    def post(self, request):
        request.data['student']=request.user.username
        request.data['date']= datetime.date.today()
        serializer = DirectorSilverSerializer(data=request.data)
        if serializer.is_valid():
            director_silver_instance = serializer.save()
            return Response(DirectorSilverSerializer(director_silver_instance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class DirectorGoldRetrieveView(APIView):
    def post(self, request):
        roll_number = request.user.username
        
        if not roll_number:
            return Response({"detail": "Roll number is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        director_gold_data = Director_gold.objects.filter(student=roll_number)
        
        if not director_gold_data.exists():
            return Response({"detail": "No Director Gold data found for this roll number."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = DirectorGoldSerializer(director_gold_data, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

class DirectorGoldUpdateView(APIView):
    def post(self, request):
        request.data['student']=request.user.username
        serializer = DirectorGoldSerializer(data=request.data)
        if serializer.is_valid():
            director_gold_instance = serializer.save()
            return Response(DirectorGoldSerializer(director_gold_instance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProficiencyDmUpdateView(APIView):
    def post(self, request):
        request.data['student']=request.user.username
        print(request.data)
        serializer = ProficiencyDmSerializer(data=request.data)
        if serializer.is_valid():
            proficiency_dm_instance = serializer.save()
            return Response(ProficiencyDmSerializer(proficiency_dm_instance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProficiencyDmRetrieveView(APIView):
    def post(self, request):
        roll_number = request.user.username
        
        if not roll_number:
            return Response({"detail": "Roll number is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        proficiency_dm_data = Proficiency_dm.objects.filter(student=roll_number)
        
        if not proficiency_dm_data.exists():
            return Response({"detail": "No Proficiency DM data found for this roll number."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProficiencyDmSerializer(proficiency_dm_data, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

#This api for showing the list of student who has applied for mcm scholarship to convenor assistant 
class ScholarshipDetailView(APIView):
    def get(self, request):
        # Fetch all records from the Mcm table
        mcm_data = Mcm.objects.all()
        # Serialize the data
        serializer = McmSerializer(mcm_data, many=True)
        # Return the serialized data as a response
        return Response(serializer.data, status=status.HTTP_200_OK)

class DirectorGoldListView(APIView):
    def get(self, request):
        # Fetch all entries
        director_gold_entries = Director_gold.objects.all()  
        # Serialize all entries
        serializer = DirectorGoldSerializer(director_gold_entries, many=True)  
        # Return the serialized data as a response
        return Response(serializer.data, status=status.HTTP_200_OK)

class DMProficiencyListView(APIView):
    def get(self, request):
        # Fetch all entries
        proficiency_dm_entries = Proficiency_dm.objects.all()
        # Serialize all entries
        serializer = ProficiencyDmSerializer(proficiency_dm_entries, many=True)
        # Return the serialized data as a response
        return Response(serializer.data, status=status.HTTP_200_OK)

#This api is for showing the all the documnet to the convenor or assistant submitted by the student in browse application 
class StudentDetailView(APIView):
    def post(self, request):
        student_id = request.data.get('student_id')
        if not student_id:
            return Response({"error": "Student ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            mcm_entry = Mcm.objects.get(student_id=student_id)
        except Mcm.DoesNotExist:
            return Response({"error": "No record found for the given student ID."}, status=status.HTTP_404_NOT_FOUND)

        serializer = McmSerializer(mcm_entry)
        return Response(serializer.data, status=status.HTTP_200_OK)

#This api is for showing the list of student who has applied for director silver in browse application in convenor and assistant
class DirectorSilverDetailView(APIView):
    def post(self, request):
        student_id = request.data.get('student_id')
        
        if not student_id:
            return Response({"error": "Student ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            director_silver_entry = Director_silver.objects.get(student__id=student_id)
        except Director_silver.DoesNotExist:
            return Response({"error": "No record found for the given student ID."}, status=status.HTTP_404_NOT_FOUND)

        serializer = DirectorSilverSerializer(director_silver_entry)
        return Response(serializer.data, status=status.HTTP_200_OK)

#This api is for showing the list of student who has applied for director gold in browse application in convenor and assistant
class DirectorGoldDetailView(APIView):
    def post(self, request):
        student_id = request.data.get('student_id')

        if not student_id:
            return Response({"error": "Student ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            director_gold_entry = Director_gold.objects.get(student__id=student_id)
        except Director_gold.DoesNotExist:
            return Response({"error": "No record found for the given student ID."}, status=status.HTTP_404_NOT_FOUND)

        serializer = DirectorGoldSerializer(director_gold_entry)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetReleaseByAwardView(APIView):
    def post(self, request, *args, **kwargs):
        # Get the award name from the request
        award_name = request.data.get('award')

        # Check if the award variable is provided
        if not award_name:
            return Response(
                {'result': 'Failure', 'error': 'Award is a required field'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch records from the Release table where the award matches
        releases = Release.objects.filter(award=award_name)

        # Check if any records were found
        if releases.exists():
            # Build the response data
            data = []
            for release in releases:
                data.append({
                    'id': release.id,
                    'date_time': release.date_time,
                    'programme': release.programme,
                    'startdate': release.startdate,
                    'enddate': release.enddate,
                    'award': release.award,
                    'remarks': release.remarks,
                    'batch': release.batch,
                    'notif_visible': release.notif_visible,
                })

            return Response({'result': 'Success', 'data': data}, status=status.HTTP_200_OK)

        # If no records found
        return Response(
            {'result': 'Failure', 'error': 'No releases found for the specified award'},
            status=status.HTTP_404_NOT_FOUND
        )

#This api for MCM status that is accept, reject and under review
class McmStatusUpdateView(APIView):
    def post(self, request):
        # Fetch the Mcm instance based on the provided primary key (pk)
        mcm_instance = get_object_or_404(Mcm,id=request.data.get('id'))
        
        # Deserialize the input data with the existing object
        serializer = McmStatusUpdateSerializer(mcm_instance, data=request.data, partial=True)
        
        # Validate the data
        if serializer.is_valid():
            # Save the updated status
            serializer.save()
            return Response({"message": "Status updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        
        # Return validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#This api for Director silver accepting and rejecting the application by convenor and assistant
class DirectorSilverDecisionView(APIView):
    def post(self, request):
        # Deserialize the request data
        serializer = DirectorSilverDecisionSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Retrieve the Director_silver instance using the provided id
                director_silver = Director_silver.objects.get(id=request.data['id'])
                
                # Update the status field
                director_silver.status = serializer.validated_data['status']
                director_silver.save()

                return Response({"message": f"Application has been {director_silver.status.lower()}."},
                                status=status.HTTP_200_OK)

            except Director_silver.DoesNotExist:
                return Response({"error": "Director_silver entry not found."},
                                status=status.HTTP_404_NOT_FOUND)
        
        # If the data is invalid
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DMProficiencyDecisionView(APIView):
    def post(self, request):
        # Deserialize the request data
        serializer = DMProficiencyDecisionSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Retrieve the Proficiency_dm instance using the provided id
                proficiency_dm = Proficiency_dm.objects.get(id=request.data['id'])
                
                # Update the status field
                proficiency_dm.status = serializer.validated_data['status']
                proficiency_dm.save()

                return Response({"message": f"Application has been {proficiency_dm.status.lower()}."},
                                status=status.HTTP_200_OK)

            except Proficiency_dm.DoesNotExist:
                return Response({"error": "Proficiency_dm entry not found."},
                                status=status.HTTP_404_NOT_FOUND)
        
        # If the data is invalid
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

##This api for Director gold accepting and rejecting the application by convenor and assistant
class DirectorGoldAcceptRejectView(APIView):
    def post(self, request):
        # Get the ID of the Director_gold entry to update
        director_gold_id = request.data.get('id')
        action = request.data.get('action')  # 'accept' or 'reject'
        
        # Check if the action is valid
        if action not in ['accept', 'reject']:
            return Response({'error': 'Invalid action. Please choose either "accept" or "reject".'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the Director_gold entry from the database using the ID
            director_gold = Director_gold.objects.get(id=director_gold_id)
        except Director_gold.DoesNotExist:
            return Response({'error': 'Director_gold entry not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Update the status based on the action
        if action == 'accept':
            director_gold.status = 'ACCEPTED'
        else:
            director_gold.status = 'REJECTED'

        # Save the updated Director_gold entry
        director_gold.save()

        # Return the updated entry as a response
        serializer = DirectorGoldSerializer(director_gold)
        return Response(serializer.data, status=status.HTTP_200_OK)

#API View to list all entries of the Director_silver model.
class DirectorSilverListView(APIView):
    """
    API View to list all entries of the Director_silver model.
    """
    def get(self, request):
        director_silver_entries = Director_silver.objects.all()
        serializer = DirectorSilverSerializer(director_silver_entries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class McmDocumentsRetrieveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        roll_number = request.data.get("roll")  # Roll number from request body

        if not roll_number:
            return Response({"detail": "Roll number is required."}, status=status.HTTP_400_BAD_REQUEST)

        mcm_instance = get_object_or_404(Mcm, student__id=roll_number)

        documents = {
            "income_certificate": bytes(mcm_instance.income_certificate).decode('utf-8') if mcm_instance.income_certificate else None,
            "marksheet": bytes(mcm_instance.Marksheet).decode('utf-8') if mcm_instance.Marksheet else None,
            "bank_details": bytes(mcm_instance.Bank_details).decode('utf-8') if mcm_instance.Bank_details else None,
            "affidavit": bytes(mcm_instance.Affidavit).decode('utf-8') if mcm_instance.Affidavit else None,
            "aadhar_card": bytes(mcm_instance.Aadhar_card).decode('utf-8') if mcm_instance.Aadhar_card else None,
            "fee_receipt": bytes(mcm_instance.Fee_Receipt).decode('utf-8') if mcm_instance.Fee_Receipt else None,
        }

        return Response(documents, status=status.HTTP_200_OK)

class DirectorSilverMarksheetView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        roll_number = request.data.get('roll')  # Get roll number from POST request body
        
        if not roll_number:
            return Response({"error": "Roll number is required"}, status=400)
        
        director_silver_entry = get_object_or_404(Director_silver, student_id=roll_number)

        marksheet_data = director_silver_entry.Marksheet  
        if marksheet_data:
            marksheet_str = bytes(marksheet_data).decode('utf-8')  # Convert memoryview to bytes first, then decode
        else:
            marksheet_str = None

        return Response({
            "marksheet": marksheet_str,
        })

class DirectorGoldMarksheetView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        roll_number = request.data.get("roll")  # Get roll number from POST request body

        if not roll_number:
            return Response({"error": "Roll number is required"}, status=400)

        record = get_object_or_404(Director_gold, student_id=roll_number)

        marksheet_data = record.Marksheet  
        if marksheet_data:
            marksheet_str = bytes(marksheet_data).decode('utf-8')  # Convert memoryview to bytes first, then decode
        else:
            marksheet_str = None

        return Response({
            "marksheet": marksheet_str,
        }, status=200)
