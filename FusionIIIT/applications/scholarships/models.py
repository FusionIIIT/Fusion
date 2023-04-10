import datetime

from django.db import models

from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo


class Constants:
    STATUS_CHOICES = (
        ('Complete', 'COMPLETE'),
        ('Incomplete', 'INCOMPLETE'),
        ('Reject', 'REJECT'),
        ('Accept', 'ACCEPT'),
    )
    TIME = (
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
        ('12 Midnight', '0'),
    )
    BATCH = (
        ('UG1', 'UG1'),
        ('UG2', 'UG2'),
        ('UG3', 'UG3'),
        ('UG4', 'UG4'),
        ('PG1', 'PG1'),
        ('PG2', 'PG2'),
    )
    FATHER_OCC_CHOICE = (
        ('government', 'Government'),
        ('private', 'Private'),
        ('public', 'Public'),
        ('business', 'Business'),
        ('medical', 'Medical'),
        ('consultant', 'Consultant'),
        ('pensioners', 'Pensioners'),
    )
    MOTHER_OCC_CHOICES = (
        ('EMPLOYED', 'EMPLOYED'),
        ('HOUSE_WIFE', 'HOUSE_WIFE')
    )
    HOUSE_TYPE_CHOICES = (
        ('RENTED', 'RENTED'),
        ('OWNED', 'OWNED')
    )

    PROGRAMME_CHOICES = (
        ('B', 'UNDER_GRAD'),
        ('P', 'POST_GRAD_PHD'),
        ('M', 'POST_GRAD_MASTER')
    )

    DISCIPLINE_CHOICES = (
        ('C', 'CSE'),
        ('E', 'ECE'),
        ('M', 'ME'),
        ('D', 'DES')
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
                                  choices=Constants.FATHER_OCC_CHOICE,
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
    bank_name = models.CharField(max_length=100, null=True)
    loan_amount = models.IntegerField(blank=True, null=True)
    college_fee = models.IntegerField(blank=True, null=True)
    college_name = models.CharField(max_length=30, null=True)
    income_certificate = models.FileField(null=True, blank=True)
    forms = models.FileField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Constants.STATUS_CHOICES, default='INCOMPLETE')
    student = models.ForeignKey(Student,
                                on_delete=models.CASCADE, related_name='mcm_info')
    annual_income = models.IntegerField(default=0)
    date = models.DateField(default=datetime.date.today)
    award_id = models.ForeignKey(Award_and_scholarship, default=4, on_delete=models.CASCADE)

    class Meta:
        db_table = 'Mcm'

    def __str__(self):
        return str(self.student)


class Notional_prize(models.Model):
    spi = models.FloatField()
    cpi = models.FloatField()
    year = models.CharField(max_length=10, choices=Constants.BATCH)
    award_id = models.ForeignKey(Award_and_scholarship, default=4, on_delete=models.CASCADE)

    class Meta:
        db_table = 'Notional_prize'


# Addition: a column programme added
class Previous_winner(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    programme = models.CharField(max_length=10, default='B.Tech')
    year = models.IntegerField(default=datetime.datetime.now().year)
    award_id = models.ForeignKey(Award_and_scholarship, on_delete=models.CASCADE)

    class Meta:
        db_table = 'Previous_winner'


class Release(models.Model):
    date_time = models.DateTimeField(default=datetime.datetime.now, blank=True)
    programme = models.CharField(max_length=10, default='B.Tech')
    startdate = models.DateField(default=datetime.date.today)
    enddate = models.DateField()
    award = models.CharField(default='', max_length=50)
    remarks = models.TextField(max_length=500, default='')
    batch = models.TextField(default='all')
    notif_visible = models.IntegerField(default=1)

    class Meta:
        db_table = 'Release'


# new class added for keeping track of notifications and applied application by students
class Notification(models.Model):
    release_id = models.ForeignKey(Release, default=None, on_delete=models.CASCADE)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE)
    notification_mcm_flag = models.BooleanField(default=False)
    notification_convocation_flag = models.BooleanField(default=False)
    invite_mcm_accept_flag = models.BooleanField(default=False)
    invite_convocation_accept_flag = models.BooleanField(default=False)

    def __str__(self):
        return str(self.student_id)

    class Meta:
        db_table = 'Notification'


