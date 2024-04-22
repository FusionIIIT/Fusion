  
import datetime
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import models
from applications.globals.models import ExtraInfo

class emp_visits(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True,null=True)
    pf_no = models.CharField(max_length=20)
    v_type = models.IntegerField(default = 1)
    country = models.CharField(max_length=500, default=" ")
    place = models.CharField(max_length=500, default=" ")
    purpose = models.CharField(max_length=500, default=" ")
    v_date = models.DateField(null=True,blank=True)
    start_date = models.DateField(null=True,blank=True)
    end_date = models.DateField(null=True,blank=True)
    entry_date = models.DateField(null=True,blank=True, default=datetime.datetime.now)

    def __str__(self):
        return 'PF No.: {}   Name: {}   Purpose: {}'.format(self.pf_no,self.country,self.purpose)

    def get_absolute_url(self):
        return reverse('eis:profile')


class emp_techtransfer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True,null=True)
    pf_no = models.IntegerField()
    details = models.CharField(max_length=500, default=" ")
    date_entry = models.DateField(null=True, blank=True, default=datetime.datetime.now)
    start_date = models.DateField(null=True,blank=True)
    end_date = models.DateField(null=True,blank=True)


class emp_session_chair(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True,null=True)
    pf_no = models.IntegerField()
    name = models.CharField(max_length=500, default=" ")
    event = models.TextField(max_length=2500, default=" ")
    YEAR_CHOICES = []
    for r in range(1995, 2018):
        YEAR_CHOICES.append((r, r))
    s_year = models.IntegerField(('year'), choices=YEAR_CHOICES, null=True, blank=True)
    MONTH_CHOICES = []
    for r in range(1, 13):
        MONTH_CHOICES.append((r, r))
    a_month = models.IntegerField(('Month'), choices=MONTH_CHOICES, null=True, blank=True, default=1)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    date_entry = models.DateField(null=True, blank=True, default=datetime.datetime.now)
    remarks = models.CharField(default = " ", max_length=1000)

    def __str__(self):
        return 'PF No.: {}   Name: {}'.format(self.pf_no,self.name)


class emp_research_projects(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True,null=True)
    pf_no = models.IntegerField()
    ptype = models.CharField(max_length=100, default="Research")
    pi = models.CharField(max_length=1000, default=" ")
    co_pi = models.CharField(max_length=1500, default=" ")
    title = models.TextField(max_length=5000, default=" ")
    funding_agency = models.CharField(max_length=250, default=" ", null=True)
    financial_outlay = models.CharField(max_length=150, default=" ", null=True)
    STATUS_TYPE_CHOICES = (
        ('Awarded', 'Awarded'),
        ('Submitted', 'Submitted'),
        ('Ongoing', 'Ongoing'),
        ('Completed', 'Completed')
    )
    status = models.CharField(max_length = 10, choices = STATUS_TYPE_CHOICES)
    start_date = models.DateField(null=True, blank=True)
    finish_date = models.DateField(null=True, blank=True)
    date_submission = models.DateField(null=True, blank=True)
    date_entry = models.DateField(null=True, blank=True, default=datetime.datetime.now)

    def __str__(self):
        return 'PF No.: {}   pi: {}  title: {}'.format(self.pf_no,self.pi, self.title)


