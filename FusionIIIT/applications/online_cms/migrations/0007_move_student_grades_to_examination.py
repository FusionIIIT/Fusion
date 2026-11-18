"""Student_grades now belongs to examination (examination/0005).

This removes the model from online_cms's side only. The table
online_cms_student_grades and all its rows are left exactly as they are.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('online_cms', '0006_student_grades_roll_no_index'),
        ('examination', '0005_student_grades'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name='Student_grades'),
            ],
            database_operations=[],
        ),
    ]
