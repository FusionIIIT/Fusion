# Generated by Django 3.1.5 on 2024-04-18 13:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('academic_information', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='grade',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student', models.CharField(max_length=20)),
                ('curriculum', models.CharField(max_length=50)),
                ('semester_id', models.CharField(default='', max_length=10)),
                ('grade', models.CharField(default='B', max_length=5)),
            ],
        ),
        migrations.CreateModel(
            name='hidden_grades',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_id', models.CharField(max_length=20)),
                ('course_id', models.CharField(max_length=50)),
                ('semester_id', models.CharField(max_length=10)),
                ('grade', models.CharField(max_length=5)),
            ],
        ),
        migrations.CreateModel(
            name='authentication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('authenticator_1', models.BooleanField(default=False)),
                ('authenticator_2', models.BooleanField(default=False)),
                ('authenticator_3', models.BooleanField(default=False)),
                ('year', models.DateField(auto_now_add=True)),
                ('course_year', models.IntegerField(default=2024)),
                ('course_id', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='academic_information.course')),
            ],
        ),
    ]
