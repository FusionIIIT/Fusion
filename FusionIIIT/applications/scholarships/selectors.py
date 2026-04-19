from django.utils import timezone
from applications.academic_information.models import Student
from .models import Award_and_scholarship, Release, Application


def get_student_by_user(user):
    """Safely retrieves the Student record for the authenticated user."""
    if not user or not user.is_authenticated:
        return None

    # User -> ExtraInfo -> Student relation in Fusion data model.
    return Student.objects.select_related(
        "id__user", "id__department", "batch_id__discipline"
    ).filter(id__user=user).first()


def get_active_releases(student_batch: str, student_programme: str):
    """Retrieves scholarship releases that are currently open for a student's demographic."""
    today = timezone.now().date()
    return Release.objects.filter(
        startdate__lte=today,
        enddate__gte=today,
        batch__iexact=student_batch,
        programme__iexact=student_programme,
        notif_visible=True
    ).select_related('award')


def get_student_applications(student_id: str):
    """Retrieves all applications submitted by a specific student."""
    return Application.objects.filter(student__id=student_id).select_related('award')


def get_all_applications_for_convener(status_filter=None):
    """Retrieves applications for the convener, optionally filtered by status."""
    qs = Application.objects.select_related('student', 'award')
    if status_filter:
        qs = qs.filter(status=status_filter)
    return qs


def get_application_by_id(application_id: int):
    """Retrieves a single application by its primary key."""
    return Application.objects.select_related('student', 'award').filter(id=application_id).first()
