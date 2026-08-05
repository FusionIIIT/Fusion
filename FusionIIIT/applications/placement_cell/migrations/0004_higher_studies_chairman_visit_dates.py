import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('placement_cell', '0003_assignment7_requirement_fixes'),
    ]

    operations = [
        migrations.AddField(
            model_name='chairmanvisit',
            name='start_date',
            field=models.DateField(default=datetime.date.today, verbose_name='Start Date'),
        ),
        migrations.AddField(
            model_name='chairmanvisit',
            name='end_date',
            field=models.DateField(blank=True, null=True, verbose_name='End Date'),
        ),
    ]
