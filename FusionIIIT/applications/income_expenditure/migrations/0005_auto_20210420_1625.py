# Generated by Django 3.1.5 on 2021-04-20 16:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('income_expenditure', '0004_auto_20210420_1620'),
    ]

    operations = [
        migrations.AlterField(
            model_name='income',
            name='date_added',
            field=models.DateField(),
        ),
    ]
