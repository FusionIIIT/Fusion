from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from applications.scholarships.models import Previous_winner, Award_and_scholarship
from applications.academic_information.models import Spi, Student
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation)
from .serializers import PreviousWinnerSerializer

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