class Application(models.Model):
    application_id = models.CharField(max_length=100, primary_key=True)
    student_id = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE)
    applied_flag = models.BooleanField(default=False)
    award = models.CharField(max_length=30)

    def __str__(self):
        return str(self.application_id)

    class Meta:
        db_table = 'Application'


class Director_silver(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    award_id = models.ForeignKey(Award_and_scholarship, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=Constants.STATUS_CHOICES, default='INCOMPLETE')
    date = models.DateField(default=datetime.date.today)
    cultural_intercollege_certificate = models.FileField(blank=True, null=True)
    cultural_intercollege_certificates_no = models.IntegerField(blank=True, null=True)
    cultural_intercollege_team_event = models.TextField(max_length=1000, null=True)
    cultural_intercollege_team_certificate = models.FileField(null=True, blank=True)
    cultural_intercollege_team_certificates_no = models.IntegerField(
        blank=True, null=True
    )
    culturalfest_certificate = models.FileField(null=True, blank=True)
    culturalfest_certificates_no = models.IntegerField(blank=True, null=True)
    cultural_club_coordinator = models.TextField(max_length=1000, null=True)
    cultural_club_coordinator_certificate = models.FileField(null=True, blank=True)
    cultural_club_co_coordinator = models.TextField(max_length=1000, null=True)
    cultural_club_co_coordinator_certificate = models.FileField(null=True, blank=True)
    cultural_event_member = models.TextField(max_length=1000, null=True)
    cultural_event_member_certificate = models.FileField(null=True, blank=True)
    cultural_interIIIT_certificates_no = models.IntegerField(blank=True, null=True)
    cultural_interIIIT_team_certificate = models.FileField(null=True, blank=True)
    cultural_interIIIT_certificate = models.FileField(blank=True, null=True)
    cultural_interIIIT_team_certificates_no = models.IntegerField(blank=True, null=True)
    sports_intercollege_certificate = models.FileField(blank=True, null=True)
    sports_intercollege_team_certificate = models.FileField(null=True, blank=True)
    sportsfest_certificate = models.FileField(null=True, blank=True)
    sportsfest_team_certificate = models.FileField(null=True, blank=True)
    sports_club_coordinator = models.TextField(max_length=1000, null=True)
    sports_club_coordinator_certificate = models.FileField(null=True, blank=True)
    sports_club_co_coordinator = models.TextField(max_length=1000, null=True)
    sports_club_co_coordinator_certificate = models.FileField(null=True, blank=True)
    sports_event_member = models.TextField(max_length=1000, null=True)
    sports_event_member_certificate = models.FileField(null=True, blank=True)
    sports_interIIIT_team_certificate = models.FileField(null=True, blank=True)
    sports_interIIIT_certificate = models.FileField(blank=True, null=True)
    sports_other_accomplishment = models.TextField(max_length=1000, null=True)
    sports_other_accomplishment_doc = models.FileField(null=True, blank=True)

    class Meta:
        db_table = 'Director_silver'


class DM_Proficiency_gold(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    award_id = models.ForeignKey(Award_and_scholarship, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=10, choices=Constants.STATUS_CHOICES, default='INCOMPLETE'
    )
    date = models.DateField(default=datetime.date.today)
    brief_description_project = models.TextField(max_length=1000, null=True)
    project_grade = models.TextField(max_length=1000, null=True)
    cross_disciplinary = models.TextField(max_length=1000, null=True)
    project_cross_disciplinary = models.TextField(max_length=1000, null=True)
    project_cross_disciplinary_doc = models.FileField(null=True, blank=True)
    project_publication = models.TextField(max_length=1000, null=True)
    project_type = models.TextField(max_length=1000, null=True)
    patent_ipr_project = models.TextField(max_length=1000, null=True)
    prototype_available = models.TextField(max_length=1000, null=True)
    team_members_name = models.TextField(max_length=1000, null=True)
    team_members_cpi = models.TextField(max_length=1000, null=True)
    project_evaluation_prototype = models.TextField(max_length=1000, null=True)
    project_evaluation_prototype_doc = models.FileField(null=True, blank=True)
    project_utility = models.TextField(max_length=1000, null=True)
    project_utility_doc = models.FileField(null=True, blank=True)
    sports_cultural_doc = models.FileField(null=True, blank=True)
    sports_cultural = models.TextField(max_length=1000, null=True)
    sci = models.TextField(max_length=1000, null=True)  # new attribute added
    sci_doc = models.FileField(null=True, blank=True)  # new attribute added
    esci = models.TextField(max_length=1000, null=True)  # new attribute added
    esci_doc = models.FileField(null=True, blank=True)  # new attribute added
    scie = models.TextField(max_length=1000, null=True)  # new attribute added
    scie_doc = models.FileField(null=True, blank=True)  # new attribute added
    ij = models.TextField(max_length=1000, null=True)  # new attribute added
    ij_doc = models.FileField(null=True, blank=True)  # new attribute added
    ic = models.TextField(max_length=1000, null=True)  # new attribute added
    ic_doc = models.FileField(null=True, blank=True)  # new attribute added
    nc = models.TextField(max_length=1000, null=True)  # new attribute added
    nc_doc = models.FileField(null=True, blank=True)  # new attribute added
    workshop = models.TextField(max_length=1000, null=True)  # new attribute added
    workshop_doc = models.FileField(null=True, blank=True)  # new attribute added

    class Meta:
        db_table = 'DM_Proficiency_gold'


class Director_gold(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=10, choices=Constants.STATUS_CHOICES, default='INCOMPLETE'
    )
    date = models.DateField(default=datetime.date.today)
    award_id = models.ForeignKey(
        Award_and_scholarship, default=4, on_delete=models.CASCADE
    )
    financial_assistance = models.TextField(max_length=1000, null=True)
    financial_assistance_doc = models.FileField(null=True, blank=True)
    academic = models.TextField(max_length=1000, null=True)
    academic_doc = models.FileField(null=True, blank=True)
    science = models.TextField(max_length=1000, null=True)
    science_doc = models.FileField(null=True, blank=True)
    games = models.TextField(max_length=1000, null=True)
    games_doc = models.TextField(null=True, blank=True)
    cultural = models.TextField(max_length=1000, null=True)
    cultural_doc = models.FileField(null=True, blank=True)
    social = models.TextField(max_length=1000, null=True)
    social_doc = models.FileField(null=True, blank=True)
    corporate = models.TextField(max_length=1000, null=True)
    corporate_doc = models.FileField(null=True, blank=True)
    hall_activities = models.TextField(max_length=1000, null=True)
    hall_activities_doc = models.FileField(null=True, blank=True)
    gymkhana_activities = models.TextField(max_length=1000, null=True)
    gymkhana_activities_doc = models.FileField(null=True, blank=True)
    institute_activities = models.TextField(max_length=1000, null=True)
    institute_activities_doc = models.FileField(null=True, blank=True)
    counselling_activities = models.TextField(max_length=1000, null=True)
    counselling_activities_doc = models.FileField(null=True, blank=True)
    sci = models.TextField(max_length=1000, null=True)  # new attribute added for PG
    sci_doc = models.FileField(null=True, blank=True)  # new attribute added for PG
    scie = models.TextField(max_length=1000, null=True)  # new attribute added for PG
    scie_doc = models.FileField(null=True, blank=True)  # new attribute added for PG
    ij = models.TextField(max_length=1000, null=True)  # new attribute added for PG
    ij_doc = models.FileField(null=True, blank=True)  # new attribute added for PG
    ic = models.TextField(max_length=1000, null=True)  # new attribute added for PG
    ic_doc = models.FileField(null=True, blank=True)  # new attribute added for PG
    nc = models.TextField(max_length=1000, null=True)  # new attribute added for PG
    nc_doc = models.FileField(null=True, blank=True)  # new attribute added for PG
    workshop = models.TextField(
        max_length=1000, null=True
    )  # new attribute added for PG
    workshop_doc = models.FileField(null=True, blank=True)  # new attribute added for PG
    novelty = models.TextField(max_length=200, null=True)  # new attribute added for PG
    warning_letter = models.FileField(
        null=True, blank=True
    )  # new attribute added for PG
    disciplinary_action = models.TextField(
        max_length=1000, null=True
    )  # new attribute added
    other_extra_curricular_activities = models.FileField(null=True, blank=True)
    jagriti = models.FileField(null=True, blank=True)  # new attribute added
    blood_donation = models.FileField(null=True, blank=True)  # new attribute added

    class Meta:
        db_table = 'Director_gold'


class IIITDM_Proficiency(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=10, choices=Constants.STATUS_CHOICES, default='INCOMPLETE'
    )
    date = models.DateField(default=datetime.date.today)
    award_id = models.ForeignKey(
        Award_and_scholarship, default=4, on_delete=models.CASCADE
    )
    project_objectives = models.TextField(max_length=1000, null=True)
    project_mentor = models.TextField(max_length=1000, null=True)
    project_outcome = models.TextField(max_length=1000, null=True)
    project_publications = models.TextField(max_length=1000, null=True)
    research_Or_Patent_Detail = models.TextField(max_length=1000, null=True)
    project_Beneficial = models.TextField(max_length=1000, null=True)
    improvement_Done = models.TextField(max_length=1000, null=True)
    project_report = models.FileField(null=True, blank=True)
    project_title = models.TextField(max_length=1000, null=True)
    project_abstract = models.TextField(max_length=1000, null=True)
    sci = models.TextField(max_length=1000, null=True)  # new attribute added for PG
    sci_doc = models.FileField(null=True, blank=True)  # new attribute added for PG
    esci = models.TextField(max_length=1000, null=True)  # new attribute added for PG
    esci_doc = models.FileField(null=True, blank=True)  # new attribute added for PG
    scie = models.TextField(max_length=1000, null=True)  # new attribute added for PG
    scie_doc = models.FileField(null=True, blank=True)  # new attribute added for PG
    ij = models.TextField(max_length=1000, null=True)  # new attribute added for PG
    ij_doc = models.FileField(null=True, blank=True)  # new attribute added for PG
    ic = models.TextField(max_length=1000, null=True)  # new attribute added for PG
    ic_doc = models.FileField(null=True, blank=True)  # new attribute added for PG
    nc = models.TextField(max_length=1000, null=True)  # new attribute added for PG
    nc_doc = models.FileField(null=True, blank=True)  # new attribute added for PG
    indian_national_Conference = models.TextField(max_length=1000, null=True)
    indian_national_Conference_doc = models.FileField(null=True, blank=True)
    international_Conference = models.TextField(max_length=1000, null=True)
    international_Conference_doc = models.FileField(null=True, blank=True)
    project_grade = models.TextField(max_length=1000, null=True)
    patent_Status = models.TextField(
        max_length=1000, null=True
    )  # new attribute added for PG
    interdisciplinary_Criteria = models.TextField(
        max_length=1000, null=True
    )  # new attribute added for PG
    awards_Recieved_Workshop = models.TextField(max_length=1000, null=True)
    placement_Status = models.TextField(max_length=1000, null=True)
    workshop = models.TextField(max_length=1000, null=True)
    workshop_doc = models.TextField(max_length=1000, null=True)
    prototype = models.TextField(max_length=1000, null=True)
    prototype_doc = models.FileField(null=True, blank=True)
    utility = models.TextField(max_length=1000, null=True)
    utility_doc = models.FileField(null=True, blank=True)
    core_Area = models.TextField(max_length=1000, null=True)
    core_Area_doc = models.FileField(null=True, blank=True)
    technology_Transfer = models.TextField(max_length=1000, null=True)
    technology_Transfer_doc = models.FileField(null=True, blank=True)
    project_write_up = models.TextField(max_length=1000, null=True)

    class Meta:
        db_table = 'IIITDM_Proficiency'
