"""When a student owes course feedback.

The feedback form records the student's current semester only, so that is the
only term feedback can gate: an older term could never be unlocked. Shared by
the form, which lists the courses, and by the result views, which hold back the
current term's result until the form is filled.
"""
from applications.academic_procedures.models import (
    FeedbackFilled, FeedbackQuestion, course_registration,
)
from applications.programme_curriculum.models import CourseInstructor


def feedback_courses(student):
    """The current semester's courses that have an instructor to give feedback
    on, each with that instructor, as the feedback form lists them."""
    from applications.academic_information.models import resolve_offering
    from applications.examination.api.views import parse_academic_year

    registrations = course_registration.objects.filter(
        student_id=student,
        semester_id__semester_no=student.curr_semester_no,
    ).select_related("course_id")

    courses = []
    for reg in registrations:
        course = reg.course_id
        academic_year, _ = parse_academic_year(reg.session, reg.semester_type)
        # The student's own section instructor, else any offering (no section courses).
        offering = resolve_offering(student, course, academic_year, reg.semester_type) or \
            CourseInstructor.objects.filter(
                course_id=course,
                semester_type=reg.semester_type,
                year=academic_year,
            ).first()
        if not offering:
            continue
        user = offering.instructor_id.id.user
        courses.append({
            "course_id": course.id,
            "code": course.code,
            "name": course.name,
            "instructor_id": offering.id,
            "instructor_name": f"{user.first_name} {user.last_name}".strip(),
        })
    return courses


def feedback_pending(student, semester_no):
    """Whether the student must fill feedback before seeing this term's result:
    it is their current semester, the form has something to fill, and they have
    not filled it. Every other term is never held back."""
    try:
        semester_no = int(semester_no)
    except (TypeError, ValueError):
        return False
    if semester_no != student.curr_semester_no:
        return False
    if FeedbackFilled.objects.filter(student=student, semester_no=semester_no).exists():
        return False
    if not FeedbackQuestion.objects.exists():
        return False
    return bool(feedback_courses(student))


FEEDBACK_REQUIRED = {
    "success": False,
    "require_feedback": True,
    "message": "Please submit your feedback form to access your results.",
}
