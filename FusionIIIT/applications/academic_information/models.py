from django.db import models

from applications.globals.models import ExtraInfo

from applications.programme_curriculum.models import Batch

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

    BRANCH = (
        ('CSE','CSE'),
        ('ECE','ECE'),
        ('ME','ME'),
        ('DESIGN','DESIGN'),
        ('Common','Common'),
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

    COURSE_TYPE = (
        ('Professional Core', 'Professional Core'),
        ('Professional Elective', 'Professional Elective'),
        ('Professional Lab', 'Professional Lab'),
        ('Engineering Science', 'Engineering Science'),
        ('Natural Science', 'Natural Science'),
        ('Humanities', 'Humanities'),
        ('Design', 'Design'),
        ('Manufacturing', 'Manufacturing'),
        ('Management Science', 'Management Science'),
    )


class Student(models.Model):
    '''
        Current Purpose : To store information pertinent to a user who is also a student
        
        

        ATTRIBUTES :

        id(globals.ExtraInfo) - one to one unique reference to the nominal details of the student[not nullable]
        program(char) - to store the programme (eg: Btech Mtech)
        batch(Integer) -  to store the batch year(eg 2019)
        batch_id(programme_curriculum.Batch) - reference to the Batch collective details(foreign key, can be null)
        cpi(Float) - to store the current CPI of the student
        category - to store the details about category of a sutdent (General/OBC etc)[not nullable]
        father_name(char) - father's name
        mother_name(char) - mother's name
        hall_no(integer) - the hostel number in which the student has been alloted a room
        room_no(char) - the room.no of the student
        specialization - to dentote the specialization for MTECH students[null is allowed]
        cur_sem_no(integer) - the current semester of the student

    '''
    id = models.OneToOneField(ExtraInfo, on_delete=models.CASCADE, primary_key=True)
    programme = models.CharField(max_length=10, choices=Constants.PROGRAMME)
    batch = models.IntegerField(default=2016)
    batch_id = models.ForeignKey(Batch, null=True, blank=True, on_delete=models.CASCADE)
    cpi = models.FloatField(default=0)
    category = models.CharField(max_length=10, choices=Constants.CATEGORY, null=False)
    father_name = models.CharField(max_length=40, default='')
    mother_name = models.CharField(max_length=40, default='')
    hall_no = models.IntegerField(default=0)
    room_no = models.CharField(max_length=10, blank=True, null=True)
    specialization = models.CharField(max_length=40,choices=Constants.MTechSpecialization, null=True, default='')
    curr_semester_no = models.IntegerField(default=1)
#     pwd_status = models.BooleanField(null=True, blank=True,default=False)
#     father_mobile_no = models.CharField(max_length=10, null=True, blank=True, default='9999999999')
#     mother_mobile_no = models.CharField(max_length=10, null=True, blank=True, default='9999999999')

    def __str__(self):
        username = str(self.id.user.username)
        return username
        


class Course(models.Model):
    '''
        Current Purpose : To store information of a course
        
        

        ATTRIBUTES :

        course_name(char) - to store the name of the course
        course_details(TextField) -  to store the course details

    '''
    course_name = models.CharField(max_length=600)
    course_details = models.TextField(max_length=500)

    class Meta:
        db_table = 'Course'

    def __str__(self):
        return self.course_name


class Curriculum(models.Model):
    '''
        Current Purpose : Currently this table stores mapping of a course to a particular semester and relevant details

        ! - the table does not follow the conventional definition of the term Curriculum 
        ATTRIBUTES :

        curriculum_id(AutoField) - to store the automatically generated course id which will be the primary key
        course_code(CharField) -  stores the course code (can be null)
        course_id(academic_information.Course) - foreign key to the course 
        credits(integer) - stores credits assigned for the course
        course_type(char) - to select the type of the course(eg : Professional Core/Project)
        programme(char) - to store the programme for which the course is being offered
        branch(char) - to store the branch/discipline for which the course is being offered(eg CSE)
        batch(integer) - to store the batch for which the course is available(eg:2019)
        sem(Integer) - the semester in which the course is offered for a batch
        optional(Boolean) - denotes whether the course is optional or not
        floated(Boolean) - denotes whether a course is floated for a particular semester or not

    '''
    curriculum_id = models.AutoField(primary_key=True)
    course_code = models.CharField(max_length = 20)
    course_id = models.ForeignKey(Course,on_delete= models.CASCADE)
    credits = models.IntegerField()
    course_type = models.CharField(choices=Constants.COURSE_TYPE, max_length=25)
    programme = models.CharField(choices=Constants.PROGRAMME, max_length=10)
    branch = models.CharField(choices=Constants.BRANCH, max_length=10, default='Common')
    batch = models.IntegerField()
    sem = models.IntegerField()
    optional = models.BooleanField(default=False)
    floated = models.BooleanField(default=False)

    class Meta:
        db_table = 'Curriculum'
        unique_together = ('course_code', 'batch', 'programme')

    def __str__(self):
        return '{} - {}'.format(self.course_code,self.course_id.course_name)


class Curriculum_Instructor(models.Model):
    '''
        Current Purpose : Currently this table stores mapping of a course in a semester to the faculty who will teach the course

        ! - the table does not follow the conventional definition of the term Curriculum 

        
        
        

        ATTRIBUTES :

        curriculum_id(academic_information.Curriculum) - reference to the course details 
        instructor_id(globals.ExtraInfo) - reference to the faculty who will teach the course
        chief_inst(Bool) - denotes whether the faculty is the chief instructor of the course or not


    '''
    curriculum_id = models.ForeignKey(Curriculum, on_delete=models.CASCADE)
    instructor_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    chief_inst = models.BooleanField(default=False)

    class Meta:
        db_table = 'Curriculum_Instructor'
        unique_together = ('curriculum_id', 'instructor_id')

    def __self__(self):
        return '{} - {}'.format(self.curriculum_id, self.instructor_id)
    
    def __str__(self):
        return '{} - {}'.format(self.curriculum_id.course_code,self.instructor_id.user.username)


class Student_attendance(models.Model):
    '''
        Current Purpose : Currently this table stores mapping of a student's attendance for a particular course in a semester


        
        
        

        ATTRIBUTES :

        student_id(academic_information.Student) - referene to the student for whom the attendance is being recorded
        instructor_id(academic_information.Curriculum_Instructor) - reference to the faculty and course 
        date(DateField) - the date for which the attendance will be recorded
        present(Boolean) - to denote whether the student was present or not

    '''
    student_id = models.ForeignKey(Student,on_delete=models.CASCADE)
#    course_id = models.ForeignKey(Course)
#    attend = models.CharField(max_length=6, choices=Constants.ATTEND_CHOICES)
    instructor_id = models.ForeignKey(Curriculum_Instructor, on_delete=models.CASCADE)
#    curriculum_id = models.ForeignKey(Curriculum, on_delete=models.CASCADE)
    date = models.DateField()
    present = models.BooleanField(default=False)

    class Meta:
        db_table = 'Student_attendance'

    def __self__(self):
        return self.course_id


class Meeting(models.Model):
    '''
        Current Purpose : stores the information regarding a meeting which was conducted by the academic department

        ATTRIBUTES:
        
        venue(char) - venue where the meeting will be held(eg:L-103)
        date(DateField) - the date on which the meeting was held
        time(char) -  time at the meeting was held
        agenga(text) - the points of discussion for the meeting
        minutes_file(char) - the summary of the meeting

    '''
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
    '''
        Current Purpose : stores the information regarding an academic event(eg : course registrations etc)

        ATTRIBUTES:
        
        from_date(DateField) -  start date of the event
        to_date(DateField) - end date of the event
        description(Char) - description about the event
    '''
    from_date = models.DateField()
    to_date = models.DateField()
    description = models.CharField(max_length=40)

    class Meta:
        db_table = 'Calendar'

    def __str__(self):
        return self.description


class Holiday(models.Model):
    '''
        Current Purpose : stores the information regarding a holiday 

        ATTRIBUTES
        holiday_date(DateField) - the date of the holidar
        holiday_name(char) - to denote the name of the holiday(eg : Republic Day)
        holiday_type - to store whether the holiday is restricted or closed
    '''
    holiday_date = models.DateField()
    holiday_name = models.CharField(max_length=40)
    holiday_type = models.CharField(default='restricted', max_length=30,
                                    choices=Constants.HOLIDAY_TYPE)

    class Meta:
        db_table = 'Holiday'

    def __str__(self):
        return self.holiday_name


class Grades(models.Model):
    '''
        Current Purpose : stores the information regarding the gradees of a student for a course in a semester

        ATTRIBUTES
        student_id(academic_information.Student) - Reference to the student for whom the grades is about to be stores
        curriculum_id(academic_information.Curriculum) - Reference to the course for which the graded are to be given
        grade(Char) - denotes whether the grade given to the student is verified or not
    '''
    student_id = models.ForeignKey(Student,on_delete=models.CASCADE)
    curriculum_id = models.ForeignKey(Curriculum,on_delete=models.CASCADE)
    grade = models.CharField(max_length=4)
    verify =models.BooleanField(default=False)

    class Meta:
        db_table = 'Grades'


class Spi(models.Model):
    '''
        Current Purpose : stores the information regarding the SPI of a student for a semester

        ATTRIBUTES
        sem(Integer) - the semester to which the spi refers to
        student_id(academic_information.Student) - the student for whom the spi is stored
        spi(float) - the spi value achieved
    '''
    sem = models.IntegerField()
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    spi = models.FloatField(default=0)

    class Meta:
        db_table = 'Spi'
        unique_together = ('student_id', 'sem')

    def __self__(self):
        return self.sem


class Timetable(models.Model):
    '''
        Current Purpose : stores the class-schedule timetable for a batch (eg CSE -2019-Btech)

        ATTRIBUTES

        upload_date(DateTime) - stores the upload date and time 
        time_table(File) -  the file which contains the timetable
        batch(Integer) -  stores the batch for which the timetable is valid
        programme(Char) - stores the programme for which the time table is valid
        branch(char) - the branch for which the time table is valid
    '''

    upload_date = models.DateTimeField(auto_now_add=True)
    time_table = models.FileField(upload_to='Administrator/academic_information/')
    batch = models.IntegerField(default="2016")
    programme = models.CharField(max_length=10, choices=Constants.PROGRAMME)
    branch = models.CharField(max_length=10, choices=Constants.BRANCH, default="Common")
    class Meta:
        db_table = 'Timetable'


class Exam_timetable(models.Model):
    '''
        Current Purpose : stores the exam-schedule timetable for a batch (2019-Btech)

        ATTRIBUTES

        upload_date(DateTime) - stores the upload date and time 
        exam_time_table(File) -  the file which contains the timetable
        batch(Integer) -  stores the batch for which the timetable is valid
        programme(Char) - stores the programme for which the time table is valid
        
    '''
    upload_date = models.DateField(auto_now_add=True)
    exam_time_table = models.FileField(upload_to='Administrator/academic_information/')
    batch = models.IntegerField(default="2016")
    programme = models.CharField(max_length=10, choices=Constants.PROGRAMME)

    class Meta:
        db_table = 'Exam_Timetable'
