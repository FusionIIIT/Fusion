# Generated by Django 3.1.5 on 2024-04-20 19:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academic_information', '0001_initial'),
        ('online_cms', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Student_grades',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('semester', models.IntegerField(default=1)),
                ('year', models.IntegerField(default=2016)),
                ('roll_no', models.TextField(max_length=2000)),
                ('total_marks', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('grade', models.TextField(max_length=2000)),
                ('batch', models.TextField(max_length=2000)),
                ('course_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic_information.course')),
            ],
        ),
    ]
