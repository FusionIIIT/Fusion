import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Constants:
    # Class for various choices on the enumerations
    SEX_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')
    )

    USER_CHOICES = (
        ('student', 'student'),
        ('staff', 'staff'),
        ('compounder', 'compounder'),
        ('faculty', 'faculty')
    )

    RATING_CHOICES = (
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
        (5, 5),
    )

    MODULES = (
        ("academic_information", "Academic"),
        ("central_mess", "Central Mess"),
        ("complaint_system", "Complaint System"),
        ("eis", "Employee Imformation System"),
        ("file_tracking", "File Tracking System"),
        ("health_center", "Health Center"),
        ("leave", "Leave"),
        ("online_cms", "Online Course Management System"),
        ("placement_cell", "Placement Cell"),
        ("scholarships", "Scholarships"),
        ("visitor_hostel", "Visitor Hostel"),
        ("other", "Other"),
    )

    ISSUE_TYPES = (
        ("feature_request", "Feature Request"),
        ("bug_report", "Bug Report"),
        ("security_issue", "Security Issue"),
        ("ui_issue", "User Interface Issue"),
        ("other", "Other than the ones listed"),
    )

    TITLE_CHOICES = (
        ("Mr.", "Mr."),
        ("Mrs.", "Mrs."),
        ("Ms.", "Ms."),
        ("Dr.", "Dr."),
        ("Professor", "Prof."),
        ("Shreemati", "Shreemati"),
        ("Shree", "Shree")
    )

    DESIGNATIONS = (
        ('academic', 'Academic Designation'),
        ('administrative', 'Administrative Designation'),
    )
    USER_STATUS = (
        ("NEW", "NEW"),
        ("PRESENT", "PRESENT"),
    )


class Designation(models.Model):
    '''
        Current Purpose : To store and segregate information regarding a designation in a the department  
        Eg : rewacaretaker -- Administrative designation

        ATTRIBUTES :

        name(char) - to store the designation name as information eg: dean_rspc
        full_name(char) - to store the full name of the designation eg: Dean(Research, Sponsered Projects and Consultancy)
        type(char) - to store the designation type eg: Academic designation
    '''
    name = models.CharField(max_length=50, unique=True,
                            blank=False, default='student')
    full_name = models.CharField(
        max_length=100, default='Computer Science and Engineering')

    type = models.CharField(
        max_length=30, default='academic', choices=Constants.DESIGNATIONS)

    def __str__(self):
        return self.name


class DepartmentInfo(models.Model):
    '''
        Current Purpose : To store the list of departments in the institute 
        Eg : CSE, ME, Finance etct
        ! - Disciplines(CSE,ECE,etc) and Departments(Finance,etc) are under the same table.
        ! - Can incorporate more attributes

        ATTRIBUTES :

        name(char) - to store the department name as information
    '''

    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return 'department: {}'.format(self.name)


class ExtraInfo(models.Model):
    '''
        Current Purpose : to store one to one mapping of information for each user under django.contrib.auth.User

        

        ATTRIBUTES :

        id(char) - primary key defined for augmenting extra information (is redundant)
        user(User) - one to one field for linking the extra information to the User
        title(char) - to store title of the personeg : Mr, Ms, Dr)
        sex(char) - to store the gender from SEX_CHOICES
        date_of_birth(DateTime) - Date of birth of user
        user_status(char) - Defines whether the user is new or is already part of the Institute
        address(char) - address of the user
        phone_no(BigInt) - the phone number of the user
        user_type(char) - type of user (eg : student, staff)
        department(DepartmentInfo) - to link a user to a department from DepartmentInfo table
        profile_picture(ImageField) - profile photo of the user
        about_me(text) - to store extra information of the user

    '''
    id = models.CharField(max_length=20, primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    title = models.CharField(
        max_length=20, choices=Constants.TITLE_CHOICES, default='Dr.')
    sex = models.CharField(
        max_length=2, choices=Constants.SEX_CHOICES, default='M')
    date_of_birth = models.DateField(default=datetime.date(1970, 1, 1))
    user_status = models.CharField(
        max_length=50, choices=Constants.USER_STATUS, default='PRESENT')
    address = models.TextField(max_length=1000, default="")
    phone_no = models.BigIntegerField(null=True, default=9999999999)
    user_type = models.CharField(max_length=20, choices=Constants.USER_CHOICES)
    department = models.ForeignKey(
        DepartmentInfo, on_delete=models.CASCADE, null=True, blank=True)
    profile_picture = models.ImageField(
        null=True, blank=True, upload_to='globals/profile_pictures')
    about_me = models.TextField(default='NA', max_length=1000, blank=True)
    date_modified = models.DateTimeField('date_updated', blank=True, null=True)
    last_selected_role = models.CharField(max_length=20, null=True, blank=True)

    @property
    def age(self):
        timedelta = timezone.now().date() - self.date_of_birth
        return int(timedelta.days / 365)

    def __str__(self):
        return '{} - {}'.format(self.id, self.user.username)


class HoldsDesignation(models.Model):
    """
    Purpose : Records designations held by users.

    ATTRIBUTES :
    'user' refers to the permanent/tenured holder of the designation.
    'working' always refers to the user who's holding the title, either permanently or temporarily
    Use 'working' to handle permissions in code

    'designation(Designation)' - maps the designation to the user 
    held_at(DateTime) - stores the time at which the position was held
    """
    user = models.ForeignKey(
        User, related_name='holds_designations', on_delete=models.CASCADE)
    working = models.ForeignKey(
        User, related_name='current_designation', on_delete=models.CASCADE)
    designation = models.ForeignKey(
        Designation, related_name='designees', on_delete=models.CASCADE)
    held_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['user', 'designation'], ['working', 'designation']]

    def __str__(self):
        return '{} - {}'.format(self.user.username, self.designation)


