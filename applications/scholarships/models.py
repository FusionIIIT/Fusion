import datetime

from django.db import models

from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo


class Constants:
    STATUS_CHOICES = (
        ('Complete', 'COMPLETE'),
        ('Incomplete', 'INCOMPLETE'),
        ('Reject', 'REJECT'),
        ('Accept', 'ACCEPT')

    )
    time = (
        ('0', '12 Midnight'),
        ('1am', '1'),
        ('2am', '2'),
        ('3am', '3'),
        ('4am', '4'),
        ('5am', '5'),
        ('6am', '6'),
        ('7am', '7'),
        ('8am', '8'),
        ('9am', '9'),
        ('10am', '10'),
        ('11am', '11'),
        ('12 Noon', '12'),
        ('1pm', '13'),
        ('2pm', '14'),
        ('3pm', '15'),
        ('4pm', '16'),
        ('5pm', '17'),
        ('6pm', '18'),
        ('7pm', '19'),
        ('8pm', '20'),
        ('9pm', '21'),
        ('10pm', '22'),
        ('11pm', '23'),
        ('12 Midnight', '0')
    )
    batch = (
        ('UG1', 'UG1'),
        ('UG2', 'UG2'),
        ('UG3', 'UG3'),
        ('UG4', 'UG4'),
        ('PG1', 'PG1'),
        ('PG2', 'PG2')
    )
    father_occ_choice = (
        ('government', 'Government'),
        ('private', 'Private'),
        ('public', 'Public'),
        ('business', 'Business'),
        ('medical', 'Medical'),
        ('consultant', 'Consultant'),
        ('pensioners', 'Pensioners')
    )
    MOTHER_OCC_CHOICES = (
        ('EMPLOYED', 'EMPLOYED'),
        ('HOUSE_WIFE', 'HOUSE_WIFE')
    )
    HOUSE_TYPE_CHOICES = (
        ('RENTED', 'RENTED'),
        ('OWNED', 'OWNED')
    )


class Award_and_scholarship(models.Model):
    award_name = models.CharField(max_length=100, default='')
    catalog = models.TextField(max_length=5000)

    class Meta:
        db_table = 'Award_and_scholarship'

    def __str__(self):
        return self.award_name


class Mcm(models.Model):
    brother_name = models.CharField(max_length=30, null=True)
    brother_occupation = models.TextField(max_length=100, null=True)
    sister_name = models.CharField(max_length=30, null=True)
    sister_occupation = models.TextField(max_length=100, null=True)
    income_father = models.IntegerField(default=0)
    income_mother = models.IntegerField(default=0)
    income_other = models.IntegerField(default=0)
    father_occ = models.CharField(max_length=10,
                                  choices=Constants.father_occ_choice,
                                  default='')
    mother_occ = models.CharField(max_length=10,
                                  choices=Constants.MOTHER_OCC_CHOICES,
                                  default='')
    father_occ_desc = models.CharField(max_length=30, null=True)
    mother_occ_desc = models.CharField(max_length=30, null=True)
    four_wheeler = models.IntegerField(blank=True, null=True)
    four_wheeler_desc = models.CharField(max_length=30, null=True)
    two_wheeler = models.IntegerField(blank=True, null=True)
    two_wheeler_desc = models.CharField(max_length=30, null=True)
    house = models.CharField(max_length=10, null=True)
    plot_area = models.IntegerField(blank=True, null=True)
    constructed_area = models.IntegerField(blank=True, null=True)
    school_fee = models.IntegerField(blank=True, null=True)
    school_name = models.CharField(max_length=30, null=True)
    bank_name = models.CharField(max_length=10, null=True)
    loan_amount = models.IntegerField(blank=True, null=True)
    college_fee = models.IntegerField(blank=True, null=True)
    college_name = models.CharField(max_length=30, null=True)
    income_certificate = models.FileField(null=True, blank=True)
    forms = models.FileField(null=True, blank=True)
    status = models.CharField(
        max_length=10, choices=Constants.STATUS_CHOICES, default='INCOMPLETE')
    student = models.ForeignKey(Student,
                                on_delete=models.CASCADE, related_name='mcm_info')
    annual_income = models.IntegerField(default=0)
    date = models.DateField(default=datetime.date.today)
    award_id = models.ForeignKey(Award_and_scholarship, default=4)


    class Meta:
        db_table = 'Mcm'

    def __str__(self):
        return str(self.student)


class Notional_prize(models.Model):
    spi = models.FloatField()
    cpi = models.FloatField()
    year = models.CharField(max_length=10, choices=Constants.batch)
    award_id = models.ForeignKey(Award_and_scholarship, default=4)


    class Meta:
        db_table = 'Notional_prize'


class Previous_winner(models.Model):
    student = models.ForeignKey(Student)
    year = models.IntegerField(default=datetime.datetime.now().year)
    award_id = models.ForeignKey(Award_and_scholarship)

    class Meta:
        db_table = 'Previous_winner'



class Release(models.Model):
    startdate = models.DateField(default=datetime.date.today)
    enddate = models.DateField()
    award = models.CharField(default='',max_length=25)
    remarks = models.TextField(max_length=500,default='')

    class Meta:
        db_table = 'Release'


