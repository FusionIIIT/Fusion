import datetime

from django.db import models

from applications.academic_information.models import Student


class Constants:
    STATUS_CHOICES = (
        ('COMPLETE', 'COMPLETE'),
        ('INCOMPLETE', 'INCOMPLETE')
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
    FATHER_OCC_CHOICES = (
        ('Service', (
                        ('government', 'Government'),
                        ('private', 'Private'),
                        ('public', 'Public'),
                        )
         ),
        ('Non_Salaried', (
                         ('business', 'Business'),
                         ('medical', 'Medical'),
                         ('consultant', 'Consultant'),
                        )
         ),
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


class Mcm(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    email_id = models.CharField(max_length=50, default='siri@gmail.com')
    income_total = models.IntegerField(default=0)
    income_file = models.FileField(null=True, blank=True)
    loan_bank_details = models.TextField(max_length=1000, default='no loan')
    bank_acc_no = models.CharField(default='', max_length=30)
    loan_amount = models.IntegerField(default=0)
    brother_name = models.CharField(max_length=30)
    brother_occupation = models.TextField(max_length=100)
    sister_name = models.CharField(max_length=30)
    sister_occupation = models.TextField(max_length=100)
    income_father = models.IntegerField(default=0)
    income_mother = models.IntegerField(default=0)
    father_occ_choice = models.CharField(max_length=10, choices=Constants.FATHER_OCC_CHOICES)
    father_occ = models.TextField(max_length=100)
    mother_occ_choice = models.CharField(max_length=10, choices=Constants.MOTHER_OCC_CHOICES)
    mother_occ = models.TextField(max_length=100)
    four_wheeler = models.IntegerField(default=0)
    four_wheeler_des = models.TextField(max_length=1000, null=True)
    two_wheeler = models.IntegerField(default=0)
    two_wheeler_des = models.TextField(max_length=1000, null=True)
    house_type = models.CharField(max_length=10, choices=Constants.HOUSE_TYPE_CHOICES)
    house_area = models.IntegerField(default=0)
    school_10 = models.CharField(max_length=250)
    school_10_fee = models.IntegerField(default=0)
    school_12 = models.CharField(max_length=250)
    school_12_fee = models.IntegerField(default=0)
    father_declaration = models.FileField(null=True, blank=True)
    affidavit = models.FileField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Constants.STATUS_CHOICES)
    status_check = models.BooleanField(default=False)

    class Meta:
        db_table = 'Mcm'


class Award_and_scholarship(models.Model):
    award_name = models.CharField(max_length=100, default='gold_medal')
    catalog = models.TextField(max_length=5000)

    class Meta:
        db_table = 'Award_and_scholarship'


class Previous_winner(models.Model):
    student_id = models.ForeignKey(Student)
    year = models.IntegerField(default=datetime.datetime.now().year)
    award_id = models.ForeignKey(Award_and_scholarship)

    class Meta:
        db_table = 'Previous_winner'


class Release(models.Model):
    startdate = models.DateField(("Start"), default=datetime.date.today)
    enddate = models.DateField(("End date"))
    award_id = models.ForeignKey(Award_and_scholarship)
    venue = models.CharField(max_length=50)
    time = models.CharField(max_length=10, choices=Constants.time)
    batch = models.CharField(max_length=10, choices=Constants.batch)

    class Meta:
        db_table = 'Release'


class Financial_assistance(models.Model):
    authority_name = models.TextField(max_length=150)
    name_of_prize = models.TextField(max_length=50)
    amount_month = models.IntegerField(default=0)
    total_amount = models.IntegerField(default=0)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)

    class Meta:
        db_table = 'Financial_assistance'


class Common_info(models.Model):
    police_station = models.TextField(max_length=150)
    railway_station = models.TextField(max_length=150)
    correspondence_address = models.TextField(max_length=150)
    justification_description = models.TextField(max_length=1000)
    financial_assistance_id = models.ForeignKey(Financial_assistance)
    relevant_documents = models.FileField(null=True, blank=True)

    class Meta:
        db_table = 'Common_info'


class Director_silver(models.Model):
    common_info_id = models.ForeignKey(Common_info, on_delete=models.CASCADE)
    description = models.TextField(max_length=7000)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    award_id = models.ForeignKey(Award_and_scholarship, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=Constants.STATUS_CHOICES, default='COMPLETE')
    status_check = models.BooleanField(default=False)

    class Meta:
        db_table = 'Director_silver'


class Proficiency_dm(models.Model):
    common_info_id = models.ForeignKey(Common_info, on_delete=models.CASCADE)
    report_file = models.FileField(null=True, blank=True)
    title_name = models.CharField(max_length=30)
    description = models.TextField(max_length=3500)
    ece_topic_description = models.TextField(max_length=1000)
    mech_topic_description = models.TextField(max_length=1000)
    cse_topic_description = models.TextField(max_length=1000)
    design_topic_description = models.TextField(max_length=200)
    ece_percentage = models.FloatField(null=True, blank=True, default=0.0)
    cse_percentage = models.FloatField(null=True, blank=True, default=0.0)
    mech_precentage = models.FloatField(null=True, blank=True, default=0.0)
    design_percentage = models.FloatField(null=True, blank=True, default=0.0)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    award_id = models.ForeignKey(Award_and_scholarship, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=Constants.STATUS_CHOICES, default='COMPLETE')
    status_check = models.BooleanField(default=False)

    class Meta:
        db_table = 'Proficiency_dm'


class Director_gold(models.Model):
    common_info_id = models.ForeignKey(Common_info, on_delete=models.CASCADE)
    academic_achievements = models.TextField(max_length=5000, default='Academic achhievements')
    sta_in_desc = models.TextField(max_length=5000, default='Technical Acheivements ins IIITDMJ')
    sta_out_desc = models.TextField(max_length=5000, default='Technical Acheivements outs IIITDMJ')
    cul_in_desc = models.TextField(max_length=5000, default='Cultural Achievements ins IIITDMJ')
    cul_out_desc = models.TextField(max_length=5000, default='Cultural Acheivements outs IIITDMJ')
    games_in_desc = models.TextField(max_length=5000, default='Games Acheivements ins IIITDMJ')
    games_out_desc = models.TextField(max_length=5000, default='Games Acheivements outs IIITDMJ')
    social_service = models.TextField(max_length=5000, default='Social Services')
    corporate_service = models.TextField(max_length=5000, default='Corporate Services')
    hall_activity_desc = models.TextField(max_length=5000, default='Hall Related Activities')
    inst_activity_desc = models.TextField(max_length=5000, default='Institute Related Activities')
    gymkhana_desc = models.TextField(max_length=5000, default='Gymkhana Activities')
    coun_service_desc = models.TextField(max_length=5000, default='counselling service description')
    other_activity_desc = models.TextField(max_length=5000)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    award_id = models.ForeignKey(Award_and_scholarship, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=Constants.STATUS_CHOICES)
    status_check = models.BooleanField(default=False)

    class Meta:
        db_table = 'Director_gold'


class Group_student(models.Model):
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    proficiency_dm_id = models.ForeignKey(Proficiency_dm, on_delete=models.CASCADE)

    class Meta:
        db_table = 'Group_student'
