from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('scholarships', '0002_auto_20250201_2228'),
    ]

    operations = [
        migrations.AlterField(
            model_name='previous_winner',
            name='year',
            field=models.IntegerField(default=2026),
        ),
    ]