class emp_research_papers(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True,null=True)
    pf_no = models.IntegerField()
    R_TYPE_CHOICES = (
        ('Journal', 'Journal'),
        ('Conference', 'Conference'),
    )
    rtype = models.CharField(max_length=500, choices = R_TYPE_CHOICES, default='Conference')
    authors = models.CharField(max_length=2500, null=True, blank=True)
    co_authors = models.CharField(max_length=2500, null=True, blank=True)
    title_paper = models.CharField(max_length=2500, null=True, blank=True)
    name = models.CharField(max_length=2500, null=True, blank=True)
    paper = models.CharField(max_length=1000, blank=True,null=True)
    venue = models.CharField(max_length=2500, null=True, blank=True)
    volume_no = models.CharField(max_length=500, null=True , blank=True)
    page_no = models.CharField(max_length=500,null=True, blank=True)
    IS_SCI_TYPE_CHOICES = (
        ('SCI', 'SCI'),
        ('SCIE', 'SCIE'),
    )
    is_sci = models.CharField(max_length=6, choices=IS_SCI_TYPE_CHOICES, null=True, blank=True)
    isbn_no = models.CharField(max_length=250, null=True, blank=True)
    doi = models.CharField(max_length=1000,null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    date_acceptance = models.DateField(null=True, blank=True)
    date_publication = models.DateField(null=True, blank=True)
    YEAR_CHOICES = []
    for r in range(1995, (datetime.datetime.now().year + 1)):
        YEAR_CHOICES.append((r, r))
    year = models.CharField(max_length=10, choices=YEAR_CHOICES, null=True, blank=True)
    MONTH_CHOICES = []
    for r in range(1, 13):
        MONTH_CHOICES.append((r, r))
    a_month = models.CharField(max_length=500, choices=MONTH_CHOICES, null=True, blank=True, default=1)
    doc_id = models.CharField(max_length=50, null=True, blank=True)
    doc_description = models.CharField(max_length=1000, null=True, blank=True)
    date_entry = models.DateField(null=True, blank=True, default=datetime.datetime.now)
    STATUS_TYPE_CHOICES = (
        ('Published', 'Published'),
        ('Accepted', 'Accepted'),
        ('Communicated', 'Communicated'),
    )
    status = models.CharField(max_length=15, choices=STATUS_TYPE_CHOICES, null=True, blank=True)
    date_submission = models.DateTimeField(null=True, blank=True)
    reference_number = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return 'PF No.: {}   Author: {}  Title: {}'.format(self.pf_no,self.authors, self.title_paper)


class emp_published_books(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True,null=True)
    pf_no = models.IntegerField()
    PTYPE_TYPE_CHOICES = (
        ('Book', 'Book'),
        ('Monograph', 'Monograph'),
        ('Book Chapter', 'Book Chapter'),
        ('Handbook', 'Handbook'),
        ('Technical Report', 'Technical Report'),
    )
    p_type = models.CharField(max_length=16, choices=PTYPE_TYPE_CHOICES)
    title = models.CharField(max_length=2500, default=" ")
    publisher = models.CharField(max_length=2500, default=" ")
    YEAR_CHOICES = []
    for r in range(1995, (datetime.datetime.now().year + 1)):
        YEAR_CHOICES.append((r, r))
    pyear = models.IntegerField(('year'), choices=YEAR_CHOICES, null=True, blank=True)
    authors = models.CharField(max_length=250, default=" ")
    date_entry = models.DateField(null=True, blank=True, default=datetime.datetime.now)
    publication_date = models.DateField(null=True,blank=True)
    
    def __str__(self):
        return 'PF No.: {}   Type: {}  Title: {}'.format(self.pf_no,self.p_type, self.title)


class emp_patents(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True,null=True)
    pf_no = models.IntegerField()
    p_no = models.CharField(max_length=150)
    title = models.CharField(max_length=1500)
    earnings = models.IntegerField(default=0)
    STATUS_TYPE_CHOICES = (
        ('Filed', 'Filed'),
        ('Granted', 'Granted'),
        ('Published', 'Published'),
        ('Owned', 'Owned'),
    )
    status = models.CharField(max_length=15, choices=STATUS_TYPE_CHOICES)
    YEAR_CHOICES = []
    for r in range(1995, (datetime.datetime.now().year + 1)):
        YEAR_CHOICES.append((r, r))
    p_year = models.IntegerField(('year'), choices=YEAR_CHOICES, null=True, blank=True)
    MONTH_CHOICES = []
    for r in range(1, 13):
        MONTH_CHOICES.append((r, r))
    a_month = models.IntegerField(('Month'), choices=MONTH_CHOICES, null=True, blank=True, default=1)
    date_entry = models.DateField(null=True, blank=True, default=datetime.datetime.now)
    start_date = models.DateField(null=True,blank=True)
    end_date = models.DateField(null=True,blank=True)
    def __str__(self):
        return 'PF No.: {}   Status: {}  Title: {}'.format(self.pf_no,self.status, self.title)


class emp_mtechphd_thesis(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True,null=True)
    pf_no = models.IntegerField()
    degree_type = models.IntegerField(default=1)
    title = models.CharField(max_length=250)
    supervisors = models.CharField(max_length=250)
    co_supervisors = models.CharField(max_length=250, null=True, blank=True)
    rollno = models.CharField(max_length=200)
    s_name = models.CharField(max_length=5000)
    YEAR_CHOICES = []
    for r in range(1995, (datetime.datetime.now().year + 1)):
        YEAR_CHOICES.append((r, r))
    s_year = models.IntegerField(('year'), choices=YEAR_CHOICES, null=True, blank=True)
    MONTH_CHOICES = []
    for r in range(1, 13):
        MONTH_CHOICES.append((r, r))
    a_month = models.IntegerField(('Month'), choices=MONTH_CHOICES, null=True, blank=True, default=1)
    date_entry = models.DateField(null=True, blank=True, default=datetime.datetime.now)
    start_date = models.DateField(null=True,blank=True)
    end_date = models.DateField(null=True,blank=True)
    semester=models.IntegerField(default = 1, blank=True, null=True)
    STATUS_TYPE_CHOICES = (
        ('Awarded', 'Awarded'),
        ('Submitted', 'Submitted'),
        ('Ongoing', 'Ongoing'),
        ('Completed', 'Completed')
    )
    status = models.CharField(max_length = 10, choices = STATUS_TYPE_CHOICES, null=True, blank=True)

    def __str__(self):
        return 'PF No.: {}   Supervisor: {}  Title: {}'.format(self.pf_no,self.supervisors, self.title)


class emp_keynote_address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True,null=True)
    pf_no = models.IntegerField()
    KEYNOTE_TYPE_CHOICES = (
        ('Keynote', 'Keynote'),
        ('Plenary Address', 'Plenary Address'),
    )
    type = models.CharField(max_length=140, choices=KEYNOTE_TYPE_CHOICES, default='Keynote')
    title = models.CharField(max_length=1000)
    name = models.CharField(max_length=1000)
    venue = models.CharField(max_length=1000)
    page_no = models.CharField(max_length=100)
    isbn_no = models.CharField(max_length=200)
    YEAR_CHOICES = []
    for r in range(1995, (datetime.datetime.now().year + 1)):
        YEAR_CHOICES.append((r, r))
    k_year = models.IntegerField(('year'), choices=YEAR_CHOICES, null=True, blank=True)
    MONTH_CHOICES = []
    for r in range(1, 13):
        MONTH_CHOICES.append((r, r))
    a_month = models.IntegerField(('Month'), choices=MONTH_CHOICES, null=True, blank=True, default=1)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    date_entry = models.DateField(null=True, blank=True, default=datetime.datetime.now)

    def __str__(self):
        return 'PF No.: {}   Name: {}  Title: {}'.format(self.pf_no,self.name, self.title)


