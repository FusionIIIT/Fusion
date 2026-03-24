# import
import datetime
from django.utils import timezone
from django import template
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.urls import reverse

from applications.academic_information.models import Student
from applications.globals.models import ExtraInfo, Faculty

register = template.Library()

# ==================== TextChoices Classes (R5 Implementation) ====================

class ClubCategory(models.TextChoices):
    """Category choices for clubs - replaces Constants.categoryCh"""
    TECHNICAL = 'Technical', 'Technical'
    SPORTS = 'Sports', 'Sports'
    CULTURAL = 'Cultural', 'Cultural'


class MemberStatus(models.TextChoices):
    """Status choices for club members - replaces Constants.status for members"""
    OPEN = 'open', 'Open'
    CONFIRMED = 'confirmed', 'Confirmed'
    REJECTED = 'rejected', 'Rejected'
    MEMBER = 'member', 'Member'
    COORDINATOR = 'co-ordinator', 'Co-ordinator'
    CO_COORDINATOR = 'Co-cordinator', 'Co-cordinator'


class ClubStatus(models.TextChoices):
    """Status choices for clubs - replaces Constants.status for clubs"""
    OPEN = 'open', 'Open'
    CONFIRMED = 'confirmed', 'Confirmed'
    REJECTED = 'rejected', 'Rejected'


class FestChoices(models.TextChoices):
    """Fest choices - replaces Constants.fest"""
    ABHIKALPAN = 'Abhikalpan', 'Abhikalpan'
    GUSTO = 'Gusto', 'Gusto'
    TARANG = 'Tarang', 'Tarang'


class VenueCategory(models.TextChoices):
    """Venue categories for better organization"""
    CLASSROOM = 'Classroom', 'Classroom'
    LECTUREHALL = 'Lecturehall', 'Lecturehall'
    GROUND = 'Ground', 'Ground'
    COURT = 'Court', 'Court'
    OTHER = 'Other', 'Other'


class Venue(models.TextChoices):
    """All venue choices - replacing Constants.venue with flat choices for easier querying"""
    # Classrooms
    CR101 = 'CR101', 'CR101'
    CR102 = 'CR102', 'CR102'
    CR103 = 'CR103', 'CR103'
    CR104 = 'CR104', 'CR104'
    CR107 = 'CR107', 'CR107'
    CR108 = 'CR108', 'CR108'
    CR109 = 'CR109', 'CR109'
    CR201 = 'CR201', 'CR201'
    CR202 = 'CR202', 'CR202'
    CR208 = 'CR208', 'CR208'
    
    # Lecture Halls
    L101 = 'L101', 'L101'
    L102 = 'L102', 'L102'
    L103 = 'L103', 'L103'
    L104 = 'L104', 'L104'
    L105 = 'L105', 'L105'
    L106 = 'L106', 'L106'
    L107 = 'L107', 'L107'
    L108 = 'L108', 'L108'
    L201 = 'L201', 'L201'
    L202 = 'L202', 'L202'
    L206 = 'L206', 'L206'
    L207 = 'L207', 'L207'
    
    # Grounds
    FOOTBALL_GROUND = 'Football Ground', 'Football Ground'
    CRICKET_GROUND = 'Cricket Ground', 'Cricket Ground'
    BASKETBALL_GROUND = 'Basketball Ground', 'Basketball Ground'
    VOLLEYBALL_GROUND = 'Volleyball Ground', 'Volleyball Ground'
    ATHLETICS_GROUND = 'Athletics Ground', 'Athletics Ground'
    
    # Courts
    TENNIS_COURT = 'Tennis Court', 'Tennis Court'
    BADMINTON_COURT = 'Badminton Court', 'Badminton Court'
    TABLE_TENNIS_COURT = 'Table Tennis Court', 'Table Tennis Court'
    CHESS_ROOM = 'Chess Room', 'Chess Room'
    CARROM_ROOM = 'Carrom Room', 'Carrom Room'
    
    # Other Venues
    GYM = 'Gym', 'Gym'
    CC_FIRST = 'CC First Floor', 'CC First Floor'
    CC_SECOND = 'CC Second Floor', 'CC Second Floor'
    CC_THIRD = 'CC Third Floor', 'CC Third Floor'
    OAT = 'OAT', 'OAT'


class FormAvailability(models.TextChoices):
    """Form availability choices - replaces Constants.available"""
    ON = 'On', 'On'
    OFF = 'Off', 'Off'


