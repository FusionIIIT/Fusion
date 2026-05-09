# Generated manually for UC-003 special food validation completion.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('central_mess', '0003_menu_polls'),
    ]

    operations = [
        migrations.AddField(
            model_name='special_request',
            name='request_type',
            field=models.CharField(
                choices=[('medical', 'Medical'), ('event', 'Event')],
                default='event',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='special_request',
            name='semester',
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='special_request',
            name='supporting_document',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to='central_mess/special_requests/',
            ),
        ),
    ]
