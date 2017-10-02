from django.db import models

class Constants:
    RESUME_TYPE = (
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
    )
    ACHIEVEMENT_TYPE = (
        ('EDUCATIONAL', 'Educational'),
        ('OTHER', 'Other'),
    )
    INVITATION_TYPE = (
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('PENDING', 'Pending'),
    )
    PLACEMENT_TYPE = (
        ('PLACEMENT', 'Placement'),
        ('PBI', 'PBI'),
        ('HIGHER STUDIES', 'Higher Studies'),
        ('OTHER', 'Other'),
    )
    PLACED_TYPE = (
        ('ON CAMPUS', 'On Campus'),
        ('PPO', 'PPO'),
        ('OFF CAMPUS', 'Off Campus'),
    )
    DEBAR_TYPE = (
        ('DEBAR', 'Debar'),
        ('NOT DEBAR', 'Not Debar'),
    )


class Project(models.Model):
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE, primary_key=True)
    project_id = models.AutoField(primary_key=True)
    project_name = models.CharField(max_length=40, default='')
    project_status = models.CharField(max_length=20, choices=Constants.RESUME_TYPE, default='COMPLETED')
    summary = models.CharField(max_length=500, default='')
    project_link = models.CharField(max_length=200, default='')
    sdate = models.DateField()
    edate = models.DateField(null=True, blank=True)


class Language(models.Model):
    language_id = models.AutoField(primary_key=True)
    language = models.CharField(max_length=20, default='')


class Know(models.Model):
    language_id = models.ForeignKey(Language, on_delete=models.CASCADE, primary_key=True)
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE, primary_key=True)


class Skill(models.Model):
    skill_id = models.AutoField(primary_key=True)
    skill = models.CharField(max_length=30, default='')


class Has(models.Model):
    skill_id = models.ForeignKey(Skill, on_delete=models.CASCADE, primary_key=True)
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE, primary_key=True)


class Education(models.Model):
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE, primary_key=True)
    education_id = models.AutoField(primary_key=True)
    degree = models.CharField(max_length=40, default='')
    institute = models.CharField(max_length=250, default='')
    stream = models.CharField(max_length=150, default='')
    sdate = models.DateField()
    edate = models.DateField()


class Experience(models.Model):
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE, primary_key=True)
    experience_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100, default='')
    status = models.CharField(max_length=20, choices=Constants.RESUME_TYPE, default='COMPLETED')
    description = models.CharField(max_length=500, default='')
    company = models.CharField(max_length=200, default='')
    location = models.CharField(max_length=200, default='')
    sdate = models.DateField()
    edate = models.DateField(null=True, blank=True)


class Course(models.Model):
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE, primary_key=True)
    course_id = models.AutoField(primary_key=True)
    course_name = models.CharField(max_length=100, default='')
    description = models.CharField(max_length=250, default='')
    license_no = models.IntegerField(default='')
    sdate = models.DateField()
    edate = models.DateField(null=True, blank=True)


class Publication(models.Model):
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE, primary_key=True)
    publication_id = models.AutoField(primary_key=True)
    publication_title = models.CharField(max_length=100, default='')
    description = models.CharField(max_length=250, default='')
    publisher = models.CharField(max_length=250, default='')
    publication_date = models.DateField()


class Coauthor(models.Model):
    publication_id = models.ForeignKey(Publication, on_delete=models.CASCADE, primary_key=True)
    author_id = models.AutoField(primary_key=True)
    coauthor_name = models.CharField(max_length=100, default='')


class Patent(models.Model):
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE, primary_key=True)
    patent_id = models.AutoField(primary_key=True)
    patent_name = models.CharField(max_length=100, default='')
    description = models.CharField(max_length=250, default='')
    patent_office = models.CharField(max_length=250, default='')
    patent_date = models.DateField()


