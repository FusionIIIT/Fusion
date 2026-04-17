from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr2', '0003_add_missing_hr2_leavebalance_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='leavebalance',
            name='casual_leave_allotted',
            field=models.PositiveIntegerField(default=15),
        ),
        migrations.AddField(
            model_name='leavebalance',
            name='casual_leave_used',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='leavebalance',
            name='special_casual_leave_allotted',
            field=models.PositiveIntegerField(default=7),
        ),
        migrations.AddField(
            model_name='leavebalance',
            name='special_casual_leave_used',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='leavebalance',
            name='earned_leave_allotted',
            field=models.PositiveIntegerField(default=30),
        ),
        migrations.AddField(
            model_name='leavebalance',
            name='earned_leave_used',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='leavebalance',
            name='commuted_leave_allotted',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='leavebalance',
            name='commuted_leave_used',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='leavebalance',
            name='restricted_holiday_allotted',
            field=models.PositiveIntegerField(default=2),
        ),
        migrations.AddField(
            model_name='leavebalance',
            name='restricted_holiday_used',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='leavebalance',
            name='station_leave_allotted',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='leavebalance',
            name='station_leave_used',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='leavebalance',
            name='vacation_leave_allotted',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='leavebalance',
            name='vacation_leave_used',
            field=models.PositiveIntegerField(default=0),
        ),
    ]