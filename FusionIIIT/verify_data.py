
import os
import django
import sys

# Add the project root to sys.path
sys.path.append('/Users/hemangmishra/Projects/Fusion/FusionIIIT')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings')
django.setup()

from django.contrib.auth.models import User
from applications.academic_information.models import Student
from applications.placement_cell.models import (
    Company, JobPosting, JobApplication, InterviewSchedule, JobOffer, Announcement
)

print("-" * 30)
print("DATA VERIFICATION REPORT")
print("-" * 30)
print(f"Users: {User.objects.count()}")
print(f"Students: {Student.objects.count()}")
print(f"Companies: {Company.objects.count()}")
print(f"Job Postings: {JobPosting.objects.count()}")
print(f"Applications: {JobApplication.objects.count()}")
print(f"Interviews: {InterviewSchedule.objects.count()}")
print(f"Offers: {JobOffer.objects.count()}")
print(f"Announcements: {Announcement.objects.count()}")

# List some student usernames/passwords (if known) for login testing
print("\n" + "-" * 30)
print("SAMPLE LOGIN CREDENTIALS")
print("-" * 30)
users = User.objects.filter(username__startswith='student')[:5]
if users:
    print("Student Users (Password set to 'password123' in script):")
    for u in users:
        print(f" - Username: {u.username} | Email: {u.email}")
else:
    print("No student users found.")

tpo = User.objects.filter(username='tpo_admin').first()
if tpo:
    print(f"\nTPO User (Password set to 'password' in script):")
    print(f" - Username: {tpo.username} | Email: {tpo.email}")
else:
    print("\nTPO user 'tpo_admin' not found.")
print("-" * 30)

