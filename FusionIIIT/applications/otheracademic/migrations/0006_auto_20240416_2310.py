# Generated by Django 3.1.5 on 2024-04-16 23:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('otheracademic', '0005_auto_20240416_2245'),
    ]

    operations = [
      
        migrations.AlterField(
            model_name='leavepg',
            name='upload_file',
            field=models.FileField(blank=True, upload_to=''),
        ),
    ]