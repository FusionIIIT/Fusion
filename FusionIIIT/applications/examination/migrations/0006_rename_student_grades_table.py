"""Rename the grades table to examination_student_grades.

examination/0005 moved Student_grades from online_cms to examination while
keeping the table online_cms created. This gives the table its examination
name. In PostgreSQL a table rename only changes the name: every row,
column, index, constraint and the id sequence stay as they are.

Anything that names the table directly must use the new name, for example
the Fusion System Administrator's unmanaged StudentGrade model.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('examination', '0005_student_grades'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='student_grades',
            table='examination_student_grades',
        ),
    ]