class BudgetStatus(models.TextChoices):
    """Status choices for budget requests"""
    OPEN = 'open', 'Open'
    CONFIRMED = 'confirmed', 'Confirmed'
    REJECTED = 'rejected', 'Rejected'


# ==================== Legacy Constants (Kept for backward compatibility) ====================

class Constants:
    """Legacy Constants class - kept for backward compatibility"""
    available = FormAvailability.choices
    categoryCh = ClubCategory.choices
    status = MemberStatus.choices
    fest = FestChoices.choices
    venue = Venue.choices  # Now flat instead of nested tuples


# ==================== Models ====================

class Club_info(models.Model):
    """
    It has the whole information about the club information.
    It stores the details of a club.

    club_name - name of the club
    club_website - url of the club website
    category - to which category it belongs to
    co_ordinator - refers to the id of co_ordinator of the club
    co_coordinator - refers to the id of co_coordinator of the club
    faculty_incharge - the lecturer/proffesor who is incharge of this club.
    club_file - it is the url of club file
    activity_calender - it is the url of club logo
    description - refers to brief explanation about the club
    alloted_budget - the amount alloted to the club
    spent_budget - the amount spent by the club
    avail_budget  - the amount available at the club
    status - status of club whether it is confirmed or not
    head_changed_on - date when head was last changed
    created_on - date when club was created
    """
    club_name = models.CharField(max_length=50, null=False, primary_key=True)
    club_website = models.CharField(max_length=150, null=True, default="hello")
    category = models.CharField(max_length=50, null=False, choices=ClubCategory.choices)
    co_ordinator = models.ForeignKey(Student, on_delete=models.CASCADE, null=False, related_name='co_of')
    co_coordinator = models.ForeignKey(Student, on_delete=models.CASCADE, null=False, related_name='coco_of')
    faculty_incharge = models.ForeignKey(Faculty, on_delete=models.CASCADE, null=False, related_name='faculty_incharge_of')
    club_file = models.FileField(upload_to='gymkhana/club_poster', null=True)
    activity_calender = models.FileField(upload_to='gymkhana/activity_calender', null=True, default=" ")
    description = models.TextField(max_length=256, null=True)
    alloted_budget = models.IntegerField(null=True, default=0)
    spent_budget = models.IntegerField(null=True, default=0)
    avail_budget = models.IntegerField(null=True, default=0)
    status = models.CharField(max_length=50, choices=ClubStatus.choices, default=ClubStatus.OPEN)
    head_changed_on = models.DateField(default=timezone.now, auto_now=False, null=True)
    created_on = models.DateField(default=timezone.now, auto_now=False, null=True)

    def __str__(self):
        return str(self.club_name)

    class Meta:
        db_table = 'Club_info'


class Form_available(models.Model):
    """
    It stores registered form name , roll number and status.
    
    roll - roll number of the student
    status - it is a boolean value whether the form is available or not
    form_name - name of the form
    """
    roll = models.CharField(default=2016001, max_length=7, primary_key=True)
    status = models.BooleanField(default=True, max_length=5)
    form_name = models.CharField(default='senate_registration', max_length=30)

    def __str__(self):
        return str(self.roll)

    class Meta:
        db_table = 'Form_available'


class Registration_form(models.Model):
    """
    It stores the details of the student who has been registered.

    roll - roll number of the student
    user_name - stores name of the student who is registered
    branch - the branch student belongs to like cse,ece etc..,
    cpi - the cumulative pointer of the student
    programme - the programme student belongs to like B.tech,M.tech etc..,
    """
    roll = models.CharField(max_length=7, default="2016001", primary_key=True)
    user_name = models.CharField(max_length=40, default="Student")
    branch = models.CharField(max_length=20, default='open')
    cpi = models.FloatField(max_length=3, default=6.0)
    programme = models.CharField(max_length=20, default='B.tech')

    def __str__(self):
        return str(self.roll)

    class Meta:
        db_table = 'Registration_form'


class Club_member(models.Model):
    """
    This contains information of students of the club and to which club they belong to.

    id - serial number for students(not useful)
    member - roll number of student
    club -  the name of clubs this particular student belongs to
    description - brief explanation of the member related to club if any thing needed
    status - status of the member whether he is confirmed or pending in a club
    remarks - remarks of the student by the club if any.
    """
    id = models.AutoField(primary_key=True)
    member = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='member_of')
    club = models.ForeignKey(Club_info, on_delete=models.CASCADE, related_name='this_club', null=False)
    description = models.TextField(max_length=256, null=True)
    status = models.CharField(max_length=50, choices=MemberStatus.choices, default=MemberStatus.OPEN)
    remarks = models.CharField(max_length=256, null=True)

    def __str__(self):
        return str(self.member.id)

    class Meta:
        db_table = 'Club_member'


