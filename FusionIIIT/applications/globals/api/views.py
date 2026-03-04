from django.contrib.auth import get_user_model
from applications.academic_information.models import Student
from applications.placement_cell.models import (Achievement, Course, Education,
                                                Experience, Has, Patent,
                                                Project, Publication, Skill)
from applications.programme_curriculum.models import (
    Course as CurriculumCourse, CourseSlot, CourseInstructor
)
from django.shortcuts import get_object_or_404
from django.db import transaction

import hashlib
import hmac
import logging
import secrets
import re
from datetime import timedelta
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import JsonResponse

from . import serializers
from applications.globals.models import (ExtraInfo, HoldsDesignation, ModuleAccess,
                                         Designation, PasswordResetOTP)
from .utils import get_and_authenticate_user
from notifications.models import Notification
_security_log = logging.getLogger("fusion.security")

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = serializers.UserLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = get_and_authenticate_user(**serializer.validated_data)
    data = serializers.AuthUserSerializer(user).data
    
    design = HoldsDesignation.objects.select_related('user','designation').filter(working=user)

    designation=[]
                
    if str(user.extrainfo.user_type) == "student":
        designation.append(str(user.extrainfo.user_type))
        
    for i in design:
        if str(i.designation) != str(user.extrainfo.user_type):
            designation.append(str(i.designation))
    
    resp = {
        'success' : True,
        'message' : 'User logged in successfully',
        'token' : data['auth_token'],
        'designations': designation
    }
    return Response(data=resp, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def logout(request):
    try:
        request.user.auth_token.delete()
    except Exception:
        pass  # token already deleted or doesn't exist — still return success
    return Response({'message': 'User logged out successfully'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def auth_view(request):
    user=request.user
    name = request.user.first_name +"_"+ request.user.last_name
    roll_no = request.user.username

    extra_info = get_object_or_404(ExtraInfo, user=user)
    last_selected_role = extra_info.last_selected_role
    
    designation_list = list(HoldsDesignation.objects.filter(working=request.user).values_list('designation_id', flat=True))
    designation_info = list(
        Designation.objects.filter(id__in=designation_list).values_list('name', flat=True)
    )

    accessible_modules = {}
    
    for designation in designation_info:
        module_access = ModuleAccess.objects.filter(designation__iexact=designation).first()
        if module_access:
            filtered_modules = {}

            field_names = [field.name for field in ModuleAccess._meta.get_fields() if field.name not in ['id', 'designation']]

            for field_name in field_names:
                filtered_modules[field_name] = getattr(module_access, field_name)
            
            accessible_modules[designation] = filtered_modules
            
    resp={
        'designation_info' : designation_info,
        'name': name,
        'roll_no': roll_no,
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
@authentication_classes([TokenAuthentication])
def update_last_selected_role(request):
    new_role = request.data.get('last_selected_role')

    if new_role is None:
        return Response({'error': 'last_selected_role is required'}, status=status.HTTP_400_BAD_REQUEST)

    extra_info = get_object_or_404(ExtraInfo, user=request.user)

    extra_info.last_selected_role = new_role
    extra_info.save(update_fields=['last_selected_role'])

    return Response({'message': 'last_selected_role updated successfully'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def profile(request, username=None):
    user = get_object_or_404(User, username=username) if username else request.user
    profile = serializers.ExtraInfoSerializer(user.extrainfo).data
    
    if profile['user_type'] == 'student':
        student = user.extrainfo.student
        std_sem = student.curr_semester_no
        skills = list(
        Has.objects.filter(unique_id_id=student)
        .select_related("skill_id")
        .values("skill_id__skill", "skill_rating")
        )
        formatted_skills = [
            {"skill_name": skill["skill_id__skill"], "skill_rating": skill["skill_rating"]}
            for skill in skills
        ]
        education = serializers.EducationSerializer(student.education_set.all(), many=True).data
        course = serializers.CourseSerializer(student.course_set.all(), many=True).data
        experience = serializers.ExperienceSerializer(student.experience_set.all(), many=True).data
        project = serializers.ProjectSerializer(student.project_set.all(), many=True).data
        achievement = serializers.AchievementSerializer(student.achievement_set.all(), many=True).data
        publication = serializers.PublicationSerializer(student.publication_set.all(), many=True).data
        patent = serializers.PatentSerializer(student.patent_set.all(), many=True).data
        current = serializers.HoldsDesignationSerializer(user.current_designation.all(), many=True).data
        resp = {
            'profile' : profile,
            'semester_no' : std_sem,
            'skills' : formatted_skills,
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
    else:
        current = serializers.HoldsDesignationSerializer(user.current_designation.all(), many=True).data
        resp = {
            'profile'     : profile,
            'semester_no' : None,
            'skills'      : [],
            'education'   : [],
            'course'      : [],
            'experience'  : [],
            'project'     : [],
            'achievement' : [],
            'publication' : [],
            'patent'      : [],
            'current'     : current,
        }
        return Response(data=resp, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def profile_update(request):
    user = request.user
    profile = user.extrainfo

    # Basic profile fields apply to ALL users (students and non-students alike)
    if 'profilesubmit' in request.data:
        serializer = serializers.ExtraInfoSerializer(profile, data=request.data['profilesubmit'], partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # For student-only
    current = user.current_designation.filter(designation__name="student")
    if not current:
        return Response({'error': 'Cannot update'}, status=status.HTTP_400_BAD_REQUEST)

    student = profile.student
    if 'education' in request.data:
        data = request.data
        data['education']['unique_id'] = profile
        serializer = serializers.EducationSerializer(data=data['education'])
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif 'skillsubmit' in request.data:
        try:
            skill_data = request.data['skillsubmit']
            skill_id = skill_data['skill_id']
            skill_name = skill_id['skill_name']
            skill_rating = skill_data['skill_rating']

            if not skill_name or skill_rating is None:
                return Response({"error": "Missing skill_name or skill_rating"}, status=status.HTTP_400_BAD_REQUEST)

            skill, _ = Skill.objects.get_or_create(skill=skill_name)
            has_obj, created = Has.objects.get_or_create(skill_id=skill, unique_id=student, defaults={"skill_rating": skill_rating})
            if not created:
                has_obj.skill_rating = skill_rating
                has_obj.save(update_fields=['skill_rating'])

            return Response({"message": "Skill added successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def profile_delete(request, id):
    user = request.user
    profile = user.extrainfo
    # All records are scoped to the requesting user's own profile via unique_id__extrainfo.
    # Using get_object_or_404 with the ownership filter ensures that a record belonging
    # to another user is indistinguishable from a missing record (no ID enumeration).
    if 'deleteskill' in request.data:
        skill = get_object_or_404(Has, id=id, unique_id__extrainfo=profile)
        skill.delete()
        return Response({'message': 'Skill deleted successfully'}, status=status.HTTP_200_OK)
    elif 'deleteedu' in request.data:
        education = get_object_or_404(Education, id=id, unique_id__extrainfo=profile)
        education.delete()
        return Response({'message': 'Education deleted successfully'}, status=status.HTTP_200_OK)
    elif 'deletecourse' in request.data:
        course = get_object_or_404(Course, id=id, unique_id__extrainfo=profile)
        course.delete()
        return Response({'message': 'Course deleted successfully'}, status=status.HTTP_200_OK)
    elif 'deleteexp' in request.data:
        experience = get_object_or_404(Experience, id=id, unique_id__extrainfo=profile)
        experience.delete()
        return Response({'message': 'Experience deleted successfully'}, status=status.HTTP_200_OK)
    elif 'deletepro' in request.data:
        project = get_object_or_404(Project, id=id, unique_id__extrainfo=profile)
        project.delete()
        return Response({'message': 'Project deleted successfully'}, status=status.HTTP_200_OK)
    elif 'deleteach' in request.data:
        achievement = get_object_or_404(Achievement, id=id, unique_id__extrainfo=profile)
        achievement.delete()
        return Response({'message': 'Achievement deleted successfully'}, status=status.HTTP_200_OK)
    elif 'deletepub' in request.data:
        publication = get_object_or_404(Publication, id=id, unique_id__extrainfo=profile)
        publication.delete()
        return Response({'message': 'Publication deleted successfully'}, status=status.HTTP_200_OK)
    elif 'deletepat' in request.data:
        patent = get_object_or_404(Patent, id=id, unique_id__extrainfo=profile)
        patent.delete()
        return Response({'message': 'Patent deleted successfully'}, status=status.HTTP_200_OK)
    return Response({'error': 'Wrong attribute'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def NotificationRead(request):
    try:
        notif_id = int(request.data['id'])
        notification = get_object_or_404(Notification, recipient=request.user, id=notif_id)
        notification.mark_as_read()
        return Response({'message': 'Notification successfully marked as seen.'}, status=status.HTTP_200_OK)
    except Exception:
        return Response({'error': 'Failed to mark notification as seen.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def NotificationUnread(request):
    try:
        notif_id = int(request.data['id'])
        notification = get_object_or_404(Notification, recipient=request.user, id=notif_id)
        if not notification.unread:
            notification.unread = True
            notification.save(update_fields=['unread'])
        return Response({'message': 'Notification successfully marked as unread.'}, status=status.HTTP_200_OK)
    except Exception:
        return Response({'error': 'Failed to mark the notification as unread.'}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['POST']) 
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def delete_notification(request):
    try:
        notif_id = int(request.data['id'])
        notification = get_object_or_404(Notification, recipient=request.user, id=notif_id)
        
        notification.deleted = True
        notification.save(update_fields=['deleted'])
        
        response = {
            'message': 'Notification marked as deleted.'
        }
        return Response(response, status=status.HTTP_200_OK)
    except Exception:
        return Response(
            {'error': 'Failed to mark the notification as deleted.'},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def admin_delete_course_proxy(request, course_id):
    """
    Delete a curriculum course after validating no instructor or slot dependencies exist.
    """
    try:
        course = CurriculumCourse.objects.get(id=course_id)
    except CurriculumCourse.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Course not found.'}, status=404)

    course_name = course.name

    instructor_count = CourseInstructor.objects.filter(course_id=course).count()
    if instructor_count > 0:
        return JsonResponse({
            'success': False,
            'message': f'Cannot delete course. It has {instructor_count} active instructor assignment(s). Remove instructor assignments first.'
        }, status=400)

    slot_count = CourseSlot.objects.filter(courses=course).count()
    if slot_count > 0:
        return JsonResponse({
            'success': False,
            'message': f'Cannot delete course. It is assigned to {slot_count} course slot(s). Remove from course slots first.'
        }, status=400)

    try:
        with transaction.atomic():
            course.delete()
        return JsonResponse({'success': True, 'message': f'Course "{course_name}" deleted successfully.'}, status=200)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error deleting course: {e}'}, status=500)


# OTP-based Password Reset

def _otp_hash(otp: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode(),
        otp.encode(),
        hashlib.sha256,
    ).hexdigest()


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

_safe_eq = hmac.compare_digest

_SEND_OTP_OK = {
    "success": True,
    "message": "If the username exists, an OTP has been sent to the registered e-mail.",
}


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_send_otp(request):
    """
    POST /api/auth/password-reset/send-otp/
    Body: { "username": "<username>" }
    Generates a 6-digit OTP, stores its HMAC hash, and e-mails it to the
    user's registered address.
    Rate-limited: max OTP_HOURLY_LIMIT sends per hour per username.
    Always returns HTTP 200 with an identical message to prevent enumeration.
    """
    username = (request.data.get("username") or "").strip().lower()
    if not username:
        return Response({"success": False, "message": "Username is required."}, status=400)

    try:
        user = User.objects.get(username__iexact=username)
    except User.DoesNotExist:
        return Response(_SEND_OTP_OK)

    if not user.email:
        return Response(_SEND_OTP_OK)

    now = timezone.now()
    record = PasswordResetOTP.objects.filter(username=user.username).first()

    if record:
        window_age = (now - record.window_start).total_seconds()
        if window_age < 3600:
            if record.send_count >= PasswordResetOTP.OTP_HOURLY_LIMIT:
                return Response(
                    {"success": False, "message": "Too many OTP requests. Please wait before trying again."},
                    status=429,
                )
            record.send_count += 1
        else:
            record.send_count = 1
            record.window_start = now
    else:
        record = PasswordResetOTP(username=user.username, window_start=now)

    otp = f"{secrets.randbelow(1_000_000):06d}"
    record.otp_hash         = _otp_hash(otp)
    record.attempts         = 0
    record.expires_at       = now + timedelta(minutes=PasswordResetOTP.OTP_TTL_MINUTES)
    record.reset_token_hash = None
    record.token_expires_at = None
    record.token_used       = False
    record.save()

    try:
        subject = "Fusion – Password Reset OTP"

        text_message = (
            f"Hello {user.first_name or user.username},\n\n"
            f"Your OTP for password reset is: {otp}\n\n"
            f"It is valid for {PasswordResetOTP.OTP_TTL_MINUTES} minutes.\n"
            f"Do NOT share this OTP with anyone.\n\n"
            f"If you did not request this, you can safely ignore this e-mail.\n\n"
            f"— PDPM IIITDM Jabalpur"
        )

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <p>Dear <strong>{user.first_name or user.username}</strong>,</p>
                
                <p>We received a request to reset your FUSION account password. Please use the One-Time Password (OTP) below to complete the password reset process:</p>
                
                <div style="background-color: #e3f2fd; padding: 25px; border-left: 4px solid #2196f3; margin: 25px 0; border-radius: 4px; text-align: center;">
                    <p style="margin: 0 0 10px 0; font-size: 14px; color: #666;">Your OTP Code:</p>
                    <p style="margin: 0; font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #1976d2; font-family: 'Courier New', monospace;">{otp}</p>
                    <p style="margin: 10px 0 0 0; font-size: 14px; color: #666;">Valid for <strong>{PasswordResetOTP.OTP_TTL_MINUTES} minutes</strong></p>
                </div>
                
                <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; border-radius: 4px;">
                    <h4 style="margin-top: 0; color: #856404;">⚠️ Security Note</h4>
                    <ul style="margin-bottom: 0; color: #856404; padding-left: 20px;">
                        <li>Do NOT share this OTP with anyone.</li>
                        <li>This OTP will expire in {PasswordResetOTP.OTP_TTL_MINUTES} minutes</li>
                        <li>If you did not request this reset, please ignore this email</li>
                    </ul>
                </div>
                
                <div style="background-color: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0; border-radius: 4px;">
                    <h4 style="margin-top: 0; color: #155724;">📞 Need Help?</h4>
                    <p style="margin-bottom: 0; color: #155724;">
                        For technical support or security concerns, contact:<br>
                        📧 <a href="mailto:{settings.EMAIL_HOST_USER}" style="color: #155724;">{settings.EMAIL_HOST_USER}</a><br>
                        🏢 PDPM IIITDM Jabalpur
                    </p>
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 4px; font-size: 12px; color: #6c757d; text-align: center;">
                    This is an automated security message from FUSION. Do not reply to this email.
                    Generated on {timezone.now().strftime('%B %d, %Y at %I:%M %p IST')}
                </div>
            </div>
        </body>
        </html>
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        
        email.attach_alternative(html_content, "text/html")
        email.send()
        
    except Exception:
        _security_log.exception("OTP email delivery failed | user=%s", user.username)

    return Response(_SEND_OTP_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_verify_otp(request):
    """
    POST /api/auth/password-reset/verify-otp/
    Body: { "username": "<username>", "otp": "<6-digit OTP>" }
    Validates the OTP and, on success, returns a single-use reset token.
    Locked after OTP_MAX_ATTEMPTS failed attempts.
    """
    username = (request.data.get("username") or "").strip().lower()
    otp      = (request.data.get("otp")      or "").strip()

    if not username or not otp:
        return Response({"success": False, "message": "Username and OTP are required."}, status=400)

    _INVALID = {"success": False, "message": "Invalid or expired OTP."}

    record = PasswordResetOTP.objects.filter(username__iexact=username).first()
    if not record:
        return Response(_INVALID, status=400)

    now = timezone.now()

    if now > record.expires_at:
        return Response({"success": False, "message": "OTP has expired. Please request a new one."}, status=400)

    if record.attempts >= PasswordResetOTP.OTP_MAX_ATTEMPTS:
        return Response(
            {"success": False, "message": "Too many incorrect attempts. Please request a new OTP."},
            status=429,
        )

    if not _safe_eq(_otp_hash(otp), record.otp_hash):
        record.attempts += 1
        record.save(update_fields=["attempts"])
        remaining = PasswordResetOTP.OTP_MAX_ATTEMPTS - record.attempts
        return Response(
            {"success": False, "message": f"Incorrect OTP. {remaining} attempt(s) remaining."},
            status=400,
        )

    reset_token = secrets.token_urlsafe(32)
    record.otp_hash         = ""                     
    record.attempts         = PasswordResetOTP.OTP_MAX_ATTEMPTS
    record.reset_token_hash = _token_hash(reset_token)
    record.token_expires_at = now + timedelta(minutes=PasswordResetOTP.TOKEN_TTL_MINUTES)
    record.token_used       = False
    record.save()

    return Response({"success": True, "reset_token": reset_token})


def _validate_password_complexity(password):
    """
    Validates password complexity requirements:
    - At least 8 characters
    - At most 72 characters (bcrypt hard truncation limit)
    - At least one lowercase letter (a-z)
    - At least one uppercase letter (A-Z)
    - At least one number (0-9)
    - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters."

    if len(password) > 72:  # bcrypt silently truncates beyond 72 bytes (DoS vector)
        return False, "Password exceeds maximum length (72 characters)."

    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter (a-z)."

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter (A-Z)."

    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number (0-9)."

    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        return False, "Password must contain at least one special character (!@#$%^&* etc)."

    return True, ""


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_reset(request):
    """
    POST /api/auth/password-reset/reset/
    Body: { "username": "<username>", "reset_token": "<token>", "new_password": "<password>" }
    Validates the single-use token and sets the new password.
    """
    username     = (request.data.get("username")    or "").strip().lower()
    reset_token  = (request.data.get("reset_token") or "").strip()
    new_password = request.data.get("new_password", "")

    if not username or not reset_token or not new_password:
        return Response({"success": False, "message": "All fields are required."}, status=400)

    # Validate password complexity
    is_valid, error_message = _validate_password_complexity(new_password)
    if not is_valid:
        return Response({"success": False, "message": error_message}, status=400)

    _INVALID = {"success": False, "message": "Invalid or expired reset token."}

    record = PasswordResetOTP.objects.filter(username__iexact=username).first()
    if not record or not record.reset_token_hash:
        return Response(_INVALID, status=400)

    now = timezone.now()

    if record.token_used:
        return Response(_INVALID, status=400)

    if not record.token_expires_at or now > record.token_expires_at:
        return Response({"success": False, "message": "Reset token has expired. Please start over."}, status=400)

    if not _safe_eq(_token_hash(reset_token), record.reset_token_hash):
        return Response(_INVALID, status=400)

    try:
        user = User.objects.get(username__iexact=username)
    except User.DoesNotExist:
        return Response(_INVALID, status=400)

    record.token_used = True
    record.save(update_fields=["token_used"])

    user.set_password(new_password)
    user.save(update_fields=["password"])

    record.delete()

    # Audit trail — visible in logs when fusion.security logger is configured
    _security_log.info(
        "[PASSWORD_RESET] success | user=%s | ip=%s",
        username,
        request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "unknown")),
    )

    return Response({"success": True, "message": "Password has been reset successfully."})
