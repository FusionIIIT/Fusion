# Generated by Django 3.1.5 on 2021-04-21 13:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('central_mess', '0019_auto_20210303_2238'),
    ]

    operations = [
        migrations.AlterField(
            model_name='monthly_bill',
            name='month',
            field=models.CharField(default=4, max_length=20),
        ),
    ]
