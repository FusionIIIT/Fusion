from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr2', '0005_leave_extension'),
    ]

    operations = [
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='station_leave',
            field=models.CharField(
                blank=True,
                choices=[('WITH', 'With Station Leave'), ('WITHOUT', 'Without Station Leave')],
                max_length=10,
            ),
        ),
    ]
