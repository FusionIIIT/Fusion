# Generated by Django 3.1.5 on 2023-03-26 16:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leave', '0002_auto_20230326_1629'),
    ]

    operations = [
        migrations.AlterField(
            model_name='leavetype',
            name='max_in_year',
            field=models.IntegerField(default=15),
        ),
        migrations.AlterField(
            model_name='leavetype',
            name='name',
            field=models.CharField(default='medical', max_length=40),
        ),
    ]
