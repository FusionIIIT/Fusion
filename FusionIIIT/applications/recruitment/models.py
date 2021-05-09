from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
# Create your models here.



class Constants:
    # Class for various choices on the enumerations
    SEX_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )

    MARITAL_STATUS = (
        ('M', 'Married'),
        ('U', 'Unmarried'),
    )

    STATUS = (
        ('Ongoing', 'Ongoing'),
        ('Completed', 'Completed'),
    )

    LEVEL = (
        ('UG','UnderGraduate'),
        ('PG','PostGraduate'),
    )


    LEVEL_POST = (
        ('Masters','Masters'),
        ('PhD','PhD'),
    )

    SPECIALIZATION_CHOICES = (
        ('MA', 'Major'),
        ('MI', 'Minor'),
    )


    JOB_CHOICES = (
        ('T', 'Teaching'),
        ('NT', 'Non-Teaching'),
    )

    USER_CHOICES = (
        ('student', 'student'),
        ('staff', 'staff'),
        ('compounder', 'compounder'),
        ('faculty', 'faculty'),
    )


    CATEGORY_CHOICES = (
        ('PH', 'Physically Handicapped'),
        ('UR', 'Unreserved'),
        ('OBC', 'Other Backward Classes'),
        ('SC', 'Scheduled Castes'),
        ('ST','Scheduled Tribes'),
        ('EWS','Economic Weaker Section'),
    )


    



class PersonalDetails(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=20, default='Dr.')
    sex = models.CharField(max_length=2, choices=Constants.SEX_CHOICES, default='M')
    profile_picture = models.ImageField(null=True, blank=True, upload_to='')
    marital_status = models.CharField(max_length=10,choices=Constants.MARITAL_STATUS)
    discipline = models.CharField(max_length=50)
    specialization = models.CharField(max_length=10,choices=Constants.SPECIALIZATION_CHOICES)
    category = models.CharField(max_length=20,choices=Constants.CATEGORY_CHOICES)
    father_name = models.CharField(max_length=40, default='')
    address_correspondence = models.TextField(max_length=1000)
    address_permanent = models.TextField(max_length=1000, default="")
    email_alternate = models.EmailField(null=True,max_length=50,default="")
    phone_no = models.BigIntegerField(null=True,default=9999999999)
    mobile_no_first = models.BigIntegerField(default=9999999999)
    mobile_no_second = models.BigIntegerField(null=True, default=9999999999)
    date_of_birth = models.DateField(default=datetime.date(1970, 1, 1))
    nationality = models.CharField(max_length= 30)

    def __str__(self):
        username = str(self.user.username)
        return username
    


