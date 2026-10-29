from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('globals', '0015_fix_basic_designation_update_trigger'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='holdsdesignation',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='holdsdesignation',
            constraint=models.UniqueConstraint(
                fields=('user', 'designation'),
                condition=Q(end_time__isnull=True),
                name='globals_hold_user_role_open_uniq',
            ),
        ),
        migrations.AddConstraint(
            model_name='holdsdesignation',
            constraint=models.UniqueConstraint(
                fields=('working', 'designation'),
                condition=Q(end_time__isnull=True),
                name='globals_hold_working_role_open_uniq',
            ),
        ),
    ]
