# Generated by Django 3.1.5 on 2023-01-27 16:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('globals', '0003_auto_20230127_1556'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extrainfo',
            name='user_status',
            field=models.CharField(choices=[('PRESENT', 'PRESENT'), ('NEW', 'NEW')], default='PRESENT', max_length=50),
        ),
    ]
