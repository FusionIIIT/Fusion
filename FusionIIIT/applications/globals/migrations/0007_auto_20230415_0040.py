# Generated by Django 3.1.5 on 2023-04-15 00:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('globals', '0006_auto_20230409_2255'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extrainfo',
            name='user_status',
            field=models.CharField(choices=[('NEW', 'NEW'), ('PRESENT', 'PRESENT')], default='PRESENT', max_length=50),
        ),
    ]
