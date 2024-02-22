# Generated by Django 3.1.5 on 2024-02-18 04:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('health_center', '0003_auto_20240218_0427'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='doctor',
            name='id',
        ),
        migrations.RemoveField(
            model_name='pathologist',
            name='id',
        ),
        migrations.RemoveField(
            model_name='schedule',
            name='id',
        ),
        migrations.AddField(
            model_name='doctor',
            name='doctor_id',
            field=models.CharField(default=1, max_length=100, primary_key=True, serialize=False),
        ),
        migrations.AddField(
            model_name='pathologist',
            name='pathologist_id',
            field=models.CharField(default=1, max_length=100, primary_key=True, serialize=False),
        ),
        migrations.AddField(
            model_name='schedule',
            name='schedule_id',
            field=models.CharField(default=1, max_length=100, primary_key=True, serialize=False),
        ),
    ]
