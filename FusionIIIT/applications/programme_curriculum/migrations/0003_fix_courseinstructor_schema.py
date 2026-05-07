# Generated migration to fix CourseInstructor schema

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('programme_curriculum', '0002_auto_20260326_0127'),
    ]

    operations = [
        # Add the batch_id field to CourseInstructor
        migrations.AddField(
            model_name='courseinstructor',
            name='batch_id',
            field=models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, to='programme_curriculum.batch'),
        ),
    ]
