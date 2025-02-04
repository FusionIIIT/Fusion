from django.contrib.auth import get_user_model
from applications.academic_information.models import Student
from applications.eis.api.views import profile as eis_profile
from applications.globals.models import (HoldsDesignation,Designation)
from applications.gymkhana.api.views import coordinator_club
from applications.placement_cell.models import (Achievement, Course, Education,
                                                Experience, Has, Patent,
                                                Project, Publication, Skill)
from django.shortcuts import get_object_or_404, redirect

from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


from . import serializers
from applications.globals.models import (ExtraInfo, Feedback, HoldsDesignation,
                                         Issue, IssueImage, DepartmentInfo, ModuleAccess)
from .utils import get_and_authenticate_user
from notifications.models import Notification

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = serializers.UserLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_and_authenticate_user(**serializer.validated_data)
    data = serializers.AuthUserSerializer(user).data
    print(user.id)
    desig = list(HoldsDesignation.objects.select_related('user','working','designation').all().filter(working = user).values_list('designation'))
    print(desig)
    b = [i for sub in desig for i in sub]
    design = HoldsDesignation.objects.select_related('user','designation').filter(working=user)

    designation=[]
                
                
    if str(user.extrainfo.user_type) == "student":
        designation.append(str(user.extrainfo.user_type))
        
    for i in design:
        if str(i.designation) != str(user.extrainfo.user_type):
            print('-------')
            print(i.designation)
            print(user.extrainfo.user_type)
            print('')
            designation.append(str(i.designation))
    for i in designation:
        print(i)

    
    resp = {
        'success' : 'True',
        'message' : 'User logged in successfully',
        'token' : data['auth_token'],
        'designations':designation
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
@permission_classes([AllowAny])
def auth_view(request):
    user=request.user
    name = request.user.first_name +"_"+ request.user.last_name

    extra_info = get_object_or_404(ExtraInfo, user=user)
    last_selected_role = extra_info.last_selected_role
    
    designation_list = list(HoldsDesignation.objects.all().filter(working = request.user).values_list('designation'))
    designation_id = [designation for designations in designation_list for designation in designations]
    designation_info = []
    for id in designation_id :
        name_ = get_object_or_404(Designation, id = id)
        designation_info.append(str(name_.name))

    accessible_modules = {}
    
    for designation in designation_info:
        module_access = ModuleAccess.objects.filter(designation=designation).first()
        if module_access:
            filtered_modules = {}

            field_names = [field.name for field in ModuleAccess._meta.get_fields() if field.name not in ['id', 'designation']]

            for field_name in field_names:
                filtered_modules[field_name] = getattr(module_access, field_name)
            
            accessible_modules[designation] = filtered_modules
            
    resp={
        'designation_info' : designation_info,
        'name': name,
        'accessible_modules': accessible_modules,
        'last_selected_role': last_selected_role
    }
    
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
def profile(request, username=None):
    user = get_object_or_404(User, username=username) if username else request.user
    user_detail = serializers.UserSerializer(user).data
    profile = serializers.ExtraInfoSerializer(user.extrainfo).data

    print(user)
    
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
            'user' : user_detail,
            'profile' : profile,
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
        print(username)
        return redirect('/eis/api/profile/' + (username+'/' if username else ''))
    elif profile['user_type'] == 'staff':
        resp = {
            'user' : user_detail,
            'profile' : profile,
        }
        return Response(data=resp, status=status.HTTP_200_OK)   

@api_view(['PUT'])
def profile_update(request):
    user = request.user
    profile = user.extrainfo
    current = user.current_designation.filter(designation__name="student")
    if current:
        student = profile.student
        if 'education' in request.data:
            data = request.data
            data['education']['unique_id'] = profile
            serializer = serializers.EducationSerializer(data=data['education'])
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif 'profilesubmit' in request.data:
            serializer = serializers.ExtraInfoSerializer(profile, data=request.data['profilesubmit'],partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif 'skillsubmit' in request.data:
            serializer = serializers.HasSerializer(data=request.data['skillsubmit'])
            if serializer.is_valid():
                serializer.save(unique_id=student)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif 'achievementsubmit' in request.data:
            request.data['achievementsubmit']['unique_id'] = profile
            serializer = serializers.AchievementSerializer(data=request.data['achievementsubmit'])
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif 'publicationsubmit' in request.data:
            request.data['publicationsubmit']['unique_id'] = profile
            serializer = serializers.PublicationSerializer(data=request.data['publicationsubmit'])
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif 'patentsubmit' in request.data:
            request.data['patentsubmit']['unique_id'] = profile
            serializer = serializers.PatentSerializer(data=request.data['patentsubmit'])
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif 'coursesubmit' in request.data:
            request.data['coursesubmit']['unique_id'] = profile
            serializer = serializers.CourseSerializer(data=request.data['coursesubmit'])
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif 'projectsubmit' in request.data:
            request.data['projectsubmit']['unique_id'] = profile
            serializer = serializers.ProjectSerializer(data=request.data['projectsubmit'])
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif 'experiencesubmit' in request.data:
            request.data['experiencesubmit']['unique_id'] = profile
            serializer = serializers.ExperienceSerializer(data=request.data['experiencesubmit'])
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def NotificationUnread(request):
    try:
        notifId = int(request.data['id'])
        user = request.user
        notification = get_object_or_404(Notification, recipient=user, id=notifId)
        if not notification.unread:  
            notification.unread = True
            notification.save() 
        response = {
            'message': 'Notification successfully marked as unread.'
        }
        return Response(response, status=status.HTTP_200_OK)
    except:
        response = {
            'error': 'Failed to mark the notification as unread.'
        }
        return Response(response, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['POST']) 
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def delete_notification(request):
    try:
        notifId = int(request.data['id'])  
        notification = get_object_or_404(Notification, recipient=request.user, id=notifId)
        
        notification.deleted = True
        notification.save()
        
        response = {
            'message': 'Notification marked as deleted.'
        }
        return Response(response, status=status.HTTP_200_OK)
    except Exception as e:
        response = {
            'error': 'Failed to mark the notification as deleted.',
            'details': str(e)
        }
        return Response(response, status=status.HTTP_400_BAD_REQUEST)