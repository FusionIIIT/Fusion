from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('examination', '0002_resultannouncement'),
    ]

    operations = [
        migrations.AddField(
            model_name='resultannouncement',
            name='semester_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('Odd Semester', 'Odd Semester'),
                    ('Even Semester', 'Even Semester'),
                    ('Summer Semester', 'Summer Semester'),
                ],
                max_length=20,
                null=True,
            ),
        ),
        migrations.AlterUniqueTogether(
            name='resultannouncement',
            unique_together={('batch', 'semester', 'semester_type')},
        ),
    ]