class emp_expert_lectures(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True,null=True)
    pf_no = models.IntegerField()
    LECTURE_TYPE_CHOICES = (
        ('Expert Lecture', 'Expert Lecture'),
        ('Invited Talk', 'Invited Talk'),
    )
    l_type = models.CharField(max_length=14, choices=LECTURE_TYPE_CHOICES, default='Expert Lecture', null=False)
    title = models.CharField(max_length=1000)
    place = models.CharField(max_length=1000)
    l_date = models.DateField(null=True, blank=True)
    YEAR_CHOICES = []
    for r in range(1995, (datetime.datetime.now().year + 1)):
        YEAR_CHOICES.append((r, r))
    l_year = models.IntegerField(('year'), choices=YEAR_CHOICES, null=True, blank=True)
    MONTH_CHOICES = []
    for r in range(1, 13):
        MONTH_CHOICES.append((r, r))
    a_month = models.IntegerField(('Month'), choices=MONTH_CHOICES, null=True, blank=True, default=1)
    date_entry = models.DateField(null=True, blank=True, default=datetime.datetime.now)

    def __str__(self):
        return 'PF No.: {}  Title: {}'.format(self.pf_no, self.title)


class emp_event_organized(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True,null=True)
    pf_no = models.IntegerField()
    TYPE_CHOICES = (
        ('Training Program', 'Training Program'),
        ('Seminar', 'Seminar'),
        ('Short Term Program', 'Short Term Program'),
        ('Workshop', 'Workshop'),
        ('Any Other', 'Any Other'),
    )
    type = models.CharField(max_length=180, choices=TYPE_CHOICES)
    name = models.CharField(max_length=1000)
    sponsoring_agency = models.CharField(max_length=150)
    venue = models.CharField(max_length=100)
    ROLE_TYPE_CHOICES = (
        ('Convener', 'Convener'),
        ('Coordinator', 'Coordinator'),
        ('Co-Convener', 'Co-Convener'),
    )
    role = models.CharField(max_length=11, choices=ROLE_TYPE_CHOICES)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    date_entry = models.DateField(null=True, blank=True, default=datetime.datetime.now)

    def __str__(self):
        return 'PF No.: {}  Name: {}'.format(self.pf_no, self.name)


