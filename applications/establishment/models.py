from pickle import TRUE
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from applications.globals.models import ExtraInfo, HoldsDesignation, Designation

class Constants:
    STATUS = (
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('adjustments_pending', 'Adjustments Pending'),
        ('finished', 'Finished'),
        ('outstanding', 'Outstanding'),
        ('excellant','Excellent'),
        ('very good','Very Good'),
        ('good','Good'),
        ('poor','Poor')
    )
    REVIEW_STATUS = (
        ('to_assign', 'To Assign'),
        ('under_review', 'Under Review'),
        ('reviewed', 'Reviewed')
    )
    LTC_TYPE = (
        ('hometown', 'Home Town'),
        ('elsewhere', 'Elsewhere')
    )
    LTC_TRAVEL = (
        ('rail', 'Rail'),
        ('road', 'Road')
    )
    LTC_LEAVE = (
        ('yes', 'Yes'),
        ('no', 'No')
    )
    APPRAISAL_PERMISSIONS = (
            ('intermediary', 'Intermediary Staff'),
            ('sanc_auth', 'Appraisal Sanctioning Authority'),
            ('sanc_off', 'Appraisal Sanctioning Officer'),
        )
    DESIGNATIONS = (
        ('academic', 'Academic Designation'),
        ('administrative', 'Administrative Designation'),
    )
    STATUS = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('forwarded', 'Forwarded'),
        ('auto rejected', 'Auto Rejected'),
        ('outstanding', 'Outstanding'),
        ('excellant','Excellent'),
        ('very good','Very Good'),
        ('good','Good'),
        ('poor','Poor')
    )



class Establishment_variables(models.Model):
    est_admin = models.ForeignKey(User, on_delete=models.CASCADE)


class Cpda_application(models.Model):
    status = models.CharField(max_length=20, null=True, choices=(
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('adjustments_pending', 'Adjustments Pending'),
        ('finished', 'Finished')))

    # CPDA Request fields
    applicant = models.ForeignKey(User, on_delete=models.CASCADE)
    pf_number = models.CharField(max_length=50, default='1',null=True)
    purpose = models.CharField(max_length=500, default='', blank=True)
    requested_advance = models.IntegerField(blank=True)
    request_timestamp = models.DateTimeField(auto_now=True, null=True)

    # CPDA Adjustment fields
    adjustment_amount = models.IntegerField(blank=True, null=True, default='0')
    bills_attached = models.IntegerField( blank=True, null=True, default='-1')
    total_bills_amount = models.IntegerField( blank=True, null=True, default='0')
    ppa_register_page_no = models.IntegerField( blank=True, null=True, default='-1')
    adjustment_timestamp = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return 'cpda id ' + str(self.id) + ', applied by ' + self.applicant.username

    class Meta:
        db_table = 'Cpda Application'


class Cpda_tracking(models.Model):
    application = models.OneToOneField(Cpda_application, primary_key=True, related_name='tracking_info',on_delete=models.CASCADE)
    reviewer_id = models.ForeignKey(User,related_name='reviewer1', null = True, blank=True, on_delete=models.CASCADE)
    reviewer_id2 = models.ForeignKey(User,related_name='reviewer2', null = True, blank=True, on_delete=models.CASCADE)
    reviewer_id3 = models.ForeignKey(User,related_name='reviewer3', null = True, blank=True, on_delete=models.CASCADE)
    current_reviewer_id= models.IntegerField(blank=True,default=1)
    reviewer_design = models.ForeignKey(Designation,related_name='desig1', null=True, blank=True, on_delete=models.CASCADE)
    reviewer_design2 = models.ForeignKey(Designation,related_name='desig2', null=True, blank=True, on_delete=models.CASCADE)
    reviewer_design3 = models.ForeignKey(Designation,related_name='desig3', null=True, blank=True, on_delete=models.CASCADE)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    remarks_rev1 = models.CharField(max_length=250, null=True, blank=True)
    remarks_rev2 = models.CharField(max_length=250, null=True, blank=True)
    remarks_rev3 = models.CharField(max_length=250, null=True, blank=True)
    review_status = models.CharField(max_length=20, null=True, choices=Constants.REVIEW_STATUS)
    bill = models.FileField(blank=True,null=True)

    def __str__(self):
        return 'cpda id ' + str(self.application.id) + ' tracking'

    class Meta:
        db_table = 'Cpda Tracking'
        
