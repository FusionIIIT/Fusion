from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr2', '0006_station_leave_selection'),
    ]

    operations = [
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='is_half_day',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='half_day_slot',
            field=models.CharField(
                blank=True,
                choices=[('AM', 'AM'), ('PM', 'PM')],
                max_length=2,
            ),
        ),
    ]
