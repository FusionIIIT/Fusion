from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academic_procedures', '0052_course_registration_term_unique'),
    ]

    operations = [
        migrations.AddField(
            model_name='bonafidecertificate',
            name='pdf_content',
            field=models.BinaryField(
                blank=True, editable=False, null=True),
        ),
    ]