class Core_team(models.Model):
    """
    The details about the main members who conducted/take care of the fest.
    It stores the information of those members.

    id - serial number
    student_id - roll number of student
    team - name of the core_team
    year - year in which this team conducted the fest
    fest_name - name of the fest the core_team students takes care of
    pda - achievements they achieved through the fest
    remarks - remarks(if there are any) in the fest
    """
    id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='applied_for')
    team = models.CharField(max_length=50, null=False)
    year = models.DateTimeField(max_length=6, null=True)
    fest_name = models.CharField(max_length=256, null=False, choices=FestChoices.choices)
    pda = models.TextField(max_length=256, null=False)
    remarks = models.CharField(max_length=256, null=True)

    def __str__(self):
        return str(self.student_id)

    class Meta:
        db_table = 'Core_team'


class Club_budget(models.Model):
    """
    Records the budget details of the clubs.

    id - serial number
    club - name of the club
    budget_for - the purpose of the budget, like for equipment or for event etc..,
    budget_amt - the amount required for the club
    budget_file - it is file which contains complete details regarding the amount they want to spend
    description - description about the budget if any
    status - status of budget request
    remarks - remarks if any
    """
    id = models.AutoField(primary_key=True)
    club = models.ForeignKey(Club_info, on_delete=models.CASCADE, max_length=50, null=False)
    budget_for = models.CharField(max_length=256, null=False)
    budget_amt = models.IntegerField(default=0, null=False)
    budget_file = models.FileField(upload_to='uploads/', null=False)
    description = models.TextField(max_length=256, null=False)
    status = models.CharField(max_length=50, choices=BudgetStatus.choices, default=BudgetStatus.OPEN)
    remarks = models.CharField(max_length=256, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'Club_budget'


class Session_info(models.Model):
    """
    This model has the information regarding the sessions conducting by the clubs.

    id - serial number
    club - name of the club
    venue - the place at which they conducting the session
    date - date of the session 
    start_time - the time at which session starts
    end_time - the time at which session ends
    session_poster - the logo/poster for the session(image)
    details - for which purpose they are taking the session
    status - whether it is approved/rejected.
    """
    id = models.AutoField(primary_key=True)
    club = models.ForeignKey(Club_info, on_delete=models.CASCADE, max_length=50, null=True)
    venue = models.CharField(max_length=50, null=False, choices=Venue.choices)
    date = models.DateField(default=None, auto_now=False, null=False)
    start_time = models.TimeField(default=None, auto_now=False, null=False)
    end_time = models.TimeField(default=None, auto_now=False, null=True)
    session_poster = models.ImageField(upload_to='gymkhana/session_poster', null=True)
    details = models.TextField(max_length=256, null=True)
    status = models.CharField(max_length=50, choices=ClubStatus.choices, default=ClubStatus.OPEN)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'Session_info'


class Event_info(models.Model):
    """
    This model has the information regarding the events conducting by the clubs.

    id - serial number
    club - name of the club
    event_name - name of the event
    venue - the place at which they conducting the event
    incharge - name of faculty who is incharge for the event
    date - date of the event
    start_time - the time at which event starts
    end_time - the time at which event ends
    event_poster - the logo/poster for the event(image)
    details - for which purpose they are conducting the event
    status - whether it is approved/rejected.
    """
    id = models.AutoField(primary_key=True)
    club = models.ForeignKey(Club_info, on_delete=models.CASCADE, max_length=50, null=True)
    event_name = models.CharField(max_length=256, null=False)
    venue = models.CharField(max_length=50, null=False, choices=Venue.choices)
    incharge = models.CharField(max_length=256, null=False)
    date = models.DateField(default=None, auto_now=False, null=False)
    start_time = models.TimeField(default=None, auto_now=False, null=False)
    end_time = models.TimeField(default=None, auto_now=False, null=True)
    event_poster = models.FileField(upload_to='gymkhana/event_poster', blank=True)
    details = models.TextField(max_length=256, null=True)
    status = models.CharField(max_length=50, choices=ClubStatus.choices, default=ClubStatus.OPEN)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'Event_info'


class Club_report(models.Model):
    """
    It has the details of the events given by the club for approval for the event.
    If it is approved then they give date,time etc.., in Event_info

    id - serial number
    club - name of the club
    event_name - name of the event
    incharge - name of faculty who is incharge for the event
    date - date of the event
    event_details - for which purpose they are conducting the event
    description - brief explanation about event if needed
    """
    id = models.AutoField(primary_key=True)
    club = models.ForeignKey(Club_info, on_delete=models.CASCADE, max_length=50, null=False)
    incharge = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, max_length=256, null=False)
    event_name = models.CharField(max_length=50, null=False)
    date = models.DateTimeField(max_length=50, default=timezone.now, blank=True)
    event_details = models.FileField(upload_to='uploads/', null=False)
    description = models.TextField(max_length=256, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'Club_report'


class Fest_budget(models.Model):
    """
    It has details regarding the budget for the fest.

    id - serial_number
    fest - name of the fest for which this budget required
    budget_amt - amount needed for the fest
    budget_file - It is a file which contains complete details regarding the budget that is going to spent for fest
    year - year in which the fest takes place
    description - brief explanation regarding budget if any
    status - whether budget is approved or rejected
    remarks - negative things regarding budget
    """
    id = models.AutoField(primary_key=True)
    fest = models.CharField(max_length=50, null=False, choices=FestChoices.choices)
    budget_amt = models.IntegerField(default=0, null=False)
    budget_file = models.FileField(upload_to='uploads/', null=False)
    year = models.CharField(max_length=10, null=True)
    description = models.TextField(max_length=256, null=False)
    status = models.CharField(max_length=50, choices=BudgetStatus.choices, default=BudgetStatus.OPEN)
    remarks = models.CharField(max_length=256, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'Fest_budget'


class Other_report(models.Model):
    """
    This model also stores details of the events conducting by all clubs irrespective of the clubs.

    id - serial number
    incharge - name of faculty who is incharge for the event
    date - date of the event
    event_details - for which purpose they are conducting the event
    description - brief explanation about event if needed
    """
    id = models.AutoField(primary_key=True)
    incharge = models.ForeignKey(ExtraInfo, on_delete=models.CASCADE, max_length=256, null=False)
    event_name = models.CharField(max_length=50, null=False)
    date = models.DateTimeField(max_length=50, default=timezone.now, blank=True)
    event_details = models.FileField(upload_to='uploads/', null=False)
    description = models.TextField(max_length=256, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'Other_report'


class Change_office(models.Model):
    """
    id - serial number
    club - name of the club
    co_ordinator - co_ordinator of the club
    co_coordinator - co_coordinator of the club
    status - whether it is confirmed or pending
    date_request - the date at which they requested to change
    date_approve - the date at which they approved to change
    remarks - remarks if there are any.
    """
    id = models.AutoField(primary_key=True)
    club = models.ForeignKey(Club_info, on_delete=models.CASCADE, max_length=50, null=False)
    co_ordinator = models.ForeignKey(User, on_delete=models.CASCADE, null=False, related_name='co_of')
    co_coordinator = models.ForeignKey(User, on_delete=models.CASCADE, null=False, related_name='coco_of')
    status = models.CharField(max_length=50, choices=ClubStatus.choices, default=ClubStatus.OPEN)
    date_request = models.DateTimeField(max_length=50, default=timezone.now, blank=True)
    date_approve = models.DateTimeField(max_length=50, blank=True)
    remarks = models.CharField(max_length=256, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'Change_office'


class Voting_polls(models.Model):
    """
    It shows the information about the voting poll.

    title - title of the poll
    description - explanation about the voting
    pub_date - the date at which polling starts
    exp_date - the date at which polling ends
    created_by - name of the person who created this poll
    groups - the groups that are participating in the voting
    """
    title = models.CharField(max_length=200, null=False)
    description = models.CharField(max_length=5000, null=False)
    pub_date = models.DateTimeField(default=timezone.now)
    exp_date = models.DateTimeField(default=timezone.now)
    created_by = models.CharField(max_length=100, null=True)
    groups = models.CharField(max_length=500, default='{}')
    
    def groups_data(self):
        return self.groups

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-pub_date']


class Voting_choices(models.Model):
    """
    poll_event - name of the poll_event
    title - name of the poll
    description - description about choices if any
    votes - no.of votes recorded
    """
    poll_event = models.ForeignKey(Voting_polls, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, null=False)
    description = models.CharField(max_length=500, default='')
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.title
    
    class Meta:
        get_latest_by = 'votes'


class Voting_voters(models.Model):
    """
    records students who has voted in the poll.

    poll_event - name of the poll
    student_id - roll number of student
    """
    poll_event = models.ForeignKey(Voting_polls, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=50, null=False)
    
    def __str__(self):
        return self.student_id