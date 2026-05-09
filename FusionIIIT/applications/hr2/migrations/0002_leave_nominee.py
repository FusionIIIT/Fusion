from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr2', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='leaveapplicationnew',
            name='handover_to',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='nominee_status',
            field=models.CharField(choices=[('NOT_REQUIRED', 'Not Required'), ('PENDING', 'Pending'), ('ACCEPTED', 'Accepted'), ('DECLINED', 'Declined')], default='NOT_REQUIRED', max_length=20),
        ),
        migrations.AddField(
            model_name='leaveapplicationnew',
            name='nominee_responded_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
