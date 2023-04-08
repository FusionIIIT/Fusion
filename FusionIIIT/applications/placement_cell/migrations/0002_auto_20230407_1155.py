# Generated by Django 3.1.5 on 2023-04-07 11:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academic_information', '0002_student_hall_id'),
        ('placement_cell', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='placementrecord',
            name='unique_id',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='academic_information.student'),
        ),
    ]
