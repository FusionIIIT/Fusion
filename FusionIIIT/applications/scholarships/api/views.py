from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from applications.scholarships.models import Previous_winner, Award_and_scholarship,Mcm,Director_gold,Notional_prize,Director_silver,Proficiency_dm
from applications.academic_information.models import Spi, Student
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation)
from rest_framework import viewsets
from applications.scholarships.api.serializers import PreviousWinnerSerializer,AwardAndScholarshipSerializer,McmSerializer,NotionalPrizeSerializer,DirectorGoldSerializer,DirectorSilverSerializer,ProficiencyDmSerializer




class AwardAndScholarshipCreateView(APIView): 
    def post(self, request):
        
        serializer = AwardAndScholarshipSerializer(data=request.data)

        if serializer.is_valid():
            # Save the new entry to the database
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)  # 201 Created response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # 400 Bad Request if data is invalid






class create_award(APIView):

    def get(self, request, *args, **kwargs):
        awards = Award_and_scholarship.objects.all()  # Fetch all awards
        serializer = AwardAndScholarshipSerializer(awards, many=True)  # Serialize the awards
        return Response(serializer.data, status=status.HTTP_200_OK)  



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
        serializer = McmSerializer(data=request.data)
        if serializer.is_valid():
            mcm_instance = serializer.save()
            return Response(McmSerializer(mcm_instance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class McmRetrieveView(APIView):
    def post(self, request):
        roll_number = request.data.get('roll_number')
        
        if not roll_number:
            return Response({"detail": "Roll number is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        mcm_data = Mcm.objects.filter(student=roll_number)
        
        if not mcm_data.exists():
            return Response({"detail": "No Mcm data found for this roll number."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = McmSerializer(mcm_data, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
class DirectorSilverRetrieveView(APIView):
    def post(self, request):
        roll_number = request.data.get('roll_number')
        
        if not roll_number:
            return Response({"detail": "Roll number is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        director_silver_data = Director_silver.objects.filter(student=roll_number)
        
        if not director_silver_data.exists():
            return Response({"detail": "No Director Silver data found for this roll number."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = DirectorSilverSerializer(director_silver_data, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
class DirectorSilverUpdateView(APIView):
    def post(self, request):
        serializer = DirectorSilverSerializer(data=request.data)
        if serializer.is_valid():
            director_silver_instance = serializer.save()
            return Response(DirectorSilverSerializer(director_silver_instance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class DirectorGoldRetrieveView(APIView):
    def post(self, request):
        roll_number = request.data.get('roll_number')
        
        if not roll_number:
            return Response({"detail": "Roll number is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        director_gold_data = Director_gold.objects.filter(student=roll_number)
        
        if not director_gold_data.exists():
            return Response({"detail": "No Director Gold data found for this roll number."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = DirectorGoldSerializer(director_gold_data, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
class DirectorGoldUpdateView(APIView):
    def post(self, request):
        serializer = DirectorGoldSerializer(data=request.data)
        if serializer.is_valid():
            director_gold_instance = serializer.save()
            return Response(DirectorGoldSerializer(director_gold_instance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class ProficiencyDmUpdateView(APIView):
    def post(self, request):
        serializer = ProficiencyDmSerializer(data=request.data)
        if serializer.is_valid():
            proficiency_dm_instance = serializer.save()
            return Response(ProficiencyDmSerializer(proficiency_dm_instance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class ProficiencyDmRetrieveView(APIView):
    def post(self, request):
        roll_number = request.data.get('roll_number')
        
        if not roll_number:
            return Response({"detail": "Roll number is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        proficiency_dm_data = Proficiency_dm.objects.filter(student=roll_number)
        
        if not proficiency_dm_data.exists():
            return Response({"detail": "No Proficiency DM data found for this roll number."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProficiencyDmSerializer(proficiency_dm_data, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

class ScholarshipDetailView(APIView):
    def get(self, request):
        # Fetch all records from the Mcm table
        mcm_data = Mcm.objects.all()
        # Serialize the data
        serializer = McmSerializer(mcm_data, many=True)
        # Return the serialized data as a response
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class StudentDetailView(APIView):
    def post(self, request):
        student_id = request.data.get('student')
        if not student_id:
            return Response({"error": "Student ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            mcm_entry = Mcm.objects.get(student__id=student_id)
        except Mcm.DoesNotExist:
            return Response({"error": "No record found for the given student ID."}, status=status.HTTP_404_NOT_FOUND)

        serializer = McmSerializer(mcm_entry)
        return Response(serializer.data, status=status.HTTP_200_OK)
