from django.db import models

#
class Constants:
    DEPARTMENT = (
        ('CSE','CSE'),
        ('ECE','ECE'),
        ('ME','ME'),
        ('DESIGN','DESIGN'),
    )
    PARAMETER = (
        ('TLR','Teaching, Learning & Resources'),
        ('RP','Research & Professional Practice'),
        ('GO','Graduation Outcomes'),
        ('OI','Outreach and Inclusivity'),
        ('PR','PERCEPTION')
    )

# for adding new publicatons by faculty
class Add_publication(models.Model):
    faculty_id = models.AutoField(primary_key=True)
    faculty_name = models.CharField(max_length=122)
    title_of_publication = models.CharField(max_length=200)
    link_of_publication=models.URLField()
    description = models.TextField(max_length=300)
    date_of_publication = models.DateField()
    department = models.CharField(max_length=100)

# info about different research groups
class Research_group(models.Model):
    name = models.CharField(max_length=100)
    faculty_under_group = models.CharField(max_length=300)
    students_under_group = models.CharField(max_length=300)
    description = models.CharField(max_length=500)

#Research info of faculy
class Research(models.Model):
    faculty_id = models.AutoField(primary_key=True)
    faculty_name = models.CharField(max_length=100)
    department = models.CharField(choices=Constants.DEPARTMENT, max_length=10)
    description = models.CharField(max_length=500)
    research_work = FileField()

#student research info
class Student_research(models.Model):
    student_id = models.AutoField(primary_key=True)
    student_name = models.CharField(max_length=100)
    branch = models.CharField(choices=Constants.DEPARTMENT, max_length=10)
    work = models.FileField()
    approved = models.BooleanField(default='false')

#Info about nirf parameters
class Nirf_parameters(models.Model):
    parameter=models.CharField(choices=Constants.PARAMETER, max_length=50)
    description=models.CharField()

#Nirf information of institute
class Nirf(models.Model):
    ranking=models.IntegerField(default=50)
    year=models.IntegerField(default=2016)
    tlr_score=models.FloatField()
    rpc_score=models.FloatField()
    go_score=models.FloatField()
    pr_score=models.FloatField()
    overall_score=models.FloatField()
    parameters=models.ForeignKey(Nirf_parameters,on_delete=models.CASCADE)

#Rpsc office staff details
class Rspc_staff(models.Model):
    staff_name=models.CharField(max_length=50)
    email_id=models.CharField(default='staff@iiitdmj.ac.in')
    contact=models.BigIntegerField()

#rpsc office details
class Rspc_office(models.Model):
    dean=models.CharField(max_length=50)
    email_id=models.CharField(default='dean@iiitdmj.ac.in')
    staff=models.ForeignKey(Rspc_staff,on_delete=models.CASCADE)
    contact=models.BigIntegerField()

