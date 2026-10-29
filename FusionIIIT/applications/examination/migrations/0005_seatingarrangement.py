from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('examination', '0004_auto_20260625_1637'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExamRoom',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('room_no', models.CharField(max_length=20, unique=True)),
                ('seating_capacity', models.PositiveIntegerField(default=45)),
                ('block', models.CharField(blank=True, max_length=10)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['room_no'],
            },
        ),
        migrations.CreateModel(
            name='SeatingArrangement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exam_title', models.CharField(choices=[('midsem', 'Mid-Sem'), ('endsem', 'End-Sem')], max_length=20)),
                ('exam_date', models.DateField()),
                ('shift', models.CharField(choices=[('morning', 'Morning (9:00 AM)'), ('afternoon', 'Afternoon (2:00 PM)')], max_length=20)),
                ('academic_year', models.CharField(max_length=10)),
                ('programme_type', models.CharField(choices=[('UG', 'Undergraduate'), ('PG', 'Postgraduate'), ('PHD', 'PhD'), ('ALL', 'All')], default='ALL', max_length=10)),
                ('course_code', models.CharField(max_length=20)),
                ('course_name', models.CharField(max_length=200)),
                ('room_no', models.CharField(max_length=20)),
                ('student_roll', models.CharField(max_length=20)),
                ('student_name', models.CharField(max_length=200)),
                ('seat_no', models.PositiveIntegerField()),
                ('is_excluded', models.BooleanField(default=False)),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['exam_date', 'shift', 'room_no', 'seat_no'],
            },
        ),
        migrations.AddConstraint(
            model_name='seatingarrangement',
            constraint=models.UniqueConstraint(
                fields=['exam_date', 'shift', 'room_no', 'seat_no'],
                name='unique_seat_per_slot',
            ),
        ),
    ]
