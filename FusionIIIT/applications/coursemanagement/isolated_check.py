import ast
import os
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
from django.conf import settings
settings.configure(SECRET_KEY='isolated-local-check-only', USE_TZ=False,
    DEFAULT_AUTO_FIELD='django.db.models.AutoField',
    MEDIA_ROOT=str(Path(os.environ.get('TEMP', '/tmp')) / 'lms-isolated-check'),
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    INSTALLED_APPS=['django.contrib.auth', 'django.contrib.contenttypes', 'applications.coursemanagement'],
    TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[str(root/'templates')], 'APP_DIRS':True}])
import django
django.setup()
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.template import engines
from applications.coursemanagement import forms, services
from applications.coursemanagement.models import Assignment, Material, Submission, Workspace, GradeAudit

for path in (root / 'applications' / 'coursemanagement').rglob('*.py'):
    ast.parse(path.read_text(encoding='utf-8'), feature_version=8)
print('Python 3.8 grammar: passed')
call_command('makemigrations', 'coursemanagement', check=True, dry_run=True, verbosity=1)
call_command('migrate', interactive=False, verbosity=0)
call_command('check', verbosity=1)
call_command('makemigrations', 'coursemanagement', check=True, dry_run=True, verbosity=1)
for template in ('lms_index.html', 'lms_form.html', 'lms_workspace.html'):
    engines['django'].get_template('coursemanagement/' + template)
print('Three LMS templates: parsed successfully')
user = get_user_model().objects.create_user(username='localcheck')
space = Workspace.objects.create(course_id=1, year=2026, semester_type='Odd Semester')
now = timezone.now()
assignment = Assignment.objects.create(workspace=space, title='Example', instructions='Work',
    submission_type='text', points_possible=10, due_at=now+timedelta(days=1), state='published')
form = forms.SubmissionForm(data={'text': 'Answer'})
assert form.is_valid(), form.errors
with patch.object(services, 'require_role', return_value='student'):
    submission = services.submit(user, assignment, form)
    try:
        services.submit(user, assignment, form)
        raise AssertionError('Resubmission should remain unresolved')
    except ValidationError:
        pass
with patch.object(services, 'require_role', return_value='faculty'):
    submission = services.grade(user, submission, {'revision':1, 'points':Decimal('8'), 'feedback':'Good'})
    assert not submission.released
    submission = services.grade(user, submission, {'revision':2}, release=True)
    assert submission.released and GradeAudit.objects.count() == 2
    try:
        services.grade(user, submission, {'revision':3, 'points':Decimal('9'), 'feedback':'Changed'})
        raise AssertionError('Post-release policy should remain unresolved')
    except ValidationError:
        pass
Material.objects.create(workspace=space, title='Scheduled', kind='text', text='Note',
                        state='scheduled', release_at=now-timedelta(minutes=1))
assert services.release_due() == 1
assert services.release_due() == 0
invalid = forms.AssignmentForm(data={'title':'Bad', 'instructions':'Work', 'submission_type':'text',
    'points_possible':'-1', 'due_at':now.isoformat()})
assert not invalid.is_valid()
print('Isolated smoke checks: submission, unresolved resubmission, draft/released grade, audit, unresolved post-release edit, scheduled release replay, invalid points: passed')
print('LIMIT: checks used Django ' + django.get_version() + ' with SQLite and patched course authorization; full legacy Django 3.1/PostgreSQL integration was not run.')