# TODO : ADD additional staff related fields when needed
class Staff(models.Model):
    '''
        Current Purpose : To store attributes relevant to a staff member 
        
        ! - Not complete yet

        ATTRIBUTES :

        id(ExtraInfo) - to establish attributes to a user
    '''
    id = models.OneToOneField(
        ExtraInfo, on_delete=models.CASCADE, primary_key=True)

    def __str__(self):
        return str(self.id)


# TODO : ADD additional employee related fields when needed
class Faculty(models.Model):
    '''
        Current Purpose : To store attributes relevant to a faculty 
        
        ! - Not complete yet

        ATTRIBUTES :

        id(ExtraInfo) - to establish attributes to a user
    '''
    id = models.OneToOneField(
        ExtraInfo, on_delete=models.CASCADE, primary_key=True)

        

    def __str__(self):
        return str(self.id)


""" Feedback and bug report models start"""


class Feedback(models.Model):
    '''
        Current Purpose : To store the feedback of a user 
        
        

        ATTRIBUTES :

        user(User) - the 1-1 attribute for the user who has given a feedback
        rating - the rating given by the user
        feedback(Text) - the descriptive feedback given by the user
        timestamp(DateTime) - to store when the feedback was registered
    '''


    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="fusion_feedback")
    rating = models.IntegerField(choices=Constants.RATING_CHOICES)
    feedback = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username + ": " + str(self.rating)


def Issue_image_directory(instance, filename):
    return 'issues/{0}/images/{1}'.format(instance.user.username, filename)


class IssueImage(models.Model):
    '''
        Current Purpose : To store images of an issue by a user 
        
        

        ATTRIBUTES :

        user(User) - to link the user who will upload the image
        image(Image) - the image of the issue
    '''
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=Issue_image_directory)


class Issue(models.Model):

    '''
        Current Purpose : To link an issue with issue images by a user and relevant details of the issue
        
        

        ATTRIBUTES :

        user(User) - to link the user who is reporting the issue
       report_type(char) - to store the issue type (eg: feature request, bug report etc ) 
       module(char) -  to store in which module the issue was found(eg : Academic, Mess etc)
       closed(boolean) -  to denote whether the issue has been resolved or not
       text(Text) -  textual description of the issue
       title(char) -  to store the title of the issue
       images(IssueImage) - reference to the images for the issue
       support(User) - manyTomany field to store the users who also support the issue
       timestamp(DateTime) - to keep track when the issue was first created
       added_on(DateTime) - to keep track of when the issue was last modified

    '''
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reported_issues")
    report_type = models.CharField(
        max_length=63, choices=Constants.ISSUE_TYPES)
    module = models.CharField(max_length=63, choices=Constants.MODULES)
    closed = models.BooleanField(default=False)
    text = models.TextField()
    title = models.CharField(max_length=255)
    images = models.ManyToManyField(IssueImage, blank=True)
    support = models.ManyToManyField(User, blank=True)
    timestamp = models.DateTimeField(auto_now=True)
    added_on = models.DateTimeField(auto_now_add=True)


""" End of feedback and bug report models"""



class ModuleAccess(models.Model):
    designation = models.CharField(max_length=155)
    program_and_curriculum = models.BooleanField(default=False)
    course_registration = models.BooleanField(default=False)
    course_management = models.BooleanField(default=False)
    other_academics = models.BooleanField(default=False)
    spacs = models.BooleanField(default=False)
    department = models.BooleanField(default=False)
    examinations = models.BooleanField(default=False)
    hr = models.BooleanField(default=False)
    iwd = models.BooleanField(default=False)
    complaint_management = models.BooleanField(default=False)
    fts = models.BooleanField(default=False)
    purchase_and_store = models.BooleanField(default=False)
    rspc = models.BooleanField(default=False)
    hostel_management = models.BooleanField(default=False)
    mess_management = models.BooleanField(default=False)
    gymkhana = models.BooleanField(default=False)
    placement_cell = models.BooleanField(default=False)
    visitor_hostel = models.BooleanField(default=False)
    phc = models.BooleanField(default=False)

    def __str__(self):
        return self.designation
