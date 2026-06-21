from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("placement_cell", "0007_reporting_features"),
    ]

    operations = [
        migrations.AddField(
            model_name="placementround",
            name="end_datetime",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="placementround",
            name="location_link",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="placementround",
            name="mode",
            field=models.CharField(blank=True, default="", max_length=30),
        ),
        migrations.AddField(
            model_name="placementround",
            name="start_datetime",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
