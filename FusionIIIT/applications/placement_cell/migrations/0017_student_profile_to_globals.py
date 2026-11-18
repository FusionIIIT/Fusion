"""The student profile models now belong to globals (globals/0013).

This removes them from placement_cell's side only, and points Coauthor and
Coinventor, which stay in placement_cell, at the globals Publication and
Patent. The ten tables, their rows and the database foreign keys are left
exactly as they are.
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('placement_cell', '0016_studentbankdetails'),
        ('globals', '0013_student_profile_from_placement_cell'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='coauthor',
                    name='publication_id',
                    field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='globals.publication'),
                ),
                migrations.AlterField(
                    model_name='coinventor',
                    name='patent_id',
                    field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='globals.patent'),
                ),
                migrations.DeleteModel(name='Has'),
                migrations.DeleteModel(name='Skill'),
                migrations.DeleteModel(name='Education'),
                migrations.DeleteModel(name='Experience'),
                migrations.DeleteModel(name='Project'),
                migrations.DeleteModel(name='Course'),
                migrations.DeleteModel(name='Publication'),
                migrations.DeleteModel(name='Patent'),
                migrations.DeleteModel(name='Achievement'),
                migrations.DeleteModel(name='StudentBankDetails'),
            ],
            database_operations=[],
        ),
    ]