class Director_silver(models.Model):
    nearest_policestation = models.TextField(max_length=30, default='station')
    nearest_railwaystation = models.TextField(max_length=30, default='station')
    correspondence_address = models.TextField(max_length=150, null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    award_id = models.ForeignKey(Award_and_scholarship, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=Constants.STATUS_CHOICES,
                              default='INCOMPLETE')
    relevant_document = models.FileField(null=True, blank=True)
    date = models.DateField(default=datetime.date.today)
    financial_assistance = models.TextField(max_length=1000 ,null=True)
    grand_total = models.IntegerField(null=True)
    inside_achievements = models.TextField(max_length=1000, null=True)
    justification = models.TextField(max_length=1000, null=True)
    outside_achievements = models.TextField(max_length=1000, null=True)
    correspondence_address = models.CharField(max_length=100, null=True)
    financial_assistance = models.TextField(max_length=1000, null=True)
    grand_total = models.IntegerField(null=True)
    nearest_policestation = models.CharField(max_length=25, null=True)
    nearest_railwaystation = models.CharField(max_length=25, null=True)


    class Meta:
        db_table = 'Director_silver'


class Proficiency_dm(models.Model):
    relevant_document = models.FileField(null=True, blank=True)
    title_name = models.CharField(max_length=30, null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    award_id = models.ForeignKey(Award_and_scholarship, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=Constants.STATUS_CHOICES,
                              default='INOMPLETE')
    nearest_policestation = models.TextField(max_length=30, default='station')
    nearest_railwaystation = models.TextField(max_length=30, default='station')
    correspondence_address = models.TextField(max_length=150, null=True)
    no_of_students = models.IntegerField(default=1)
    date = models.DateField(default=datetime.date.today)
    roll_no1 = models.IntegerField(default=0)
    roll_no2 = models.IntegerField(default=0)
    roll_no3 = models.IntegerField(default=0)
    roll_no4 = models.IntegerField(default=0)
    roll_no5 = models.IntegerField(default=0)
    financial_assistance = models.TextField(max_length=1000 ,null=True)
    brief_description = models.TextField(max_length=1000 ,null=True)
    justification = models.TextField(max_length=1000 ,null=True)
    grand_total = models.IntegerField(null=True)
    ece_topic = models.CharField(max_length=25,null=True)
    cse_topic = models.CharField(max_length=25,null=True)
    mech_topic = models.CharField(max_length=25,null=True)
    design_topic = models.CharField(max_length=25,null=True)
    ece_percentage = models.IntegerField(null=True)
    cse_percentage = models.IntegerField(null=True)
    mech_percentage = models.IntegerField(null=True)
    design_percentage = models.IntegerField(null=True)
    correspondence_address = models.CharField(max_length=100, null=True)
    financial_assistance = models.TextField(max_length=1000, null=True)
    grand_total = models.IntegerField(null=True)
    nearest_policestation = models.CharField(max_length=25, null=True)
    nearest_railwaystation = models.CharField(max_length=25, null=True)


    class Meta:
        db_table = 'Proficiency_dm'


class Director_gold(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    status = models.CharField(max_length=10,
                              choices=Constants.STATUS_CHOICES, default='INCOMPLETE')
    correspondence_address = models.TextField(max_length=40, default='adress')
    nearest_policestation = models.TextField(max_length=30, default='station')
    nearest_railwaystation = models.TextField(max_length=30, default='station')
    relevant_document = models.FileField(null=True, blank=True)
    date = models.DateField(default=datetime.date.today)
    award_id = models.ForeignKey(Award_and_scholarship, default=4)
    financial_assistance = models.TextField(max_length=1000 ,null=True)
    academic_achievements = models.TextField(max_length=1000 ,null=True)
    science_inside = models.TextField(max_length=1000 ,null=True)
    science_outside = models.TextField(max_length=1000 ,null=True)
    games_inside = models.TextField(max_length=1000 ,null=True)
    games_outside = models.TextField(max_length=1000 ,null=True)
    cultural_inside = models.TextField(max_length=1000 ,null=True)
    cultural_outside = models.TextField(max_length=1000 ,null=True)
    social = models.TextField(max_length=1000 ,null=True)
    coorporate = models.TextField(max_length=1000 ,null=True)
    hall_activities = models.TextField(max_length=1000 ,null=True)
    gymkhana_activities = models.TextField(max_length=1000 ,null=True)
    institute_activities = models.TextField(max_length=1000 ,null=True)
    counselling_activities = models.TextField(max_length=1000 ,null=True)
    other_activities = models.TextField(max_length=1000 ,null=True)
    justification = models.TextField(max_length=1000 ,null=True)
    grand_total = models.IntegerField(null=True)
    correspondence_address = models.CharField(max_length=100, null=True)
    financial_assistance = models.TextField(max_length=1000, null=True)
    grand_total = models.IntegerField(null=True)
    nearest_policestation = models.CharField(max_length=25, null=True)
    nearest_railwaystation = models.CharField(max_length=25, null=True)

    class Meta:
        db_table = 'Director_gold'