class emp_consultancy_projects(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True,null=True)
    pf_no = models.IntegerField()
    consultants = models.CharField(max_length=150)
    title = models.CharField(max_length=1000)
    client = models.CharField(max_length=1000)
    financial_outlay = models.IntegerField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    duration = models.CharField(max_length=500, null=True, blank=True)
    date_entry = models.DateField(null=True, blank=True, default=datetime.datetime.now)
    STATUS_TYPE_CHOICES = (
        ('Completed', 'Completed'),
        ('Submitted', 'Submitted'),
        ('Ongoing', 'Ongoing')
    )
    status = models.CharField(default = 'Ongoing', max_length = 10, choices = STATUS_TYPE_CHOICES, null=True, blank=True)
    remarks = models.CharField(max_length=1000, null=True, blank=True)
    def __str__(self):
        return 'PF No.: {}  Consultants: {}'.format(self.pf_no, self.consultants)


class emp_confrence_organised(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True,null=True)
    pf_no = models.IntegerField()
    name = models.CharField(max_length=500)
    venue = models.CharField(max_length=500)
    YEAR_CHOICES = []
    for r in range(1995, (datetime.datetime.now().year + 1)):
        YEAR_CHOICES.append((r, r))
    k_year = models.IntegerField(('year'), choices=YEAR_CHOICES, null=True, blank=True)
    MONTH_CHOICES = []
    for r in range(1, 13):
        MONTH_CHOICES.append((r, r))
    a_month = models.IntegerField(('Month'), choices=MONTH_CHOICES, null=True, blank=True, default=1)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    date_entry = models.DateField(default=datetime.datetime.now, null=True, blank=True)
    ROLE1_TYPE_CHOICES = (
        ('Advisary Committee', 'Advisary Committee'),
        ('Program Committee', 'Program Committee'),
        ('Organised', 'Organised'),
        ('Conference Chair', 'Conference Chair'),
        ('Any Other', 'Any Other'),
    )
    role1 = models.CharField(max_length=200, choices=ROLE1_TYPE_CHOICES, null=True, blank=True, default="Any Other")
    role2 = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return 'PF No.: {}  Name: {}'.format(self.pf_no, self.name)


class emp_achievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True,null=True)
    pf_no = models.IntegerField()
    A_TYPE_CHOICES = (
        ('Award', 'Award'),
        ('Honour', 'Honour'),
        ('Prize', 'Prize'),
        ('Other', 'Other'),
    )
    a_type = models.CharField(max_length=180, choices=A_TYPE_CHOICES, default="Other")
    details = models.TextField(max_length=1550, default=" ")
    DAY_CHOICES = []
    for r in range(1, 32):
        DAY_CHOICES.append((r, r))
    a_day = models.IntegerField(('Day'), choices=DAY_CHOICES, null=True, blank=True)
    MONTH_CHOICES = []
    for r in range(1, 13):
        MONTH_CHOICES.append((r, r))
    a_month = models.IntegerField(('Month'), choices=MONTH_CHOICES, null=True, blank=True)
    YEAR_CHOICES = []
    for r in range(1995, (datetime.datetime.now().year + 1)):
        YEAR_CHOICES.append((r, r))
    a_year = models.IntegerField(('year'), choices=YEAR_CHOICES, null=True, blank=True)
    date_entry = models.DateField(default=datetime.datetime.now)
    achievment_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return 'PF No.: {} {} : {}'.format(self.pf_no, self.a_type,self.details)

    def get_absolute_url(self):
        return reverse('eis:profile')


class faculty_about(models.Model):
    # id= models.OneToOneField(ExtraInfo, on_delete=models.CASCADE)
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    about = models.TextField(max_length=1000)
    doj = models.DateField(default=datetime.datetime.now)
    education = models.TextField(max_length=500)
    interest = models.TextField(max_length=500)
    contact = models.CharField(max_length=10,null=True, blank=True)
    github = models.CharField(max_length=100,null=True, blank=True)
    linkedin = models.CharField(max_length=100,null=True, blank=True)

    def __str__(self):
        return str(self.user)