# Generated by Django 3.1.5 on 2021-05-12 16:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('globals', '0008_auto_20210511_0944'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extrainfo',
            name='user_status',
            field=models.CharField(choices=[('NEW', 'NEW'), ('PRESENT', 'PRESENT')], default='PRESENT', max_length=50),
        ),
    ]
