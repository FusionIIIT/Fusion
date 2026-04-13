from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr2', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='leaveform',
            name='leave_pdf_file',
            field=models.FileField(upload_to='Hr2/leave_pdfs', null=True, blank=True),
        ),
    ]
