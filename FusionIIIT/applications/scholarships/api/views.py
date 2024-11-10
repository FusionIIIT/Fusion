from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from applications.scholarships.models import Previous_winner, Award_and_scholarship,Director_gold,Director_silver
from applications.academic_information.models import Spi, Student
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation)
from rest_framework import viewsets
from applications.scholarships.api.serializers import PreviousWinnerSerializer,AwardAndScholarshipSerializer,DirectorGoldSerializer,DirectorSilverSerializer,ProficiencyDMSerializer,McmSerializer

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



class DirectorGoldUpdateView(APIView):
    def put(self, request):
        # Deserialize the data without specifying an instance, allowing for creation or update
        serializer = DirectorGoldSerializer(data=request.data)

        if serializer.is_valid():
            # Save the object; if the data contains an 'id', it will update the existing record
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class DirectorSilverUpdateView(APIView):
    def put(self, request):
        # Deserialize the data, which includes the ID for identifying the record to update
        serializer = DirectorSilverSerializer(data=request.data)

        if serializer.is_valid():
            # Save the object; if the data contains an 'id', it will update the existing record
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ProficiencyDMUpdateView(APIView):
    def put(self, request):
        # Deserialize the data, which includes the ID for identifying the record to update
        serializer = ProficiencyDMSerializer(data=request.data)

        if serializer.is_valid():
            # Save the object; if the data contains an 'id', it will update the existing record
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class McmUpdateView(APIView):
    def put(self, request):
        # Deserialize the data from the request
        serializer = McmSerializer(data=request.data)

        # Validate and save data if valid
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        # Return error details if validation fails
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)