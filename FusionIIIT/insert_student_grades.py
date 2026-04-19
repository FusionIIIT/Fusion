import os, django, random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings.development')
django.setup()

from applications.online_cms.models import Student_grades
from applications.programme_curriculum.models import Course

def insert_specific_grades():
    # 1. Clear old grades
    count_deleted, _ = Student_grades.objects.all().delete()
    print(f"Cleared {count_deleted} existing grade records.")

    # 2. Define target roll numbers
    def get_rolls(prefix, start, end, padding=3):
        return [f"{prefix}{str(i).zfill(padding)}" for i in range(start, end + 1)]

    target_rolls = []
    # 23 Batch B.Tech/B.Des
    target_rolls.extend(get_rolls('23BCS', 1, 10, 3))
    target_rolls.extend(get_rolls('23BEC', 1, 10, 3))
    target_rolls.extend(get_rolls('23BSM', 1, 10, 3))
    target_rolls.extend(get_rolls('23BME', 1, 10, 3))
    target_rolls.extend(get_rolls('23BDS', 1, 10, 3))
    
    # 25 Batch M.Tech/M.Des
    target_rolls.extend(get_rolls('25MCSA', 1, 10, 2))
    target_rolls.extend(get_rolls('25MCSS', 1, 10, 2))
    target_rolls.extend(get_rolls('25MDS', 1, 7, 2))

    # 3. Setup courses and grades
    GRADES = ['O', 'A+', 'A', 'B+', 'B', 'C+', 'C']
    courses = list(Course.objects.all()[:10])
    
    if not courses:
        print("Error: No courses found in programme_curriculum_course table.")
        return

    print(f"Inserting grades for {len(target_rolls)} specific students across {len(courses)} courses...")

    to_create = []
    for roll in target_rolls:
        # Determine batch from roll number
        batch = 2023 if roll.startswith('23') else 2025
        
        # Add a mix of courses for each student
        for c in courses:
            to_create.append(
                Student_grades(
                    course_id=c,
                    semester=1,
                    year=batch, # Using batch year as starting year
                    roll_no=roll,
                    grade=random.choice(GRADES),
                    batch=batch,
                    verified=True,
                    academic_year=f'{batch}-{str(batch+1)[2:]}',
                    semester_type='Odd Semester'
                )
            )

    Student_grades.objects.bulk_create(to_create)
    print(f"Successfully inserted {len(to_create)} grade records for demo students.")

if __name__ == '__main__':
    insert_specific_grades()
