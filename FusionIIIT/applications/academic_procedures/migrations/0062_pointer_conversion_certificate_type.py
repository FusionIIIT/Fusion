from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academic_procedures', '0061_alter_bonafidecertificate_certificate_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bonafidecertificate',
            name='certificate_type',
            field=models.CharField(
                choices=[
                    ('bonafide', 'Bonafide Certificate'),
                    ('fee', 'Paid / Unpaid Fee Certificate'),
                    ('demand', 'Demand Letter'),
                    ('fee_structure', 'Fee Structure Certificate'),
                    ('medium_of_instruction', 'Medium of Instruction Certificate'),
                    ('pointer_conv', 'Pointer Conversion Certificate'),
                ],
                db_index=True,
                default='bonafide',
                max_length=32,
            ),
        ),
    ]
