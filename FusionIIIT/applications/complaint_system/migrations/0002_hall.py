# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-03-03 16:54
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('globals', '0003_auto_20191024_1242'),
        ('complaint_system', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Hall',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', models.CharField(choices=[('hall-1', 'hall-1'), ('hall-3', 'hall-3'), ('hall-4', 'hall-4'), ('CC1', 'CC1'), ('CC2', 'CC2'), ('core_lab', 'core_lab'), ('LHTC', 'LHTC'), ('NR2', 'NR2'), ('Rewa_Residency', 'Rewa_Residency')], default='hall-3', max_length=20)),
                ('designation_name', models.CharField(choices=[('hall1caretaker', 'hall1caretaker'), ('hall3caretaker', 'hall3caretaker'), ('hall4caretaker', 'hall4caretaker'), ('cc1convener', 'cc1convener'), ('CC2 convener', 'CC2 convener'), ('corelabcaretaker', 'corelabcaretaker')], default='hall3caretaker', max_length=20)),
                ('staff_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='globals.ExtraInfo')),
            ],
        ),
    ]
