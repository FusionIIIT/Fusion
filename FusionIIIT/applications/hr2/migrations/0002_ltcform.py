# Generated by Django 3.1.5 on 2024-02-17 17:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr2', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LTCform',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('designation', models.CharField(max_length=50)),
                ('department_info', models.CharField(max_length=20)),
                ('leave_availability', models.BooleanField()),
                ('leave_start_date', models.DateField(blank=True, max_length=6, null=True)),
                ('leave_end_date', models.DateField(blank=True, max_length=6, null=True)),
                ('date_of_leave_for_family', models.DateField(blank=True, max_length=6, null=True)),
                ('nature_of_leave', models.TextField()),
                ('purpose_of_leave', models.TextField()),
                ('hometown_or_not', models.BooleanField()),
                ('place_of_visit', models.CharField(max_length=20, null=True)),
                ('address_during_leave', models.TextField()),
                ('mode_for_vacation', models.TextField()),
                ('details_of_family_members_already_done', models.TextField()),
                ('family_members_about_to_avail', models.CharField(default='self', max_length=30)),
                ('details_of_family_members', models.TextField()),
                ('details_of_dependents', models.TextField()),
                ('amount_of_advance_required', models.IntegerField(null=True)),
                ('certified_family_dependents', models.TextField()),
                ('certified_advance', models.TextField()),
                ('adjusted_month', models.TextField()),
                ('date', models.DateField(max_length=6)),
                ('phone_number_for_contact', models.IntegerField(max_length=10)),
            ],
        ),
    ]
