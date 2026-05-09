"""BR-046: Add vip_level to Visit for escort-assignment eligibility."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vms", "0003_extended_vms_models"),
    ]

    operations = [
        migrations.AddField(
            model_name="visit",
            name="vip_level",
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
