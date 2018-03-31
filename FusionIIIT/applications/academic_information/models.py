from django.db import models

from applications.globals.models import ExtraInfo


class Constants:
    HOLIDAY_TYPE = (
        ('restricted', 'restricted'),
        ('closed', 'closed'),
        ('vacation', 'vacation')
    )

    ATTEND_CHOICES = (
        ('present', 'present'),
        ('absent', 'absent')
    )

    PROGRAMME = (
        ('B.Tech', 'B.Tech'),
        ('B.Des', 'B.Des'),
        ('M.Tech', 'M.Tech'),
        ('M.Des', 'M.Des'),
        ('PhD', 'PhD')
    )

    CATEGORY = (
        ('GEN', 'General'),
        ('SC', 'Scheduled Castes'),
        ('ST', 'Scheduled Tribes'),
        ('OBC', 'Other Backward Classes')
    )

    MTechSpecialization = (
        ('Power and Control', 'Power and Control'),
        ('Microwave and Communication Engineering', 'Microwave and Communication Engineering'),
        ('Micro-nano Electronics', 'Micro-nano Electronics'),
        ('CAD/CAM', 'CAD/CAM'),
        ('Design', 'Design'),
        ('Manufacturing', 'Manufacturing'),
        ('CSE', 'CSE'),
        ('Mechatronics', 'Mechatronics'),
        ('MDes', 'MDes'),
        ('None', 'None')
    )


class Student(models.Model):
    id = models.OneToOneField(ExtraInfo, on_delete=models.CASCADE, primary_key=True)
    programme = models.CharField(max_length=10, choices=Constants.PROGRAMME)
    cpi = models.FloatField(default=0)
    category = models.CharField(max_length=10, choices=Constants.CATEGORY, null=False)
    father_name = models.CharField(max_length=40, default='')
    mother_name = models.CharField(max_length=40, default='')
    hall_no = models.IntegerField(default=1)
    room_no = models.CharField(max_length=10, blank=True, null=True)
    specialization = models.CharField(max_length=20,
                                      choices=Constants.MTechSpecialization, null=True)

    def __str__(self):
        return str(self.id)


class Course(models.Model):
    course_id = models.CharField(max_length=100, unique=True)
    course_name = models.CharField(max_length=100)
    sem = models.IntegerField()
    credits = models.IntegerField()
    optional = models.BooleanField(default=False)
    acad_selection = models.BooleanField(default=False)

    class Meta:
        db_table = 'Course'
        unique_together = ('course_id', 'course_name', 'sem')

    def __str__(self):
        return self.course_name


class Meeting(models.Model):
    venue = models.CharField(max_length=50)
    date = models.DateField()
    time = models.CharField(max_length=20)
    agenda = models.TextField()
    minutes_file = models.CharField(max_length=40)

    class Meta:
        db_table = 'Meeting'

    def __str__(self):
        return self.date


class Calendar(models.Model):
    from_date = models.DateField()
    to_date = models.DateField()
    description = models.CharField(max_length=40)

    class Meta:
        db_table = 'Calendar'

    def __str__(self):
        return self.description


class Holiday(models.Model):
    holiday_date = models.DateField()
    holiday_name = models.CharField(max_length=40)
    holiday_type = models.CharField(default='restricted', max_length=30,
                                    choices=Constants.HOLIDAY_TYPE)

    class Meta:
        db_table = 'Holiday'

    def __str__(self):
        return self.holiday_name


class Grades(models.Model):
    student_id = models.ForeignKey(Student)
    course_id = models.ForeignKey(Course)
    sem = models.IntegerField()
    grade = models.CharField(max_length=4)

    class Meta:
        db_table = 'Grades'


class Student_attendance(models.Model):
    student_id = models.ForeignKey(Student)
    course_id = models.ForeignKey(Course)
#    attend = models.CharField(max_length=6, choices=Constants.ATTEND_CHOICES)
    date = models.DateField(auto_now=True)
    present_attend = models.IntegerField(default=0)
    total_attend = models.IntegerField(default=0)

    class Meta:
        db_table = 'Student_attendance'

    def __self__(self):
        return self.course_id


class Instructor(models.Model):
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)
    instructor_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)

    class Meta:
        db_table = 'Instructor'
        unique_together = ('course_id', 'instructor_id')

    def __self__(self):
        return '{} - {}'.format(self.course_id, self.instructor_id)


class Spi(models.Model):
    sem = models.IntegerField()
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    spi = models.FloatField(default=0)

    class Meta:
        db_table = 'Spi'
        unique_together = ('student_id', 'sem')

    def __self__(self):
        return self.sem


class Timetable(models.Model):
    upload_date = models.DateTimeField(auto_now_add=True)
    time_table = models.FileField(upload_to='Administrator/academic_information/')
    year = models.IntegerField(default="2015")
    programme = models.CharField(max_length=30, default="B.Tech")

    class Meta:
        db_table = 'Timetable'


class Exam_timetable(models.Model):
    upload_date = models.DateField(auto_now_add=True)
    exam_time_table = models.FileField(upload_to='Administrator/academic_information/')
    year = models.IntegerField(default="2015")
    programme = models.CharField(max_length=30, default="B.Tech")

    class Meta:
        db_table = 'Exam_Timetable'
