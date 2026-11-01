from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import forms, services
from .models import Announcement, Assignment, CourseRole, Material, Submission, Workspace


@login_required
def index(request):
    rows = services.associations(request.user)
    from applications.programme_curriculum.models import Course
    courses = Course.objects.in_bulk([row.course_id for row, role in rows])
    return render(request, 'coursemanagement/lms_index.html', {'courses': [
        {'workspace': row, 'role': role, 'course': courses.get(row.course_id)} for row, role in rows]})


@login_required
def workspace(request, pk):
    row = get_object_or_404(Workspace, pk=pk)
    role = services.associations(request.user, row)
    services.release_due()
    materials = row.materials.all().order_by('section', 'id')
    assignments = row.assignments.all().order_by('due_at')
    if role != 'faculty':
        materials = materials.filter(state='published')
    if role == 'student':
        assignments = assignments.filter(state='published')
    elif role == 'observer':
        assignments = assignments.none()
    submissions = Submission.objects.filter(assignment__workspace=row).select_related('assignment', 'student', 'grader')
    if role == 'student':
        submissions = submissions.filter(student=request.user)
    elif role == 'observer':
        submissions = submissions.none()
    from applications.programme_curriculum.models import Course, CourseInstructor
    course = get_object_or_404(Course, pk=row.course_id)
    instructors = CourseInstructor.objects.filter(course_id=row.course_id, year=row.year, semester_type=row.semester_type).select_related('instructor_id__id__user')
    return render(request, 'coursemanagement/lms_workspace.html', {
        'workspace': row, 'course': course, 'role': role, 'materials': materials,
        'assignments': assignments, 'submissions': submissions,
        'announcements': row.announcements.order_by('-created_at'),
        'instructors': instructors, 'tas': row.roles.filter(role='ta').select_related('user'),
        'may_announce': role == 'faculty' or (role == 'ta' and CourseRole.objects.filter(workspace=row, user=request.user, role='ta', may_announce=True).exists()),
    })


@login_required
@transaction.atomic
def edit(request, pk, kind, item_id=None):
    row = get_object_or_404(Workspace, pk=pk)
    role = services.require_role(request.user, row, ('faculty', 'ta') if kind == 'announcement' else ('faculty',))
    if role == 'ta' and not CourseRole.objects.filter(workspace=row, user=request.user, role='ta', may_announce=True).exists():
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied('Faculty permission to post announcements is required.')
    definitions = {'details': (Workspace, forms.WorkspaceForm), 'material': (Material, forms.MaterialForm),
                   'assignment': (Assignment, forms.AssignmentForm), 'announcement': (Announcement, forms.AnnouncementForm)}
    if kind not in definitions:
        raise Http404()
    model, form_class = definitions[kind]
    instance = row if kind == 'details' else (get_object_or_404(model, pk=item_id, workspace=row) if item_id else None)
    if kind == 'assignment' and instance and instance.state != 'draft':
        return HttpResponse('Only draft assignments can be edited in this baseline.', status=409)
    form = form_class(request.POST or None, request.FILES or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        if kind != 'details':
            obj.workspace = row
        if kind == 'announcement':
            obj.author = request.user
        if kind == 'material':
            obj.state = services.publish_state(obj.release_at) if form.cleaned_data['publish'] else 'draft'
        obj.save()
        return redirect('lms:workspace', pk=row.pk)
    return render(request, 'coursemanagement/lms_form.html', {'form': form, 'workspace': row, 'title': 'Manage ' + kind})


@login_required
@require_POST
@transaction.atomic
def publish(request, pk, item_id):
    row = get_object_or_404(Workspace, pk=pk)
    services.require_role(request.user, row, ('faculty',))
    assignment = get_object_or_404(Assignment.objects.select_for_update(), pk=item_id, workspace=row)
    if assignment.state != 'draft':
        return HttpResponse('Assignment is already published.', status=409)
    assignment.full_clean()
    assignment.state = services.publish_state(assignment.release_at)
    assignment.save()
    return redirect('lms:workspace', pk=pk)


@login_required
def submit(request, pk, item_id):
    row = get_object_or_404(Workspace, pk=pk)
    services.require_role(request.user, row, ('student',))
    assignment = get_object_or_404(Assignment, pk=item_id, workspace=row, state='published')
    form = forms.SubmissionForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        try:
            services.submit(request.user, assignment, form)
            return redirect('lms:workspace', pk=pk)
        except ValidationError as exc:
            form.add_error(None, exc)
    return render(request, 'coursemanagement/lms_form.html', {'form': form, 'workspace': row, 'title': 'Submit ' + assignment.title})


@login_required
def grade(request, pk, item_id):
    row = get_object_or_404(Workspace, pk=pk)
    services.require_role(request.user, row, ('faculty', 'ta'))
    submission = get_object_or_404(Submission, pk=item_id, assignment__workspace=row)
    form = forms.GradeForm(request.POST or None, initial={'points': submission.points, 'feedback': submission.feedback, 'revision': submission.revision})
    if request.method == 'POST' and form.is_valid():
        try:
            services.grade(request.user, submission, form.cleaned_data, release=request.POST.get('action') == 'release')
            return redirect('lms:workspace', pk=pk)
        except ValidationError as exc:
            form.add_error(None, exc)
    return render(request, 'coursemanagement/lms_form.html', {'form': form, 'workspace': row, 'title': 'Grade submission', 'grade': True, 'may_release': services.associations(request.user, row) == 'faculty'})


@login_required
def download(request, pk, kind, item_id):
    row = get_object_or_404(Workspace, pk=pk)
    role = services.associations(request.user, row)
    if kind == 'material':
        obj = get_object_or_404(Material, pk=item_id, workspace=row)
        if role != 'faculty' and obj.state != 'published':
            raise Http404()
    elif kind == 'assignment':
        obj = get_object_or_404(Assignment, pk=item_id, workspace=row)
        if role == 'observer' or (role == 'student' and obj.state != 'published'):
            raise Http404()
        if not obj.file:
            response = HttpResponse(obj.instructions, content_type='text/plain; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="assignment.txt"'
            return response
    elif kind == 'submission':
        obj = get_object_or_404(Submission, pk=item_id, assignment__workspace=row)
        if role == 'observer' or (role == 'student' and obj.student_id != request.user.pk):
            raise Http404()
    else:
        raise Http404()
    if not obj.file:
        raise Http404()
    return FileResponse(obj.file.open('rb'), as_attachment=True, filename='course-file')
