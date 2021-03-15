from django.db import models

# Create your models here.
# group 8 and group 9
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
#Awards and Achievements Table for Research related achievements
class ResearchAward(models.Model):
  Award_Id= models.CharField(primary_key =True)
  Award_Title= models.CharField(max_length= 100)
  Brief = models.CharField(max_length = 250)
 
 #FUnct
def year_choices(): return [(r,r) for r in range(2004, datetime.date.today().year+1)]
 
 #List of student and faculty  who recieved the award
class Awards_List(models.Model) :
  Sno = models.IntegerField(primary_key = True)
  Award_Id= models.ForeignKey(Award , on_delete = models.CASCADE) 
  Student_Id = models.ForeignKey(Student ,on_delete         =models.CASCADE) 
  year = models.IntegerField(_('year'), choices=year_choices, default=current_year)
  Status = models.CharField(max_length = 10)
 
  
  
 
# Webinars , Seminars and Workshops related Information 
class Workshop(models.Model):
  workshop_id = models.AutoField(primary_key = True)
  workshop_title = models.CharField(max_length = 80)
  workshop_brief = models.CharField(max_length = 200)
  incharge = models.ForeignKey(Employee ,on_delete    =models.CASCADE) 
  status = models.CharField(max_length = 10)
  date = models.DateField()
  venue = models.CharField(max_length = 10)
 
 #List of people participating in a particular workshop

class Workshop_application(models.Model):
  application_id = models.AutoField(primary)
  student_id = models.ForeignKey(Student , on_delete = models.CASCADE)  #Foreign Key
  workshop_id = models.ForeignKey(Workshop ,on_delete =models.CASCADE) # Foreign Key
  status = models.CharField(max_length = 10)


 #Info about hackathons and students participating in it
class Hackathons(models.Model):
  Hackathon_Title = models.CharField(max_length = 80)
  Student_Id = models.ForeignKey(Student , on_delete = models.CASCADE)
  last_date_to_apply = models.DateField()
  Status = models.CharField(max_length = 50)

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

