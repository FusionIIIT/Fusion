from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr2', '0007_half_day_cl'),
    ]

    operations = [
        migrations.AlterField(
            model_name='leaveapplicationnew',
            name='station_leave',
            field=models.CharField(
                blank=True,
                choices=[('WITH', 'With Station Leave'), ('WITHOUT', 'Without Station Leave'), ('NOT_REQUIRED', 'Not Required')],
                max_length=12,
            ),
        ),
    ]
