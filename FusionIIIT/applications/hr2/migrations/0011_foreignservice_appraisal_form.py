# Generated by Django 3.1.5 on 2021-03-31 22:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr2', '0010_auto_20210330_1413'),
    ]

    operations = [
        migrations.AddField(
            model_name='foreignservice',
            name='appraisal_form',
            field=models.FileField(blank=True, null=True, upload_to=''),
        ),
    ]