class BankDetails(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    payment_reference_number = models.CharField(max_length=20)
    payment_date = models.DateField()
    bank_name = models.CharField(max_length=100)
    bank_branch = models.CharField(max_length=200)

    def __str__(self):
        reference_number = str(self.payment_reference_number)
        return reference_number




class EducationalDetails(models.Model):
    university = models.CharField(max_length=200)
    board = models.CharField(max_length=200)
    year_of_passing = models.IntegerField()
    division = models.CharField(max_length=6)

    def __str__(self):
        return str(self.university) + "-" + str(self.year_of_passing)



class AcademicDetails(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    Xth = models.OneToOneField(EducationalDetails,on_delete=models.CASCADE,related_name="Xth_details")
    XIIth = models.OneToOneField(EducationalDetails,on_delete=models.CASCADE,related_name="XIIth_details")
    graduation = models.OneToOneField(EducationalDetails,on_delete=models.CASCADE,related_name="graduation_details")
    post_graduation = models.OneToOneField(EducationalDetails,on_delete=models.CASCADE,related_name="post_graduations_details")
    phd = models.OneToOneField(EducationalDetails,on_delete=models.CASCADE,related_name="phd_details")
    area_of_specialization = models.TextField()
    current_area_of_research = models.TextField()
    date_of_enrollment_in_phd = models.DateField()
    date_of_phd_defence = models.DateField()
    date_of_award_of_phd = models.DateField()





class ExperienceDetails(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_experience_months = models.IntegerField(null=True)
    member_of_professional_body = models.CharField(null=True,max_length=200)
    employer = models.CharField(null=True,max_length=100)
    position_held = models.CharField(null=True,max_length=100)
    date_of_joining = models.DateField(null=True)
    date_of_leaving = models.DateField(null=True)
    pay_in_payband = models.CharField(null=True,max_length=20)
    payband = models.CharField(null=True,max_length=20)
    AGP = models.CharField(null=True,max_length=20)
    reasons_for_leaving = models.TextField(null=True)

    def __str__(self):
        return str(self.user.username)+ "-"+str(self.employer)




class References(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    address = models.TextField(null=True)
    email = models.EmailField()
    mobile_number = models.BigIntegerField()
    department = models.CharField(max_length=50)

    def __str__(self):
        return str(self.user.username)+ "-"+str(self.name)



class Publications(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    referred_journal = models.CharField(max_length=100)
    sci_index_journal = models.CharField(max_length=100)
    international_conferences = models.CharField(null=True,max_length=100)
    national_conferences = models.CharField(null=True,max_length=100)

    def __str__(self):
        return str(self.user.username)+ "-"+str(self.referred_journal)



class Experience(models.Model):
    duration = models.IntegerField(null=True)
    organization = models.CharField(null=True,max_length=100)
    area = models.CharField(null=True,max_length=200)

    def __str__(self):
        return str(organization)



class ResearchExperience(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    research_experience = models.ForeignKey(Experience,on_delete = models.CASCADE)

class TeachingExperience(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    teaching_experience = models.ForeignKey(Experience,on_delete = models.CASCADE)


class AdministrativeExperience(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    period = models.IntegerField(null=True)
    organization = models.CharField(null=True,max_length=200)
    title_of_post = models.CharField(null=True,max_length=200)
    nature_of_work = models.TextField(null=True)

    def __str__(self):
        return str(self.user.username)+ "-"+str(self.organization)


class IndustrialExperience(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    period = models.IntegerField(null=True)
    organization = models.CharField(null=True,max_length=200)
    title_of_post = models.CharField(null=True,max_length=200)
    nature_of_work = models.TextField(null=True)

    def __str__(self):
        return str(self.user.username)+ "-"+str(self.organization)



class CoursesTaught(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(null=True,max_length=100)
    level = models.CharField(null=True,max_length=20,choices=Constants.LEVEL)
    number_of_times= models.IntegerField(null=True)
    developed_by_you = models.BooleanField(null=True)

    def __str__(self):
        return str(self.user.username)+ "-"+str(self.title)


class ThesisSupervision(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name_of_student = models.CharField(max_length=200)
    masters_or_phd = models.CharField(max_length=20,choices=Constants.LEVEL_POST)
    year_of_completion = models.IntegerField()
    title_of_thesis = models.CharField(max_length = 100)
    co_guides = models.CharField(max_length=200,null=True)

    def __str__(self):
        return str(self.user.username)+ "-"+str(self.title_of_thesis)



class SponsoredProjects(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    period = models.CharField(max_length = 10)
    sponsoring_organisation = models.CharField(max_length=200)
    title_of_project = models.CharField(max_length=200)
    grant_amount = models.IntegerField(null=True)
    co_investigators = models.CharField(null=True,max_length=200)
    status = models.CharField(max_length=20,choices=Constants.STATUS)

    def __str__(self):
        return str(self.user.username)+ "-"+str(self.title_of_project)



class Consultancy(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    period =models.CharField(max_length=10)
    sponsoring_organisation = models.CharField(max_length=200)
    title_of_project = models.CharField(max_length=200)
    grant_amount = models.IntegerField(null=True)
    co_investigators = models.CharField(null=True,max_length=200)
    status = models.CharField(max_length=20,choices=Constants.STATUS)

    def __str__(self):
        return str(self.user.username)+ "-"+str(self.title_of_project)



class QualifiedExams(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    net = models.BooleanField()
    gate = models.BooleanField()
    jrf = models.BooleanField()




class Patent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    filed_national = models.CharField(max_length = 200, null=True)
    filed_international = models.CharField(max_length = 200, null=True)
    award_national = models.CharField(max_length = 200, null=True)
    award_international = models.CharField(max_length = 200, null=True)



class Books(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name_of_book = models.CharField(max_length=100)
    year = models.IntegerField()
    published = models.BooleanField()
    title = models.CharField(max_length=100)
    publisher = models.CharField(max_length=200)
    co_author = models.CharField(max_length=100, null=True)

    def __str__(self):
        return str(self.user.username)+ "-"+str(self.name_of_book)




class NationalConference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    author = models.CharField(max_length=100)
    year = models.IntegerField()
    title = models.CharField(max_length=100)
    name_and_place_of_conference = models.CharField(max_length=200)
    presented = models.BooleanField()
    published = models.BooleanField()

    def __str__(self):
        return str(self.user.username)+ "-"+str(self.author)



class InternationalConference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    author = models.CharField(max_length=100)
    year = models.IntegerField()
    title = models.CharField(max_length=100)
    name_and_place_of_conference = models.CharField(max_length=200)
    presented = models.BooleanField()
    published = models.BooleanField()

    def __str__(self):
        return str(self.user.username)+ "-"+str(self.author)


class PapersInReferredJournal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    author = models.CharField(max_length=100)
    year = models.IntegerField()
    published = models.BooleanField()
    accepted = models.BooleanField()
    title = models.CharField(max_length=100)
    reference_of_journal = models.CharField(max_length=100)
    impact_factor = models.CharField(max_length=100)

    def __str__(self):
        return str(self.user.username)+ "-"+str(self.author)






################## HR ###############

class Vacancy(models.Model):
    advertisement_number = models.IntegerField()
    job_description = models.TextField()
    job_notification = models.FileField()
    number_of_vacancy = models.IntegerField(default=1)
    job_type = models.CharField(max_length=15,choices=Constants.JOB_CHOICES)
    last_date = models.DateField()

    def __str__(self):
        return str(self.advertisement_number)



class applied(models.Model):
    user = models.ForeignKey(User,on_delete = models.CASCADE)
    advertisement_number = models.ForeignKey(Vacancy,on_delete = models.CASCADE)
    date = models.DateField(default = timezone.now)

    def __str__(self):
        return str(self.advertisement_number)
