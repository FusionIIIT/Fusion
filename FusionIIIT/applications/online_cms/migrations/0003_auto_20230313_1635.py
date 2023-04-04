# Generated by Django 3.1.5 on 2023-03-13 16:35

import applications.online_cms.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('online_cms', '0002_courseassignment_courseslide'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studentassignment',
            name='upload_url',
        ),
        migrations.AddField(
            model_name='studentassignment',
            name='doc',
            field=models.FileField(blank=True, null=True, upload_to=applications.online_cms.models.assignment_submit_name),
        ),
        migrations.AlterField(
            model_name='studentassignment',
            name='assignment_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='online_cms.courseassignment'),
        ),
    ]
