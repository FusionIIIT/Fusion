# Generated by Django 3.1.5 on 2024-03-18 12:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('health_center', '0015_auto_20240222_0238'),
    ]

    operations = [
        migrations.CreateModel(
            name='MedicalRelief',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='')),
                ('description', models.CharField(max_length=500)),
            ],
        ),
    ]
