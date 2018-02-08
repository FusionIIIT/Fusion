import datetime

from django.db import models

from applications.academic_information.models import Student


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
    award_name = models.CharField(max_length=100, default='gold_medal')
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
                                  default='Government')
    mother_occ = models.CharField(max_length=10,
                                  choices=Constants.MOTHER_OCC_CHOICES,
                                  default='HOUSE-WIFE')
    relevant_document = models.FileField(null=True, blank=True)
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
    award_id = models.ForeignKey(Award_and_scholarship)
    venue = models.CharField(max_length=50)
    time = models.CharField(max_length=10, choices=Constants.time)
    batch = models.CharField(max_length=10, choices=Constants.batch)

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

    class Meta:
        db_table = 'Director_gold'
