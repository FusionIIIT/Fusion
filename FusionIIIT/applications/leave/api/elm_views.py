from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from applications.leave.elm_services import respond_to_task, submit_leave
from applications.leave.models import ELMAccountTransaction, ELMWorkflowTask, Leave, LeavesCount
from .elm_serializers import ELMApplicationSerializer, ELMTaskDecisionSerializer


def _error(exc):
    return Response({'detail': ' '.join(getattr(exc, 'messages', [str(exc)]))},
                    status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def elm_applications_api(request):
    if request.method == 'GET':
        applications = Leave.objects.filter(applicant=request.user).exclude(elm_state='') \
            .prefetch_related('segments').order_by('-timestamp')
        return Response([{
            'id': leave.pk, 'state': leave.elm_state, 'status': leave.status,
            'purpose': leave.purpose, 'station_leave': leave.station_leave,
            'station_details': leave.station_details,
            'segments': [{'category': segment.leave_type.name if segment.leave_type else None,
                          'start_date': segment.start_date, 'end_date': segment.end_date,
                          'start_half': segment.start_half, 'end_half': segment.end_half}
                         for segment in leave.segments.all()],
        } for leave in applications])
    serializer = ELMApplicationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    data = serializer.validated_data
    try:
        leave = submit_leave(request.user, data['category'], data['start_date'],
            data['end_date'], data['purpose'], data.get('start_half', False),
            data.get('end_half', False), data.get('substitute'),
            data.get('station_leave', False), data.get('station_details', ''),
            data.get('medical_evidence'))
    except (DjangoValidationError, ValueError) as exc:
        return _error(exc)
    return Response({'id': leave.pk, 'state': leave.elm_state}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes([TokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def elm_task_response_api(request, task_id):
    task = ELMWorkflowTask.objects.filter(pk=task_id, assignee=request.user,
                                         status='pending').first()
    if not task:
        return Response({'detail': 'No actionable task was found.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = ELMTaskDecisionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        leave = respond_to_task(task, request.user, serializer.validated_data['decision'],
                                serializer.validated_data.get('remark', ''))
    except (DjangoValidationError, ValueError) as exc:
        return _error(exc)
    return Response({'leave_id': leave.pk, 'state': leave.elm_state})


@api_view(['GET'])
@authentication_classes([TokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def elm_account_api(request):
    year = request.query_params.get('year')
    balances = LeavesCount.objects.filter(user=request.user)
    transactions = ELMAccountTransaction.objects.filter(user=request.user)
    if year:
        try:
            year = int(year)
        except (TypeError, ValueError):
            return Response({'year': 'Provide a numeric year.'}, status=status.HTTP_400_BAD_REQUEST)
        balances = balances.filter(year=year)
        transactions = transactions.filter(year=year)
    return Response({
        'balances': [{'category': item.leave_type.name, 'year': item.year,
                      'remaining': item.remaining_leaves} for item in balances.select_related('leave_type')],
        'transactions': [{'category': item.get_category_display(), 'year': item.year,
                          'amount': item.amount, 'reason': item.reason,
                          'reference': item.reference, 'created_at': item.created_at}
                         for item in transactions.order_by('-created_at')],
    })
