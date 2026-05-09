import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'Fusion.settings.development'
django.setup()

from applications.academic_information.models import Student
from django.contrib.auth.models import User

students = (
    Student.objects
    .filter(batch=2023)
    .select_related('id__user')
    .order_by('-cpi')
)
dummy = [s for s in students if s.id.user.username.startswith('23')][:20]
print('Roll No         | Name                      | Prog      | CPI  ')
print('-'*70)
for s in dummy:
    u = s.id.user
    name = (u.first_name + ' ' + u.last_name).strip()
    print(f'{u.username:<16}| {name:<26}| {s.programme:<10}| {s.cpi}')

print()
print('PASSWORD for all above: student@123')
print()
# Also check the login API issue - look at auth API views
import subprocess
