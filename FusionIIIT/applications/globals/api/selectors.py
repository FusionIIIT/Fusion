from django.db.models import Avg

from applications.globals.models import Feedback, HoldsDesignation, Issue, ModuleAccess
from applications.placement_cell.models import (
    Achievement,
    Course,
    Education,
    Experience,
    Has,
    Patent,
    Project,
    Publication,
)


def get_designation_names(user):
    designation_names = []

    if str(user.extrainfo.user_type) == "student":
        designation_names.append("student")

    designations = HoldsDesignation.objects.select_related("designation").filter(working=user)
    for designation in designations:
        designation_name = str(designation.designation)
        if designation_name not in designation_names:
            designation_names.append(designation_name)

    return designation_names


def get_accessible_modules(designation_names):
    accessible_modules = {}

    for designation_name in designation_names:
        module_access = ModuleAccess.objects.prefetch_related('modules').filter(
            designation__iexact=designation_name
        ).first()
        if not module_access:
            continue

        accessible_modules[designation_name] = module_access.get_module_access_map()

    return accessible_modules


def get_student_profile_querysets(student):
    return {
        "skills": list(
            Has.objects.filter(unique_id=student)
            .select_related("skill_id")
            .values("skill_id__skill", "skill_rating")
        ),
        "education": Education.objects.filter(unique_id=student),
        "course": Course.objects.filter(unique_id=student),
        "experience": Experience.objects.filter(unique_id=student),
        "project": Project.objects.filter(unique_id=student),
        "achievement": Achievement.objects.filter(unique_id=student),
        "publication": Publication.objects.filter(unique_id=student),
        "patent": Patent.objects.filter(unique_id=student),
        "current": student.id.user.current_designation.select_related("designation").all(),
    }


def get_open_issues():
    return Issue.objects.get_open_issues()


def get_closed_issues():
    return Issue.objects.get_closed_issues()


def get_feedback_average_rating():
    return Feedback.objects.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
