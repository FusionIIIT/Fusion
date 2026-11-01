from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import Http404
from django.utils import timezone

from .models import Assignment, CourseRole, GradeAudit, Material, Submission, Workspace


def associations(user, workspace=None):
    # These are the current registration tables, not the retired Register tables.
    from applications.academic_procedures.models import course_registration
    from applications.programme_curriculum.models import CourseInstructor
    registrations = course_registration.objects.filter(student_id__id__user_id=user.pk)
    instructors = CourseInstructor.objects.filter(instructor_id__id__user_id=user.pk)
    if workspace:
        values = dict(course_id=workspace.course_id, semester_type=workspace.semester_type)
        if instructors.filter(year=workspace.year, **values).exists():
            return 'faculty'
        link = CourseRole.objects.filter(workspace=workspace, user=user).first()
        if link:
            return link.role
        if registrations.filter(working_year=workspace.year, **values).exists():
            return 'student'
        raise Http404('No such course workspace.')
    # Local workspace metadata is owned by LMS; registration itself is never changed.
    for course_id, year, semester_type in registrations.values_list('course_id', 'working_year', 'semester_type'):
        if year and semester_type:
            Workspace.objects.get_or_create(course_id=course_id, year=year, semester_type=semester_type)
    for course_id, year, semester_type in instructors.values_list('course_id', 'year', 'semester_type'):
        if year and semester_type:
            Workspace.objects.get_or_create(course_id=course_id, year=year, semester_type=semester_type)
    result = []
    for row in Workspace.objects.all().order_by('-year', 'course_id'):
        try:
            role = associations(user, row)
            result.append((row, role))
        except Http404:
            pass
    return result


def require_role(user, workspace, allowed):
    role = associations(user, workspace)
    if role not in allowed:
        raise PermissionDenied('Your course role cannot perform this action.')
    return role


def release_due():
    now = timezone.now()
    return sum(model.objects.filter(state='scheduled', release_at__lte=now).update(state='published')
               for model in (Material, Assignment))


def publish_state(release_at):
    return 'scheduled' if release_at and release_at > timezone.now() else 'published'


@transaction.atomic
def submit(user, assignment, form):
    require_role(user, assignment.workspace, ('student',))
    assignment = Assignment.objects.select_for_update().get(pk=assignment.pk)
    if assignment.state != 'published' or (assignment.release_at and assignment.release_at > timezone.now()):
        raise ValidationError('The assignment is not available.')
    if timezone.now() >= assignment.due_at:
        raise ValidationError('Late-submission policy is unresolved (ISS-LMS-001); no late work was recorded.')
    if Submission.objects.filter(assignment=assignment, student=user).exists():
        raise ValidationError('Resubmission policy is unresolved (ISS-LMS-005); existing work is unchanged.')
    field = assignment.submission_type
    if not form.cleaned_data.get(field):
        raise ValidationError('Provide the configured submission type: ' + field)
    values = {field: form.cleaned_data[field]}
    return Submission.objects.create(assignment=assignment, student=user, **values)


@transaction.atomic
def grade(user, submission, values, release=False):
    require_role(user, submission.assignment.workspace, ('faculty',) if release else ('faculty', 'ta'))
    row = Submission.objects.select_for_update().get(pk=submission.pk)
    if row.revision != values['revision']:
        raise ValidationError('This submission changed. Refresh before saving.')
    before = {'points': str(row.points), 'feedback': row.feedback, 'released': row.released}
    if release:
        if row.points is None:
            raise ValidationError('Grade the submission before releasing it.')
        row.released = True
    else:
        if row.released:
            raise ValidationError('Post-release change authority/effect is unresolved (ISS-LMS-006).')
        if values['points'] > row.assignment.points_possible:
            raise ValidationError('Points exceed the assignment maximum.')
        row.points, row.feedback = values['points'], values['feedback']
        row.grader, row.graded_at = user, timezone.now()
    row.revision += 1
    row.save()
    GradeAudit.objects.create(submission=row, actor=user, old_values=before,
                              new_values={'points': str(row.points), 'feedback': row.feedback, 'released': row.released})
    return row
