from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('globals', '0004_extrainfo_last_selected_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='moduleaccess',
            name='database',
            field=models.BooleanField(default=False),
        ),
    ]
