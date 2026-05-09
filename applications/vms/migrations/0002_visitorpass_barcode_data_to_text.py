from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vms", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="visitorpass",
            name="barcode_data",
            field=models.TextField(blank=True),
        ),
    ]
