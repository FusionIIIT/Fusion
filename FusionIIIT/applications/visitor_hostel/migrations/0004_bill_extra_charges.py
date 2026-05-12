from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visitor_hostel', '0003_inventory_threshold_replenishment'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='extra_charges',
            field=models.IntegerField(default=0),
        ),
    ]