class CpdaBalance(models.Model):
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    cpda_balance=models.PositiveIntegerField(default=300000)

class Cpda_bill(models.Model):
    application = models.ForeignKey(Cpda_application, on_delete=models.CASCADE, null=True)
    bill = models.FileField(blank=True)

    def __str__(self):
        return 'cpda id ' + str(self.application.id) + ', bill id ' + str(self.id)

    class Meta:
        db_table = 'Cpda Bills'


class Ltc_application(models.Model):
    status = models.CharField(max_length=20, null=True, choices=(
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')))

    applicant = models.ForeignKey(User, on_delete=models.CASCADE)
    pf_number = models.CharField(max_length=50, default='')
    basic_pay = models.IntegerField(blank=True)
    leave_start = models.DateField(null=True)
    leave_end = models.DateField()
    family_departure_date = models.DateField()
    leave_nature = models.CharField(max_length=50, default='')
    purpose = models.CharField(max_length=500, default='', blank=True)
    is_hometown_or_elsewhere = models.CharField(choices=Constants.LTC_TYPE, max_length=50)
    phone_number = models.CharField(max_length=13, default='')
    address_during_leave = models.CharField(max_length=500, default='', blank=True)
    travel_mode = models.CharField(choices=Constants.LTC_TRAVEL, max_length=50)

    # details of family members that have already availed LTC
    ltc_availed = models.CharField(max_length=100, default='', blank=True)

    # details of family members who will avail LTC
    ltc_to_avail = models.CharField(max_length=200, default='', blank=True)

    # details of family members who are dependents of applicant
    dependents = models.CharField(max_length=500, default='', blank=True)

    requested_advance = models.IntegerField(blank=True)
    request_timestamp = models.DateTimeField(auto_now=True, null=True)
    review_timestamp = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return 'ltc id ' + str(self.id) + ', applied by ' + self.applicant.username

    class Meta:
        db_table = 'Ltc Application'




class Ltc_tracking(models.Model):
    application = models.OneToOneField(Ltc_application, primary_key=True, related_name='tracking_info',on_delete=models.CASCADE)
    reviewer_id = models.ForeignKey(User, null = True, blank=True, on_delete=models.CASCADE)
    reviewer_design = models.ForeignKey(Designation, null=True, blank=True, on_delete=models.CASCADE)
    designations=  models.CharField(max_length=350, null=True, blank=True)
    remarks = models.CharField(max_length=350, null=True, blank=True)
    review_status = models.CharField(max_length=20, null=True, choices=Constants.REVIEW_STATUS)
    admin_remarks=models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return 'ltc id ' + str(self.application.id) + ' tracking'

    class Meta:
        db_table = 'Ltc Tracking'

class Ltc_availed(models.Model):
    ltc = models.ForeignKey(Ltc_application, related_name='ltcAvailed',
                                    on_delete=models.CASCADE)
    name=models.CharField(max_length=30)
    age=models.IntegerField(blank=True, null=True)

class Ltc_to_avail(models.Model):
    ltc = models.ForeignKey(Ltc_application, related_name='ltcToAvail',
                                    on_delete=models.CASCADE)
    name=models.CharField(max_length=30)
    age=models.IntegerField(blank=True, null=True)

class Dependent(models.Model):
    ltc = models.ForeignKey(Ltc_application, related_name='Dependent',
                                    on_delete=models.CASCADE)
    name=models.CharField(max_length=30)
    age=models.IntegerField(blank=True, null=True)
    depend=models.CharField(max_length=30)


class Ltc_eligible_user(models.Model):
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    date_of_joining = models.DateField(default='2005-04-01')
    current_block_size = models.IntegerField(default=4)

    total_ltc_allowed = models.IntegerField(default=2)
    hometown_ltc_allowed = models.IntegerField(default=2)
    elsewhere_ltc_allowed = models.IntegerField(default=1)

    hometown_ltc_availed = models.IntegerField(default=0)
    elsewhere_ltc_availed = models.IntegerField(default=0)

    def get_years_of_job(self):
        ret = relativedelta(datetime.today().date(), self.date_of_joining)
        return "{:.2f}".format(ret.years + ret.months/12 + ret.days/365)

    def total_ltc_remaining(self):
        x=(self.hometown_ltc_allowed
            - self.hometown_ltc_availed+self.elsewhere_ltc_allowed
            - self.elsewhere_ltc_availed)
        x=max(x,0)
        return x

    def hometown_ltc_remaining(self):
        x=(self.hometown_ltc_allowed
            - self.hometown_ltc_availed)
        x=max(x,0)
        return x

    def elsewhere_ltc_remaining(self):
        x=(self.elsewhere_ltc_allowed
            - self.elsewhere_ltc_availed)
        x=max(x,0)
        return x

    def __str__(self):
        return str(self.user.username) + ' - joined on ' + str(self.date_of_joining)



class Appraisal(models.Model):
    """ Stores a single Appraisal application information of a person related to :model:`auth.User`. """
    applicant = models.ForeignKey(User, related_name='all_appraisals',
                                  on_delete=models.CASCADE)
    designation =models.ForeignKey(Designation, null=True,
                                related_name='desig', on_delete=models.SET_NULL)
    discipline= models.CharField(max_length=30,null=True)
    knowledge_field=models.CharField(max_length=30,null=True)
    research_interest=models.CharField(max_length=60,null=True)
    status = models.CharField(max_length=20, default='pending', choices=Constants.STATUS)
    timestamp = models.DateTimeField(auto_now=True, null=True)
    other_research_element = models.CharField(max_length=200, blank=True, null=True, default='')
    publications = models.CharField(max_length=200, blank=True, null=True, default='')
    conferences_meeting_attended = models.CharField(max_length=200, blank=True, null=True, default='')
    conferences_meeting_organized = models.CharField(max_length=200, blank=True, null=True, default='')
    admin_assign=models.CharField(max_length=200, blank=True, null=True, default='')
    sevice_to_ins=models.CharField(max_length=200, blank=True, null=True, default='')
    extra_info = models.CharField(max_length=200, blank=True, null=True, default='')
    faculty_comments= models.CharField(max_length=200, blank=True, null=True, default='')
    start_date = models.DateField(null=True,blank=True)
    end_date = models.DateField(null=True,blank=True)

    def __str__(self):
        return str(self.applicant.username) + ' -- ' + str(self.id)


class CoursesInstructed(models.Model):
    """ Stores the courses instructed by the user related to :model:'establishment.Appraisal' """
    appraisal = models.ForeignKey(Appraisal, related_name='applicant_courses',
                                    on_delete=models.CASCADE)
    semester=models.IntegerField(blank=True, null=True)
    course_name=models.CharField(max_length=30)
    course_num=models.IntegerField(blank=True, null=True)
    lecture_hrs_wk=models.FloatField(blank=True, null=True)
    tutorial_hrs_wk=models.FloatField(blank=True, null=True)
    lab_hrs_wk=models.FloatField(blank=True, null=True)
    reg_students=models.IntegerField(blank=True, null=True)
    co_instructor=models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return str(self.appraisal.applicant.username) + ' - Course Name: ' + str(self.course_name)


class NewCoursesOffered(models.Model):
    """ Stores the new courses offered by the user related to :model:'establishment.Appraisal' """
    appraisal = models.ForeignKey(Appraisal, related_name='applicants_offered_new_courses',
                                  on_delete=models.CASCADE)
    course_name = models.CharField(max_length=30)
    course_num=models.IntegerField(blank=True, null=True)
    ug_or_pg=models.CharField(max_length=2,blank=True, null=True)
    tutorial_hrs_wk=models.FloatField(blank=True, null=True)
    year=models.IntegerField(blank=True, null=True)
    semester=models.IntegerField()

    def __str__(self):
        return str(self.appraisal.applicant.username) + ' - Course Name: ' + str(self.course_name)


class NewCourseMaterial(models.Model):
    """ Stores the new course material prepared by the user related to :model:'establishment.Appraisal' """
    appraisal = models.ForeignKey(Appraisal, related_name='applicant_new_courses_material',
                                  on_delete=models.CASCADE)
    course_name = models.CharField(max_length=30)
    course_num=models.IntegerField(blank=True, null=True)
    ug_or_pg=models.CharField(max_length=2,blank=True, null=True)
    activity_type=models.CharField(max_length=10,blank=True, null=True)
    availiability=models.CharField(max_length=10,blank=True, null=True)

    def __str__(self):
        return str(self.appraisal.applicant.username) + ' - Course Name: ' + str(self.course_name)


class ThesisResearchSupervision(models.Model):
    """ Stores the thesis/research of students supervised by the user related to :model:'establishment.Appraisal' """
    appraisal = models.ForeignKey(Appraisal, related_name='applicants_supervised_stud',
                                  on_delete=models.CASCADE)
    stud_name = models.CharField(max_length=30)
    thesis_title=models.CharField(max_length=30,blank=True, null=True)
    year=models.IntegerField(blank=True, null=True)
    semester=models.IntegerField()
    status=models.CharField(max_length=30)
    co_supervisors=models.ForeignKey(User, related_name='all_supervisors',
                                  on_delete=models.CASCADE, blank=True,null=True)

    def __str__(self):
        return str(self.appraisal.applicant.username) + ' - Thesis Title: ' + str(self.thesis_title)


class SponsoredProjects(models.Model):
    """ Stores the projects sponsored by the user related to :model:'establishment.Appraisal' """
    appraisal = models.ForeignKey(Appraisal, related_name='applicant_sponsored_projects',
                                  on_delete=models.CASCADE)
    project_title=models.CharField(max_length=30)
    sponsoring_agency=models.CharField(max_length=30)
    funding=models.IntegerField()
    duration=models.IntegerField()
    co_investigators=models.ForeignKey(User, related_name='all_co_investigators',
                                  on_delete=models.CASCADE, blank=True,null=True)
    status=models.CharField(max_length=30)
    remarks=models.CharField(max_length=30)

    def __str__(self):
        return str(self.appraisal.applicant.username) + ' - Project Title: ' + str(self.project_title)


class AppraisalRequest(models.Model):
    """ Stores the appraisal request info of the user related to :model:'establishment.Appraisal' """
    appraisal=models.ForeignKey(Appraisal, related_name='appraisal_tracking', on_delete=models.CASCADE)
    hod = models.ForeignKey(User, related_name='hod', on_delete=models.CASCADE,null=True)
    director = models.ForeignKey(User, related_name='director', on_delete=models.CASCADE,null=True)
    remark_hod = models.CharField(max_length=50, blank=True, null=True)
    remark_director = models.CharField(max_length=50, blank=True, null=True)
    status_hod = models.CharField(max_length=20, default='pending', choices=Constants.STATUS)
    status_director = models.CharField(max_length=20, default='pending', choices=Constants.STATUS)
    permission = models.CharField(max_length=20, default='sanc_auth',
                                  choices=Constants.APPRAISAL_PERMISSIONS, blank=True,null=True)
    request_timestamp = models.DateTimeField(auto_now=True, null=True)

class AppraisalAdministrators(models.Model):
    """ Stores the appraisal administrators info and permissions related to :model:'auth.User' and :model:'globals.Designation' """
    user = models.OneToOneField(User, related_name='apprasial_admins', on_delete=models.CASCADE)
    authority = models.ForeignKey(Designation, null=True,
                                  related_name='sanc_authority_of_ap', on_delete=models.SET_NULL)
    officer = models.ForeignKey(Designation, null=True,
                                related_name='sanc_officer_of_ap', on_delete=models.SET_NULL)
