from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('placement_cell', '0002_frontend_api_models'),
    ]

    operations = [
        migrations.AlterField(
            model_name='education',
            name='grade',
            field=models.CharField(default='', max_length=10),
        ),
        migrations.AlterField(
            model_name='has',
            name='skill_rating',
            field=models.IntegerField(
                default=80,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(100),
                ],
            ),
        ),
    ]
