from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status

from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo
from applications.placement_cell.models import (
    Achievement,
    Course,
    Education,
    Experience,
    Has,
    Patent,
    PlacementStatus,
    Project,
    Publication,
    Skill,
)

from . import serializers
from .selectors import (
    get_accessible_modules,
    get_designation_names,
    get_student_profile_querysets,
)


PROFILE_DELETE_MODEL_MAP = {
    "deleteskill": (Has, "Skill does not exist"),
    "deleteedu": (Education, "Education does not exist"),
    "deletecourse": (Course, "Course does not exist"),
    "deleteexp": (Experience, "Experience does not exist"),
    "deletepro": (Project, "Project does not exist"),
    "deleteach": (Achievement, "Achievement does not exist"),
    "deletepub": (Publication, "Publication does not exist"),
    "deletepat": (Patent, "Patent does not exist"),
}


def build_login_payload(user, token):
    designation = get_designation_names(user)
    return {
        "success": "True",
        "message": "User logged in successfully",
        "token": token,
        "designations": designation,
    }


def build_auth_payload(user):
    extra_info = get_object_or_404(ExtraInfo, user=user)
    designation_info = get_designation_names(user)

    return {
        "designation_info": designation_info,
        "name": f"{user.first_name}_{user.last_name}",
        "roll_no": user.username,
        "accessible_modules": get_accessible_modules(designation_info),
        "last_selected_role": extra_info.last_selected_role,
    }


def build_student_profile_payload(user):
    profile_data = serializers.ExtraInfoSerializer(user.extrainfo).data
    if profile_data["user_type"] != "student":
        return None

    student = user.extrainfo.student
    std_sem = Student.objects.only("curr_semester_no").get(id=student.id).curr_semester_no
    querysets = get_student_profile_querysets(student)

    return {
        "profile": profile_data,
        "semester_no": std_sem,
        "skills": querysets["skills"],
        "education": serializers.EducationSerializer(querysets["education"], many=True).data,
        "course": serializers.CourseSerializer(querysets["course"], many=True).data,
        "experience": serializers.ExperienceSerializer(querysets["experience"], many=True).data,
        "project": serializers.ProjectSerializer(querysets["project"], many=True).data,
        "achievement": serializers.AchievementSerializer(querysets["achievement"], many=True).data,
        "publication": serializers.PublicationSerializer(querysets["publication"], many=True).data,
        "patent": serializers.PatentSerializer(querysets["patent"], many=True).data,
        "current": serializers.HoldsDesignationSerializer(querysets["current"], many=True).data,
    }


def _save_serializer(serializer_cls, payload, profile):
    payload = dict(payload)
    payload["unique_id"] = profile
    serializer = serializer_cls(data=payload)
    if serializer.is_valid():
        serializer.save()
        return serializer.data, status.HTTP_200_OK
    return serializer.errors, status.HTTP_400_BAD_REQUEST


def update_profile_from_payload(user, payload):
    profile = user.extrainfo
    if not user.current_designation.filter(designation__name="student").exists():
        return {"error": "Cannot update"}, status.HTTP_400_BAD_REQUEST

    if "education" in payload:
        return _save_serializer(serializers.EducationSerializer, payload["education"], profile)

    if "profilesubmit" in payload:
        serializer = serializers.ExtraInfoSerializer(profile, data=payload["profilesubmit"], partial=True)
        if serializer.is_valid():
            serializer.save()
            return serializer.data, status.HTTP_200_OK
        return serializer.errors, status.HTTP_400_BAD_REQUEST

    if "skillsubmit" in payload:
        skill_serializer = serializers.ProfileSkillCreateSerializer(data=payload["skillsubmit"])
        if not skill_serializer.is_valid():
            return skill_serializer.errors, status.HTTP_400_BAD_REQUEST

        skill_name = skill_serializer.validated_data["skill_name"]
        skill_rating = skill_serializer.validated_data["skill_rating"]
        student = profile.student

        skill, _ = Skill.objects.get_or_create(skill=skill_name)
        has_obj, created = Has.objects.get_or_create(
            skill_id=skill,
            unique_id=student,
            defaults={"skill_rating": skill_rating},
        )
        if not created:
            has_obj.skill_rating = skill_rating
            has_obj.save(update_fields=["skill_rating"])

        return {"message": "Skill added successfully"}, status.HTTP_200_OK

    serializer_dispatch = {
        "achievementsubmit": serializers.AchievementSerializer,
        "publicationsubmit": serializers.PublicationSerializer,
        "patentsubmit": serializers.PatentSerializer,
        "coursesubmit": serializers.CourseSerializer,
        "projectsubmit": serializers.ProjectSerializer,
        "experiencesubmit": serializers.ExperienceSerializer,
    }

    for key, serializer_cls in serializer_dispatch.items():
        if key in payload:
            return _save_serializer(serializer_cls, payload[key], profile)

    return {"error": "Cannot update"}, status.HTTP_400_BAD_REQUEST


def delete_entity(model_cls, entity_id):
    instance = model_cls.objects.get(id=entity_id)
    instance.delete()


def delete_profile_component(payload, entity_id):
    request_serializer = serializers.ProfileDeleteRequestSerializer(data=payload)
    if not request_serializer.is_valid():
        return request_serializer.errors, status.HTTP_400_BAD_REQUEST

    delete_key = request_serializer.validated_data["delete_key"]
    model_cls, missing_msg = PROFILE_DELETE_MODEL_MAP[delete_key]

    try:
        delete_entity(model_cls, entity_id)
    except model_cls.DoesNotExist:
        return {"error": missing_msg}, status.HTTP_400_BAD_REQUEST

    entity_name = missing_msg.replace(" does not exist", "")
    return {"message": f"{entity_name} deleted successfully"}, status.HTTP_200_OK


def delete_entity_from_request(payload, key_to_model):
    for key, model_cls in key_to_model.items():
        if key in payload:
            entity_id = payload.get(key)
            if entity_id in [None, ""]:
                return False
            try:
                delete_entity(model_cls, entity_id)
            except model_cls.DoesNotExist:
                return False
            return True
    return False


def parse_notification_id(payload):
    notif_id = payload.get("id")
    if notif_id is None:
        raise KeyError("id")
    return int(notif_id)


def update_profile_core_fields(extra_info, payload):
    serializer = serializers.ProfileSubmitSerializer(data=payload)
    serializer.is_valid(raise_exception=True)

    validated_data = serializer.validated_data
    extra_info.about_me = validated_data.get('about', '')
    extra_info.date_of_birth = validated_data['age']
    extra_info.address = validated_data.get('address', '')
    extra_info.phone_no = validated_data['contact']
    extra_info.save(update_fields=['about_me', 'date_of_birth', 'address', 'phone_no'])
    return extra_info


def update_placement_invitation_status(status_id, invitation):
    return PlacementStatus.objects.filter(pk=status_id).update(
        invitation=invitation,
        timestamp=timezone.now(),
    )