class Coinventor(models.Model):
    publication_id = models.ForeignKey(Publication, on_delete=models.CASCADE, primary_key=True)
    inventor_id = models.AutoField(primary_key=True)
    coinventor_name = models.CharField(max_length=100, default='')


class Interest(models.Model):
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE, primary_key=True)
    interest = models.CharField(max_length=100, default='')


class Achievement(models.Model):
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE, primary_key=True)
    achievement_id = models.AutoField(primary_key=True)
    achievement = models.CharField(max_length=100, default='')
    achievement_type = models.CharField(max_length=20, choices=Constants.ACHIEVEMENT_TYPE, default='OTHER')
    description = models.CharField(max_length=250, default='')
    issuer = models.CharField(max_length=200, default='')
    date_earned = models.DateField()


class MessageOfficer(models.Model):
    message_id = models.AutoField(primary_key=True)
    message = models.CharField(max_length=100, default='')
    timestamp = models.DateTimeField(auto_now=True)


class PlacementStatus(models.Model):
    notify_id = models.AutoField(primary_key=True)
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE, primary_key=True)
    invitation = models.CharField(max_length=20, choices=Constants.INVITATION_TYPE, default='PENDING')
    placed = models.CharField(max_length=20, choices=Constants.INVITATION_TYPE, default='PENDING')
    timestamp = models.DateTimeField(auto_now=True)


class PlacementRecord(models.Model):
    record_id = models.AutoField(primary_key=True)
    placement_type = models.CharField(max_length=20, choices=Constants.PLACEMENT_TYPE, default='PLACEMENT')
    name = models.CharField(max_length=100, default='')
    ctc = models.DecimalField(default='0.0')
    year = models.IntegerField(default='0')
    test_score = models.IntegerField(default='0')
    test_type = models.CharField(max_length=30, default='')


class StudentRecord(models.Model):
    record_id = models.ForeignKey(PlacementRecord, on_delete=models.CASCADE, primary_key=True)
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE, primary_key=True)


class NotifyStudent(models.Model):
    notify_id = models.AutoField(primary_key=True)
    placement_type = models.CharField(max_length=20, choices=Constants.PLACEMENT_TYPE, default='PLACEMENT')
    company_name = models.CharField(max_length=100, default='')
    ctc = models.DecimalField(default='0.0')
    description = models.CharField(max_length=1000, default='')


class ChairmanVisit(models.Model):
    visit_id = models.AutoField(primary_key=True)
    company_name = models.CharField(max_length=100, default='')
    loaction = models.CharField(max_length=100, default='')
    visiting_date = models.DateField()
    description = models.CharField(max_length=1000, default='')
    timestamp = models.DateTimeField(auto_now=True)


class ContactCompany(models.Model):
    contact_id = models.AutoField(primary_key=True)
    company_name = models.CharField(max_length=100, default='')
    hr_mail = models.CharField(max_length=100, default='')
    reference = models.CharField(max_length=1000, default='')
    description = models.CharField(max_length=500, default='')
    timestamp = models.DateTimeField(auto_now=True)


class PlacementSchedule(models.Model):
    schedule_id = models.AutoField(primary_key=True)
    notify_id = models.ForeignKey(NotifyStudent, on_delete=models.CASCADE, primary_key=True)
    title = models.CharField(max_length=100, default='')
    date = models.DateField()
    location = models.CharField(max_length=100, default='')
    description = models.CharField(max_length=500, default='')
    time = models.TimeField()


class PlacementSchedule(models.Model):
    unique_id = models.ForeignKey(User, on_delete=models.CASCADE, primary_key=True)
    debar = models.CharField(max_length=20, choices=Constants.DEBAR_TYPE, default='NOT DEBAR')
    future_aspect = models.CharField(max_length=20, choices=Constants.PLACEMENT_TYPE, default='PLACEMENT')
    placed_type = models.CharField(max_length=20, choices=Constants.PLACED_TYPE, default='PLACEMENT')
    placement_date = models.DateField()
    package = models.DecimalField(default='0.0')
