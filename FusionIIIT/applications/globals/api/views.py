from django.contrib.auth import get_user_model
from django.core.cache import cache
from applications.academic_information.models import Student
from applications.eis.api.views import profile as eis_profile
from applications.globals.models import (HoldsDesignation,Designation)
from applications.gymkhana.api.views import coordinator_club
from applications.placement_cell.models import (Achievement, Course, Education,
                                                Experience, Has, Patent,
                                                Project, Publication, Skill,
                                                PlacementProfileAuditLog)
from django.shortcuts import get_object_or_404, redirect

from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


from . import serializers

from .utils import get_and_authenticate_user
from notifications.models import Notification
from notifications.signals import notify

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = serializers.UserLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_and_authenticate_user(**serializer.validated_data)
    data = serializers.AuthUserSerializer(user).data
    resp = {
        'success' : 'True',
        'message' : 'User logged in successfully',
        'token' : data['auth_token']
    }
    return Response(data=resp, status=status.HTTP_200_OK)

@api_view(['POST'])
def logout(request):
    request.user.auth_token.delete()
    resp = {
        'message' : 'User logged out successfully'
    }
    return Response(data=resp, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def dashboard(request):
    user=request.user

    name = request.user.first_name +"_"+ request.user.last_name

    designation_list = list(HoldsDesignation.objects.all().filter(working = request.user).values_list('designation'))
    designation_id = [designation for designations in designation_list for designation in designations]
    designation_info = []
    for id in designation_id :
        name_ = get_object_or_404(Designation, id = id)
        designation_info.append(str(name_.name))

    notifications=serializers.NotificationSerializer(request.user.notifications.all(),many=True).data
    club_details= coordinator_club(request)

    resp={
        'notifications':notifications,
        'desgination_info' :  designation_info,
        'designation_info' :  designation_info,
        'last_selected_role' : cache.get('last_selected_role_{}'.format(user.id)),
        'club_details' : club_details
    }

    return Response(data=resp,status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def update_role(request):
    selected_role = (request.data.get('last_selected_role') or '').strip()
    designation_ids = HoldsDesignation.objects.filter(
        working=request.user,
    ).values_list('designation_id', flat=True)
    allowed_roles = set(
        Designation.objects.filter(id__in=designation_ids).values_list('name', flat=True),
    )

    if selected_role not in allowed_roles:
        return Response(
            {'last_selected_role': ['Selected role is not assigned to this user.']},
            status=status.HTTP_400_BAD_REQUEST,
        )

    cache.set('last_selected_role_{}'.format(request.user.id), selected_role, None)
    return Response(
        {'last_selected_role': selected_role},
        status=status.HTTP_200_OK,
    )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def profile(request, username=None):
    user = get_object_or_404(User, username=username) if username else request.user
    if not hasattr(user, 'extrainfo'):
        return Response(
            {
                'user': serializers.UserSerializer(user).data,
                'profile': None,
                'current': serializers.HoldsDesignationSerializer(
                    user.current_designation.all(),
                    many=True,
                ).data,
            },
            status=status.HTTP_200_OK,
        )

    user_detail = serializers.UserSerializer(user).data
    profile = serializers.ExtraInfoSerializer(user.extrainfo).data
    base_response = {
        'user': user_detail,
        'profile': profile,
        'current': serializers.HoldsDesignationSerializer(user.current_designation.all(), many=True).data,
    }

    if profile['user_type'] == 'student':
        student = user.extrainfo.student
        skills = serializers.HasSerializer(student.has_set.all(),many=True).data
        education = serializers.EducationSerializer(student.education_set.all(), many=True).data
        course = serializers.CourseSerializer(student.course_set.all(), many=True).data
        experience = serializers.ExperienceSerializer(student.experience_set.all(), many=True).data
        project = serializers.ProjectSerializer(student.project_set.all(), many=True).data
        achievement = serializers.AchievementSerializer(student.achievement_set.all(), many=True).data
        publication = serializers.PublicationSerializer(student.publication_set.all(), many=True).data
        patent = serializers.PatentSerializer(student.patent_set.all(), many=True).data
        current = serializers.HoldsDesignationSerializer(user.current_designation.all(), many=True).data
        resp = {
            **base_response,
            'skills' : skills,
            'education' : education,
            'course' : course,
            'experience' : experience,
            'project' : project,
            'achievement' : achievement,
            'publication' : publication,
            'patent' : patent,
            'current' : current
        }
        return Response(data=resp, status=status.HTTP_200_OK)
    elif profile['user_type'] == 'faculty':
        return Response(data=base_response, status=status.HTTP_200_OK)

    return Response(data=base_response, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def profile_update(request):
    user = request.user
    profile = user.extrainfo
    current = user.current_designation.filter(designation__name="student")
    if current:
        student = profile.student
        def _update_or_create(serializer_class, payload, *, instance_model=None, profile_field="unique_id"):
            payload = dict(payload)
            owner = student if profile_field == "unique_id" else profile
            payload[profile_field] = owner
            instance = None
            instance_id = payload.pop("id", None)
            if instance_model is not None and instance_id not in [None, ""]:
                filter_kwargs = {"id": instance_id}
                filter_kwargs[profile_field] = owner
                instance = instance_model.objects.filter(**filter_kwargs).first()
                if instance is None:
                    return None, Response({"error": "Record does not exist"}, status=status.HTTP_400_BAD_REQUEST)
            serializer = (
                serializer_class(instance, data=payload, partial=True)
                if instance
                else serializer_class(data=payload)
            )
            if serializer.is_valid():
                serializer.save()
                return serializer, Response(serializer.data, status=status.HTTP_200_OK)
            return serializer, Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if 'education' in request.data:
            serializer, response = _update_or_create(
                serializers.EducationSerializer,
                request.data['education'],
                instance_model=Education,
            )
            return response
        elif 'profilesubmit' in request.data:
            payload = request.data['profilesubmit']
            required_errors = {}
            for field in ['about_me', 'date_of_birth', 'address', 'phone_no']:
                if field in payload and payload.get(field) in [None, '', []]:
                    required_errors[field] = ['This field is required.']
            if required_errors:
                return Response(required_errors, status=status.HTTP_400_BAD_REQUEST)
            serializer = serializers.ExtraInfoSerializer(profile, data=request.data['profilesubmit'],partial=True)
            if serializer.is_valid():
                serializer.save()
                PlacementProfileAuditLog.objects.create(
                    student=student,
                    actor=request.user,
                    action='profile_updated',
                    details={key: value for key, value in payload.items() if key in ['about_me', 'date_of_birth', 'address', 'phone_no']},
                )
                notify.send(
                    sender=request.user,
                    recipient=request.user,
                    verb='Your profile has been updated.',
                    url='/profile',
                    module='Placement Cell',
                )
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif 'skillsubmit' in request.data:
            payload = dict(request.data['skillsubmit'])
            skill_instance = None
            if payload.get('id') not in [None, '']:
                skill_instance = Has.objects.filter(id=payload.get('id'), unique_id=student).first()
                if skill_instance is None:
                    return Response({'error': 'Skill does not exist'}, status=status.HTTP_400_BAD_REQUEST)
                payload.pop('id', None)
            serializer = (
                serializers.HasSerializer(skill_instance, data=payload, partial=True)
                if skill_instance
                else serializers.HasSerializer(data=payload)
            )
            if serializer.is_valid():
                serializer.save(unique_id=student)
                PlacementProfileAuditLog.objects.create(
                    student=student,
                    actor=request.user,
                    action='skill_updated' if skill_instance else 'skill_added',
                    details={'skill': request.data['skillsubmit'].get('skill_id', {})},
                )
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif 'achievementsubmit' in request.data:
            serializer, response = _update_or_create(
                serializers.AchievementSerializer,
                request.data['achievementsubmit'],
                instance_model=Achievement,
            )
            return response
        elif 'publicationsubmit' in request.data:
            serializer, response = _update_or_create(
                serializers.PublicationSerializer,
                request.data['publicationsubmit'],
                instance_model=Publication,
            )
            return response
        elif 'patentsubmit' in request.data:
            serializer, response = _update_or_create(
                serializers.PatentSerializer,
                request.data['patentsubmit'],
                instance_model=Patent,
            )
            return response
        elif 'coursesubmit' in request.data:
            serializer, response = _update_or_create(
                serializers.CourseSerializer,
                request.data['coursesubmit'],
                instance_model=Course,
            )
            return response
        elif 'projectsubmit' in request.data:
            serializer, response = _update_or_create(
                serializers.ProjectSerializer,
                request.data['projectsubmit'],
                instance_model=Project,
            )
            if response.status_code == status.HTTP_200_OK:
                PlacementProfileAuditLog.objects.create(
                    student=student,
                    actor=request.user,
                    action='project_updated' if request.data['projectsubmit'].get('id') else 'project_added',
                    details={'project_name': request.data['projectsubmit'].get('project_name')},
                )
            return response
        elif 'experiencesubmit' in request.data:
            serializer, response = _update_or_create(
                serializers.ExperienceSerializer,
                request.data['experiencesubmit'],
                instance_model=Experience,
            )
            if response.status_code == status.HTTP_200_OK:
                PlacementProfileAuditLog.objects.create(
                    student=student,
                    actor=request.user,
                    action='experience_updated' if request.data['experiencesubmit'].get('id') else 'experience_added',
                    details={'title': request.data['experiencesubmit'].get('title')},
                )
            return response
    return Response({'error': 'Cannot update'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def profile_delete(request, id):
    user = request.user
    profile = user.extrainfo
    student = profile.student
    if 'deleteskill' in request.data:
        try:
            skill = Has.objects.get(id=id)
        except:
            return Response({'error': 'Skill does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        skill.delete()
        return Response({'message': 'Skill deleted successfully'}, status=status.HTTP_200_OK)
    elif 'deleteedu' in request.data:
        try:
            education = Education.objects.get(id=id)
        except:
            return Response({'error': 'Education does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        education.delete()
        return Response({'message': 'Education deleted successfully'}, status=status.HTTP_200_OK)
    elif 'deletecourse' in request.data:
        try:
            course = Course.objects.get(id=id)
        except:
            return Response({'error': 'Course does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        course.delete()
        return Response({'message': 'Course deleted successfully'}, status=status.HTTP_200_OK)
    elif 'deleteexp' in request.data:
        try:
            experience = Experience.objects.get(id=id)
        except:
            return Response({'error': 'Experience does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        experience.delete()
        return Response({'message': 'Experience deleted successfully'}, status=status.HTTP_200_OK)
    elif 'deletepro' in request.data:
        try:
            project = Project.objects.get(id=id)
        except:
            return Response({'error': 'Project does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        project.delete()
        return Response({'message': 'Project deleted successfully'}, status=status.HTTP_200_OK)
    elif 'deleteach' in request.data:
        try:
            achievement = Achievement.objects.get(id=id)
        except:
            return Response({'error': 'Achievement does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        achievement.delete()
        return Response({'message': 'Achievement deleted successfully'}, status=status.HTTP_200_OK)
    elif 'deletepub' in request.data:
        try:
            publication = Publication.objects.get(id=id)
        except:
            return Response({'error': 'Publication does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        publication.delete()
        return Response({'message': 'Publication deleted successfully'}, status=status.HTTP_200_OK)
    elif 'deletepat' in request.data:
        try:
            patent = Patent.objects.get(id=id)
        except:
            return Response({'error': 'Patent does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        patent.delete()
        return Response({'message': 'Patent deleted successfully'}, status=status.HTTP_200_OK)
    return Response({'error': 'Wrong attribute'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def NotificationRead(request):
    try:
        notifId=int(request.data['id'])
        user=request.user
        notification = get_object_or_404(Notification, recipient=request.user, id=notifId)
        notification.mark_as_read()
        response ={
            'message':'notfication successfully marked as seen.'
        }
        return Response(response,status=status.HTTP_200_OK)
    except:
        response ={
            'error':'Failed, notification is not marked as seen.'
        }
        return Response(response,status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def NotificationList(request):
    notifications = request.user.notifications.all().order_by('-timestamp')
    serializer = serializers.NotificationSerializer(notifications, many=True)
    return Response({'notifications': serializer.data}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def NotificationUnread(request):
    try:
        notifId = int(request.data['id'])
        notification = get_object_or_404(Notification, recipient=request.user, id=notifId)
        notification.mark_as_unread()
        response = {
            'message': 'notification successfully marked as unseen.'
        }
        return Response(response, status=status.HTTP_200_OK)
    except:
        response = {
            'error': 'Failed, notification is not marked as unseen.'
        }
        return Response(response, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def NotificationDelete(request):
    try:
        notifId = int(request.data['id'])
        notification = get_object_or_404(Notification, recipient=request.user, id=notifId)
        notification.deleted = True
        notification.unread = False
        notification.save(update_fields=['deleted', 'unread'])
        response = {
            'message': 'notification deleted successfully.'
        }
        return Response(response, status=status.HTTP_200_OK)
    except:
        response = {
            'error': 'Failed to delete notification.'
        }
        return Response(response, status=status.HTTP_404_NOT_FOUND)
