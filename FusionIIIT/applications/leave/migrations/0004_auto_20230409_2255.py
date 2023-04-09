# Generated by Django 3.1.5 on 2023-04-09 22:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leave', '0003_auto_20230326_1630'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='leavescount',
            name='leave_type',
        ),
        migrations.RemoveField(
            model_name='leavescount',
            name='remaining_leaves',
        ),
        migrations.AddField(
            model_name='leavescount',
            name='casual',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='leavescount',
            name='medical',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='leavescount',
            name='special',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='leavescount',
            name='vacational',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='leavescount',
            name='year',
            field=models.IntegerField(default=2023),
        ),
    ]
