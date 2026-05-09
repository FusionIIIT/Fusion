from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.db.models import Q

from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.http import JsonResponse


from . import serializers
from applications.globals.models import ExtraInfo, Issue, IssueImage, Feedback
from .utils import get_and_authenticate_user
from notifications.models import Notification
from applications.globals.api.selectors import get_feedback_average_rating
from .services import (
    build_auth_payload,
    build_login_payload,
    build_student_profile_payload,
    delete_profile_component,
    parse_notification_id,
    update_profile_from_payload,
)
from PIL import Image

User = get_user_model()

MAX_ISSUE_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_ISSUE_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif"}


def _validate_issue_image(uploaded_file):
    if uploaded_file.size > MAX_ISSUE_IMAGE_SIZE_BYTES:
        return False, "Image exceeds 5 MB size limit"

    if uploaded_file.content_type not in ALLOWED_ISSUE_IMAGE_TYPES:
        return False, "Unsupported image type"

    try:
        Image.open(uploaded_file).verify()
        uploaded_file.seek(0)
    except (OSError, ValueError):
        return False, "Corrupted image file"

    return True, ""

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    payload = request.data.copy()
    if 'username' not in payload and 'email' in payload:
        payload['username'] = payload['email']

    serializer = serializers.UserLoginSerializer(data=payload)
    serializer.is_valid(raise_exception=True)
    try:
        user = get_and_authenticate_user(**serializer.validated_data)
    except ValidationError:
        return Response({'error': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)

    data = serializers.AuthUserSerializer(user).data
    resp = build_login_payload(user, data['auth_token'])
    return Response(data=resp, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def logout(request):
    auth_token = getattr(request.user, 'auth_token', None)
    if auth_token is not None:
        auth_token.delete()
    resp = {
        'message' : 'User logged out successfully'
    }
    return Response(data=resp, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def auth_view(request):
    resp = build_auth_payload(request.user)
    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def notification(request):
    notifications=serializers.NotificationSerializer(request.user.notifications.all(),many=True).data

    resp={
        'notifications':notifications, 
    }

    return Response(data=resp,status=status.HTTP_200_OK)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_last_selected_role(request):
    new_role = request.data.get('last_selected_role')

    if new_role is None:
        return Response({'error': 'last_selected_role is required'}, status=status.HTTP_400_BAD_REQUEST)

    extra_info = get_object_or_404(ExtraInfo, user=request.user)

    extra_info.last_selected_role = new_role
    extra_info.save()

    return Response({'message': 'last_selected_role updated successfully'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def profile(request, username=None):
    user = get_object_or_404(User, username=username) if username else request.user
    resp = build_student_profile_payload(user)
    if resp is None:
        return Response(data={'error': 'User is not a student'}, status=status.HTTP_400_BAD_REQUEST)  
    return Response(data=resp, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def profile_update(request):
    payload, response_status = update_profile_from_payload(request.user, request.data)
    return Response(payload, status=response_status)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def profile_delete(request, id):
    payload, response_status = delete_profile_component(request.data, id)
    return Response(payload, status=response_status)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def NotificationRead(request):
    try:
        notif_id = parse_notification_id(request.data)
    except (KeyError, TypeError, ValueError):
        return Response({'error': 'Invalid or missing notification id.'}, status=status.HTTP_400_BAD_REQUEST)

    notification = get_object_or_404(Notification, recipient=request.user, id=notif_id)
    notification.mark_as_read()
    response = {
        'message': 'notfication successfully marked as seen.'
    }
    return Response(response, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def NotificationUnread(request):
    try:
        notif_id = parse_notification_id(request.data)
    except (KeyError, TypeError, ValueError):
        return Response({'error': 'Invalid or missing notification id.'}, status=status.HTTP_400_BAD_REQUEST)

    notification = get_object_or_404(Notification, recipient=request.user, id=notif_id)
    if not notification.unread:
        notification.unread = True
        notification.save(update_fields=['unread'])

    response = {
        'message': 'Notification successfully marked as unread.'
    }
    return Response(response, status=status.HTTP_200_OK)
    
@api_view(['POST']) 
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def delete_notification(request):
    try:
        notif_id = parse_notification_id(request.data)
    except (KeyError, TypeError, ValueError):
        return Response({'error': 'Invalid or missing notification id.'}, status=status.HTTP_400_BAD_REQUEST)

    notification = get_object_or_404(Notification, recipient=request.user, id=notif_id)
    notification.deleted = True
    notification.save(update_fields=['deleted'])

    response = {
        'message': 'Notification marked as deleted.'
    }
    return Response(response, status=status.HTTP_200_OK)

from django.db import transaction, IntegrityError

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def admin_delete_course_proxy(request, course_id):
    """
    Proxy function to call the actual course delete function from programme_curriculum API
    """
    try:
        from applications.programme_curriculum.models import Course, CourseSlot, CourseInstructor
    except ImportError as import_error:
        return JsonResponse({
            'success': False,
            'message': 'Programme curriculum module is not available.',
            'error': str(import_error)
        }, status=500)

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Course not found.'
        }, status=404)

    course_name = course.name

    instructor_count = CourseInstructor.objects.filter(course_id=course).count()
    if instructor_count > 0:
        return JsonResponse({
            'success': False,
            'message': f'Cannot delete course. It has {instructor_count} active instructor assignment(s). Please remove instructor assignments first.'
        }, status=400)

    slot_count = CourseSlot.objects.filter(courses=course).count()
    if slot_count > 0:
        return JsonResponse({
            'success': False,
            'message': f'Cannot delete course. It is assigned to {slot_count} course slot(s) in curriculum(s). Please remove from course slots first.'
        }, status=400)

    try:
        with transaction.atomic():
            course.delete()
    except IntegrityError as delete_error:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting course: {str(delete_error)}'
        }, status=500)

    return JsonResponse({
        'success': True,
        'message': f'Course "{course_name}" has been successfully deleted.'
    }, status=200)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def db_issues(request):
    if request.method == 'GET':
        issues = Issue.objects.with_user_department().order_by('-added_on')
        payload = serializers.IssueListSerializer(issues, many=True, context={'request': request}).data
        return Response({'issues': payload}, status=status.HTTP_200_OK)

    serializer = serializers.IssueCreateUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    issue = serializer.save(user=request.user)
    image_errors = []
    for image in request.FILES.getlist('images'):
        valid, reason = _validate_issue_image(image)
        if not valid:
            image_errors.append(reason)
            continue
        issue_image = IssueImage.objects.create(image=image, user=request.user)
        issue.images.add(issue_image)

    response_payload = serializers.IssueListSerializer(issue, context={'request': request}).data
    return Response({'issue': response_payload, 'image_errors': image_errors}, status=status.HTTP_201_CREATED)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def db_issue_update(request, issue_id):
    issue = get_object_or_404(Issue, id=issue_id)

    if issue.user_id != request.user.id:
        return Response({'error': 'Only the issue owner can edit this issue.'}, status=status.HTTP_403_FORBIDDEN)

    if issue.closed:
        return Response({'error': 'Closed issues are read-only and cannot be edited.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = serializers.IssueCreateUpdateSerializer(issue, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    issue = serializer.save()

    remove = request.data.get('remove_images')
    if str(remove).lower() in ['true', '1', 'yes']:
        for img in issue.images.all():
            img.delete()

    image_errors = []
    for image in request.FILES.getlist('images'):
        valid, reason = _validate_issue_image(image)
        if not valid:
            image_errors.append(reason)
            continue
        issue_image = IssueImage.objects.create(image=image, user=request.user)
        issue.images.add(issue_image)

    response_payload = serializers.IssueListSerializer(issue, context={'request': request}).data
    return Response({'issue': response_payload, 'image_errors': image_errors}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def db_issue_support_toggle(request, issue_id):
    issue = get_object_or_404(Issue, id=issue_id)

    if issue.user_id == request.user.id:
        return Response(
            {
                'error': 'Issue owner cannot support their own issue',
                'supported': False,
                'support_count': issue.support.count(),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if issue.support.filter(id=request.user.id).exists():
        issue.support.remove(request.user)
        supported = False
    else:
        issue.support.add(request.user)
        supported = True

    return Response({'supported': supported, 'support_count': issue.support.count()}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def db_feedback(request):
    if request.method == 'GET':
        feeds = Feedback.objects.select_related('user').all().order_by('-timestamp')
        my_feedback = feeds.filter(user=request.user).first()
        others = feeds.order_by('-rating', '-timestamp')[:5]
        return Response(
            {
                'my_feedback': serializers.FeedbackSerializer(my_feedback).data if my_feedback else None,
                'top_feedbacks': serializers.FeedbackSerializer(others, many=True).data,
                'average_rating': round(get_feedback_average_rating(), 1),
            },
            status=status.HTTP_200_OK,
        )

    serializer = serializers.FeedbackCreateUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    rating = serializer.validated_data.get('rating')
    if not (1 <= int(rating) <= 5):
        return Response({'error': 'Rating must be between 1 and 5'}, status=status.HTTP_400_BAD_REQUEST)

    feedback_obj, _ = Feedback.objects.update_or_create(
        user=request.user,
        defaults={
            'rating': rating,
            'feedback': serializer.validated_data.get('feedback', ''),
        },
    )

    return Response({'feedback': serializers.FeedbackSerializer(feedback_obj).data}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def db_user_search(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 3:
        return Response({'results': [], 'error': 'Search query must be at least 3 characters'}, status=status.HTTP_400_BAD_REQUEST)

    words = [w.strip() for w in query.split() if w.strip()]
    name_q = Q()
    for token in words:
        name_q &= (Q(first_name__icontains=token) | Q(last_name__icontains=token) | Q(username__icontains=token))

    users = User.objects.filter(name_q).values('id', 'username', 'first_name', 'last_name')[:15]
    return Response({'results': list(users)}, status=status.HTTP_200_OK)