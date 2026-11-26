"""Migration 0061: Whole-College Timetable Generation System

Creates the seven new additive tables:
  timetable_classroom
  timetable_course_weekly_requirement
  timetable_version
  timetable_slot
  timetable_elective_basket
  timetable_elective_basket_curriculum
  timetable_faculty_preference
  timetable_conflict_log

Zero changes are made to existing production tables.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academic_procedures', '0060_demandletterbankaccounts'),
        ('academic_information', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [

        # ------------------------------------------------------------------ #
        # 1. Classroom                                                        #
        # ------------------------------------------------------------------ #
        migrations.CreateModel(
            name='Classroom',
            fields=[
                ('room_id', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('building', models.CharField(max_length=100)),
                ('capacity', models.PositiveIntegerField(help_text='Seating capacity (hard seats)')),
                ('room_type', models.CharField(
                    max_length=30,
                    choices=[
                        ('Lecture Hall', 'Lecture Hall'),
                        ('Tutorial Room', 'Tutorial Room'),
                        ('Computer Lab', 'Computer Lab'),
                        ('Hardware Lab', 'Hardware Lab'),
                        ('Mechanical Workshop', 'Mechanical Workshop'),
                        ('Seminar Room', 'Seminar Room'),
                    ],
                )),
                ('has_projector', models.BooleanField(default=True)),
                ('is_active', models.BooleanField(
                    default=True,
                    help_text='Set False during maintenance to exclude from scheduling',
                )),
            ],
            options={'db_table': 'timetable_classroom', 'ordering': ['room_id']},
        ),

        # ------------------------------------------------------------------ #
        # 2. TimetableVersion                                                 #
        # ------------------------------------------------------------------ #
        migrations.CreateModel(
            name='TimetableVersion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('academic_year', models.PositiveSmallIntegerField(
                    help_text='Start year of the academic year, e.g. 2026 for 2026-27',
                )),
                ('semester_type', models.CharField(
                    max_length=20,
                    choices=[
                        ('Odd Semester', 'Odd Semester'),
                        ('Even Semester', 'Even Semester'),
                        ('Summer Term', 'Summer Term'),
                    ],
                )),
                ('version_number', models.PositiveSmallIntegerField(default=1)),
                ('status', models.CharField(
                    max_length=15,
                    default='Draft',
                    choices=[
                        ('Draft', 'Draft'),
                        ('UnderReview', 'Under Review'),
                        ('Approved', 'Approved'),
                        ('Published', 'Published'),
                        ('Archived', 'Archived'),
                        ('Infeasible', 'Infeasible'),
                    ],
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='timetable_versions_created',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('solve_time_seconds', models.FloatField(blank=True, null=True)),
                ('slots_created', models.PositiveIntegerField(blank=True, null=True)),
                ('remarks', models.TextField(blank=True)),
                ('publish_notes', models.TextField(blank=True)),
            ],
            options={
                'db_table': 'timetable_version',
                'ordering': ['-academic_year', '-version_number'],
            },
        ),
        migrations.AddConstraint(
            model_name='timetableversion',
            constraint=models.UniqueConstraint(
                fields=['academic_year', 'semester_type', 'version_number'],
                name='unique_timetable_version',
            ),
        ),

        # ------------------------------------------------------------------ #
        # 3. TimetableSlot                                                    #
        # ------------------------------------------------------------------ #
        migrations.CreateModel(
            name='TimetableSlot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='slots',
                    to='academic_procedures.TimetableVersion',
                )),
                ('curriculum', models.ForeignKey(
                    db_column='curriculum_id',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='timetable_slots',
                    to='academic_information.Curriculum',
                )),
                ('curriculum_instructor', models.ForeignKey(
                    blank=True,
                    db_column='curriculum_instructor_id',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='timetable_slots',
                    to='academic_information.Curriculum_Instructor',
                )),
                ('classroom', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='timetable_slots',
                    to='academic_procedures.Classroom',
                )),
                ('batch', models.PositiveSmallIntegerField(help_text='Admission year of the cohort')),
                ('programme', models.CharField(max_length=15)),
                ('branch', models.CharField(max_length=15)),
                ('section', models.CharField(blank=True, default='', max_length=8)),
                ('day_of_week', models.PositiveSmallIntegerField(
                    choices=[(1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'), (4, 'Thursday'), (5, 'Friday')],
                )),
                ('start_hour', models.PositiveSmallIntegerField(
                    choices=[
                        (9, '09:00\u201310:00'), (10, '10:00\u201311:00'),
                        (11, '11:00\u201312:00'), (12, '12:00\u201313:00'),
                        (14, '14:00\u201315:00'), (15, '15:00\u201316:00'),
                        (16, '16:00\u201317:00'), (17, '17:00\u201318:00'),
                    ],
                    help_text='Hour of the day (24-h), e.g. 9 means 09:00',
                )),
                ('slot_type', models.CharField(
                    max_length=15,
                    choices=[('Lecture', 'Lecture'), ('Tutorial', 'Tutorial'), ('Practical', 'Practical')],
                )),
                ('lab_block_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('is_locked', models.BooleanField(
                    default=False,
                    help_text='Locked slots are preserved as-is in subsequent solver runs',
                )),
            ],
            options={'db_table': 'timetable_slot'},
        ),
        migrations.AddIndex(
            model_name='timetableslot',
            index=models.Index(
                fields=['version', 'batch', 'programme', 'branch', 'section'],
                name='tt_slot_cohort_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='timetableslot',
            index=models.Index(
                fields=['version', 'curriculum_instructor', 'day_of_week', 'start_hour'],
                name='tt_slot_faculty_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='timetableslot',
            index=models.Index(
                fields=['version', 'classroom', 'day_of_week', 'start_hour'],
                name='tt_slot_room_idx',
            ),
        ),

        # ------------------------------------------------------------------ #
        # 4. CourseWeeklyRequirement                                          #
        # ------------------------------------------------------------------ #
        migrations.CreateModel(
            name='CourseWeeklyRequirement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('curriculum', models.ForeignKey(
                    db_column='curriculum_id',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='weekly_requirements',
                    to='academic_information.Curriculum',
                )),
                ('lectures_per_week', models.PositiveSmallIntegerField(default=3)),
                ('tutorials_per_week', models.PositiveSmallIntegerField(default=1)),
                ('practicals_per_week', models.PositiveSmallIntegerField(default=0)),
                ('practical_block_size', models.PositiveSmallIntegerField(
                    default=2,
                    help_text='Consecutive hours for one lab session (2 or 3)',
                )),
                ('preferred_room_type', models.CharField(
                    max_length=30,
                    default='any',
                    choices=[
                        ('any', 'Any'),
                        ('Lecture Hall', 'Lecture Hall'),
                        ('Tutorial Room', 'Tutorial Room'),
                        ('Computer Lab', 'Computer Lab'),
                        ('Hardware Lab', 'Hardware Lab'),
                        ('Mechanical Workshop', 'Mechanical Workshop'),
                    ],
                )),
            ],
            options={'db_table': 'timetable_course_weekly_requirement'},
        ),
        migrations.AlterUniqueTogether(
            name='courseweeklyrequirement',
            unique_together={('curriculum',)},
        ),

        # ------------------------------------------------------------------ #
        # 5. ElectiveBasket + ElectiveBasketCurriculum                        #
        # ------------------------------------------------------------------ #
        migrations.CreateModel(
            name='ElectiveBasket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('basket_code', models.CharField(max_length=20, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('semester', models.PositiveSmallIntegerField()),
                ('programme', models.CharField(max_length=15)),
                ('academic_year', models.PositiveSmallIntegerField(default=2026)),
                ('semester_type', models.CharField(
                    max_length=20,
                    default='Odd Semester',
                    choices=[
                        ('Odd Semester', 'Odd Semester'),
                        ('Even Semester', 'Even Semester'),
                        ('Summer Term', 'Summer Term'),
                    ],
                )),
            ],
            options={'db_table': 'timetable_elective_basket', 'ordering': ['basket_code']},
        ),
        migrations.CreateModel(
            name='ElectiveBasketCurriculum',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('basket', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='academic_procedures.ElectiveBasket',
                )),
                ('curriculum', models.ForeignKey(
                    db_column='curriculum_id',
                    on_delete=django.db.models.deletion.CASCADE,
                    to='academic_information.Curriculum',
                )),
                ('max_seats', models.PositiveSmallIntegerField(
                    default=60,
                    help_text='Expected enrollment cap for room-sizing',
                )),
            ],
            options={'db_table': 'timetable_elective_basket_curriculum'},
        ),
        migrations.AlterUniqueTogether(
            name='electivebasketcurriculum',
            unique_together={('basket', 'curriculum')},
        ),
        # Wire up M2M through ElectiveBasketCurriculum
        migrations.AddField(
            model_name='electivebasket',
            name='curricula',
            field=models.ManyToManyField(
                related_name='elective_baskets',
                through='academic_procedures.ElectiveBasketCurriculum',
                to='academic_information.Curriculum',
            ),
        ),

        # ------------------------------------------------------------------ #
        # 6. FacultyPreference                                                #
        # ------------------------------------------------------------------ #
        migrations.CreateModel(
            name='FacultyPreference',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('faculty', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='timetable_preferences',
                    to='globals.Faculty',
                )),
                ('academic_year', models.PositiveSmallIntegerField(default=2026)),
                ('semester_type', models.CharField(
                    max_length=20,
                    default='Odd Semester',
                    choices=[
                        ('Odd Semester', 'Odd Semester'),
                        ('Even Semester', 'Even Semester'),
                        ('Summer Term', 'Summer Term'),
                    ],
                )),
                ('day_of_week', models.PositiveSmallIntegerField(
                    choices=[(1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'), (4, 'Thursday'), (5, 'Friday')],
                )),
                ('start_hour', models.PositiveSmallIntegerField(
                    choices=[
                        (9, '09:00\u201310:00'), (10, '10:00\u201311:00'),
                        (11, '11:00\u201312:00'), (12, '12:00\u201313:00'),
                        (14, '14:00\u201315:00'), (15, '15:00\u201316:00'),
                        (16, '16:00\u201317:00'), (17, '17:00\u201318:00'),
                    ],
                )),
                ('end_hour', models.PositiveSmallIntegerField(
                    choices=[
                        (9, '09:00\u201310:00'), (10, '10:00\u201311:00'),
                        (11, '11:00\u201312:00'), (12, '12:00\u201313:00'),
                        (14, '14:00\u201315:00'), (15, '15:00\u201316:00'),
                        (16, '16:00\u201317:00'), (17, '17:00\u201318:00'),
                    ],
                )),
                ('preference_type', models.CharField(
                    max_length=15,
                    choices=[('Unavailable', 'Unavailable'), ('Preferred', 'Preferred')],
                )),
                ('reason', models.TextField(blank=True)),
            ],
            options={
                'db_table': 'timetable_faculty_preference',
                'ordering': ['faculty', 'day_of_week', 'start_hour'],
            },
        ),

        # ------------------------------------------------------------------ #
        # 7. TimetableConflictLog                                             #
        # ------------------------------------------------------------------ #
        migrations.CreateModel(
            name='TimetableConflictLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='conflict_logs',
                    to='academic_procedures.TimetableVersion',
                )),
                ('severity', models.CharField(
                    max_length=10,
                    choices=[('CRITICAL', 'Critical'), ('WARNING', 'Warning'), ('INFO', 'Info')],
                )),
                ('error_code', models.CharField(max_length=30)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('curriculum_id_ref', models.IntegerField(blank=True, null=True)),
                ('classroom_id_ref', models.CharField(blank=True, max_length=20, null=True)),
                ('faculty_id_ref', models.CharField(blank=True, max_length=20, null=True)),
            ],
            options={
                'db_table': 'timetable_conflict_log',
                'ordering': ['-created_at', '-severity'],
            },
        ),
    ]
