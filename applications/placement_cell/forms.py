from django import forms

from applications.academic_information.models import Constants as Con
from applications.globals.models import DepartmentInfo

from .models import Constants, NotifyStudent, Skill


class AddProfile(forms.ModelForm):
    """
    The form is used to change profile picture of user.
    @variables:
            pic - chosen picture
    """
    pic = forms.ImageField()

class AddEducation(forms.Form):
    """
    The form is used to add education detail of user.
    @variables:
            institute - name of institute of previous education
            degree - name of previous degree
            grade - obtained grade
            stream - chosen stream for respective education
            sdate - start date of respective education
            edate - end date of respective education
    """
    institute = forms.CharField(widget=forms.TextInput(attrs={'max_length': 250,
                                                              'class': 'field'}),
                                label="institute")
    degree = forms.CharField(widget=forms.TextInput(attrs={'max_length': 40,
                                                           'class': 'field'}),
                             label="degree")
    grade = forms.CharField(widget=forms.TextInput(attrs={'max_length': 10,
                                                          'class': 'form-control'}),
                            label="grade")
    stream = forms.CharField(widget=forms.TextInput(attrs={'max_length': 150,
                                                           'class': 'form-control'}),
                             label="stream", required=False)
    sdate = forms.DateField(label='sdate', widget=forms.widgets.DateInput())
    edate = forms.DateField(label='edate', widget=forms.widgets.DateInput())


class AddSkill(forms.Form):
    """
    The form is used to skills in profile of user.
    @variables:
            skill - name of the skill user knows
            skill_rating - weightage of the skill he knows
    """
    skill = forms.CharField(widget=forms.TextInput(attrs={'max_length': 30,
                                                          'class': 'field'}),
                            label="skill")
    skill_rating = forms.IntegerField(label="skill_rating")


class AddCourse(forms.Form):
    """
    The form is used to add external courses that user has done.
    @variables:
            course_name - name of the course
            description - description of the course
            license_no - licence number of the course
            sdate - start date of the course
            edate - end date of the course
    """
    course_name = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100,
                                                                'class': 'field'}),
                                  label="course_name")
    description = forms.CharField(widget=forms.TextInput(attrs={'max_length': 250,
                                                                'class': 'field'}),
                                  label="description", required=False)
    license_no = forms.CharField(widget=forms.TextInput(attrs={'max_length': 250,
                                                                'class': 'field'}),
                                 label="license_no", required=False)
    sdate = forms.DateField(label='sdate', widget=forms.widgets.DateInput())
    edate = forms.DateField(label='edate', widget=forms.widgets.DateInput())


class AddExperience(forms.Form):
    """
    The form is used to add experience that useris having.
    @variables:
            title - title of the experience
            status - status of experience (ongoing/ended)
            description - description of the experience
            company - name of company where experience is gained
            location - location of the company
            sdate - start date of the company experience
            edate - end date of the company experience
    """
    title = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100,
                                                          'class': 'field'}),
                            label="title")
    status = forms.ChoiceField(choices = Constants.RESUME_TYPE, label="status",
                               widget=forms.Select(attrs={'style': "height:45px"}))
    description = forms.CharField(widget=forms.Textarea(attrs={'max_length': 500,
                                                                'class': 'form-control'}),
                                  label="description", required=False)
    company = forms.CharField(widget=forms.TextInput(attrs={'max_length': 200,
                                                            'class': 'form-control'}),
                              label="company")
    location = forms.CharField(widget=forms.TextInput(attrs={'max_length': 200,
                                                             'class': 'form-control'}),
                               label="location")
    sdate = forms.DateField(label='sdate', widget=forms.widgets.DateInput())
    edate = forms.DateField(label='edate', widget=forms.widgets.DateInput())


class AddProject(forms.Form):
    """
    The form is used to add project that user has done.
    @variables:
            project_name - name of the project
            project_status - status of the project (ongoing/ended)
            summary - summary of the project
            project_link - link of the project
            sdate - start date of the project
            edate - end date of the project
    """
    project_name = forms.CharField(widget=forms.TextInput(attrs={'max_length': 50,
                                                                 'class': 'field'}),
                                   label="title")
    project_status = forms.ChoiceField(choices = Constants.RESUME_TYPE, label="project_status",
                               widget=forms.Select())
    summary = forms.CharField(widget=forms.Textarea(attrs={'max_length': 1000,
                                                            'class': 'form-control'}),
                              label="summary", required=False)
    project_link = forms.CharField(widget=forms.TextInput(attrs={'max_length': 200,
                                                                 'class': 'form-control'}),
                                   label="project_link", required=False)
    sdate = forms.DateField(label='sdate', widget=forms.widgets.DateInput())
    edate = forms.DateField(label='edate', widget=forms.widgets.DateInput())


class AddAchievement(forms.Form):
    """
    The form is used to achievement that user has gained.
    @variables:
            achievement - name of the achievement
            achievement_type - type of achievement (educational/others)
            description - description of achievement
            issuer - issuer of achievement
            date_earned - date of earning of achievement
    """
    achievement = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100,
                                                                'class': 'field'}),
                                  label="achievement")
    achievement_type = forms.ChoiceField(choices = Constants.ACHIEVEMENT_TYPE,
                                         label="achievement_type", widget=forms.Select(attrs={'style': "height:45px"}))
    description = forms.CharField(widget=forms.Textarea(attrs={'max_length': 1000,
                                                                'class': 'form-control'}),
                                  label="description", required=False)
    issuer = forms.CharField(widget=forms.TextInput(attrs={'max_length': 200,
                                                                 'class': 'form-control'}),
                             label="issuer")
    date_earned = forms.DateField(label='date_earned', widget=forms.widgets.DateInput())


class AddPublication(forms.Form):
    """
    The form is used to add publications that user has published.
    @variables:
            publication_title - title of publication
            description - description of publication
            publisher - name of publisher
            publication_date - date of publication
    """
    publication_title = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100,
                                                                      'class': 'field'}),
                                        label="publication_title")
    description = forms.CharField(widget=forms.TextInput(attrs={'max_length': 250,
                                                                'class': 'form-control'}),
                                  label="description", required=False)
    publisher = forms.CharField(widget=forms.TextInput(attrs={'max_length': 250,
                                                              'class': 'form-control'}),
                                label="publisher")
    publication_date = forms.DateField(label='publication_date', widget=forms.widgets.DateInput())


class AddPatent(forms.Form):
    """
    The form is used to add patents that user has done.
    @variables:
            patent_name - name of the patent
            description - description of the patent
            patent_office - office from which patent has been done
            patent_date - date of patent
    """
    patent_name = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100,
                                                                'class': 'field'}),
                                  label="patent_name")
    description = forms.CharField(widget=forms.TextInput(attrs={'max_length': 250,
                                                                'class': 'form-control'}),
                                  label="description", required=False)
    patent_office = forms.CharField(widget=forms.TextInput(attrs={'max_length': 250,
                                                                  'class': 'form-control'}),
                                    label="patent_office")
    patent_date = forms.DateField(label='patent_date', widget=forms.widgets.DateInput())


class AddProfile(forms.Form):
    """
    The form is used to change profile section of user.
    @variables:
            about_me - about me about the user
            age - age of user
            address - address of user
    """
    about_me = forms.CharField(widget=forms.TextInput(attrs={'max_length': 250,
                                                              'class': 'field'}),
                                label="about_me", required=False)
    age = forms.IntegerField(label="age")
    address = forms.CharField(widget=forms.TextInput(attrs={'max_length': 250,
                                                          'class': 'form-control'}),
                            label="address")


class AddChairmanVisit(forms.Form):
    """
    The form is used to chairman visit schedule of user.
    @variables:
            company_name - name of company
            location - location of company
            description - description of company
            visiting_date - date of visiting
    """
    company_name = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100,
                                                              'class': 'field'}),
                                label="company_name")
    location = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100,
                                                           'class': 'field'}),
                             label="location")
    description = forms.CharField(widget=forms.Textarea(attrs={'max_length': 1000,
                                                          'class': 'form-control'}),
                            label="description")
    visiting_date = forms.DateField(label='visiting_date', widget=forms.widgets.DateInput())


class SearchStudentRecord(forms.Form):
    """
    The form is used to search from the student record based of various parameters.
    @variables:
            name - name of the student
            rollno - roll no of student
            programme - programme of student
            department - department of student
            cpi - cpi of student
            skill - skill of student
            debar - debarred or not debarred
            placed_type - type of placement
    """
    name = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100, 'class': 'field'}),
                           label="name", required=False)
    rollno = forms.IntegerField(label="rollno", required=False)
    programme = forms.ChoiceField(choices = Con.PROGRAMME, required=False,
                                  label="programme", widget=forms.Select(attrs={'style': "height:45px"}))
    department = forms.ChoiceField(choices = Constants.DEP, required=False,
                                  label="department", widget=forms.Select(attrs={'style': "height:45px"}))
    cpi = forms.DecimalField(label="cpi", required=False)
    skill = forms.ModelMultipleChoiceField(required=False, widget=forms.SelectMultiple(),
                                           queryset=Skill.objects.all(), label="skill")
    debar = forms.ChoiceField(widget=forms.Select(attrs={'style': "height:45px"}), label="debar", required=False,
                              choices=Constants.DEBAR_TYPE)
    placed_type = forms.ChoiceField(widget=forms.Select(attrs={'style': "height:45px"}), label="placed_type", required=False,
                                    choices=Constants.PLACED_TYPE)


class SendInvite(forms.Form):
    """
    The form is used to send invite to students about upcoming placement or pbi events.
    @variables:
            company - name of company
    """
    company = forms.ModelChoiceField(required=True, queryset=NotifyStudent.objects.all(), label="company")


class AddSchedule(forms.Form):
    """
    The form is used to placement or pbi schedule.
    @variables:
            time - time of placement activity
            ctc - salary
            company_name - name of company
            placement_type - placement type (placement/pbi)
            location - location of company
            description - description of company
            placement_date - date of placement activity
    """
    time = forms.TimeField(label='time', widget=forms.widgets.TimeInput(attrs={'type': "time",
                                                                                'value':"00:00",
                                                                                'min':"0:00",
                                                                                'max':"18:02"}))
    ctc = forms.DecimalField(label="ctc")
    company_name = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100,
                                                              'class': 'field'}),
                                   label="company_name")
    placement_type = forms.ChoiceField(widget=forms.Select(attrs={'style': "height:45px"}), label="placement_type",
                                       choices=Constants.PLACEMENT_TYPE)
    location = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100,
                                                           'class': 'field'}),
                               label="location")
    description = forms.CharField(widget=forms.Textarea(attrs={'max_length': 1000,
                                                          'class': 'form-control'}),
                                  label="description", required=False)
    attached_file = forms.FileField()

    placement_date = forms.DateField(label='placement_date', widget=forms.widgets.DateInput())


class SearchPlacementRecord(forms.Form):
    """
    The form is used to search from placement records based of various parameters.
    @variables:
            stuname - name of the student
            year - year of placement
            ctc - salary
            roll - roll no of student
            cname - name of company
    """
    stuname = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100,
                                                              'class': 'field'}),
                              label="stuname", required=False)
    year = forms.IntegerField(label="year", required=False)
    ctc = forms.DecimalField(label="ctc", required=False)
    roll = forms.CharField(widget=forms.TextInput(attrs={'max_length': 10,
                                                          'class': 'form-control'}),
                           label="roll", required=False)
    cname = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100,
                                                              'class': 'field'}),
                            label="cname", required=False)


class SearchPbiRecord(forms.Form):
    """
    The form is used to search from pbi record.
    @variables:
            stuname - name of student
            year - year of pbi
            ctc - stipend
            roll - roll no of student
            cname - name of company
    """
    stuname = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100,
                                                            'class': 'field'}),
                              label="stuname", required=False)
    year = forms.IntegerField(label="year", required=False)
    ctc = forms.DecimalField(label="ctc", required=False)
    roll = forms.CharField(widget=forms.TextInput(attrs={'max_length': 10,
                                                          'class': 'form-control'}),
                           label="roll", required=False)
    cname = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100,
                                                            'class': 'field'}),
                            label="cname", required=False)


class SearchHigherRecord(forms.Form):
    """
    The form is used to search from higher study record based on various parameters .
    @variables:
            roll - roll no of the student
            stuname - name of the student
            test_type - type of test for higher study
            test_score - score in the test
            year -year of clearing the test
            uname - name of the university
    """
    roll = forms.CharField(widget=forms.TextInput(attrs={'max_length': 10,
                                                          'class': 'form-control'}),
                           label="roll", required=False)
    stuname = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100,
                                                            'class': 'field'}),
                              label="stuname", required=False,
                              help_text="Only for searching records")
    test_type = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100,
                                                            'class': 'field'}),
                                label="test_type", required=False)
    test_score = forms.IntegerField(label="test_score", required=False)
    year = forms.IntegerField(label="year", required=False)
    uname = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100,
                                                            'class': 'field'}),
                            label="uname", required=False)


class ManagePlacementRecord(forms.Form):
    """
    The form is used to manage placement records in the database by searching based on given parameters.
    @variables:
            stuname - name of the student
            roll - roll no of student
            company - company name
            ctc - salary
    """
    stuname = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100,
                                                              'class': 'field'}),
                              label="stuname", required=False)
    roll = forms.CharField(widget=forms.TextInput(attrs={'max_length': 10,
                                                          'class': 'form-control'}),
                           label="roll", required=False)
    company = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100,
                                                              'class': 'field'}),
                              label="company", required=False)
    ctc = forms.IntegerField(label="ctc", required=False)


class ManagePbiRecord(forms.Form):
    """
    The form is used to manage pbi records in the database  by searching based on given parameters.
    @variables:
            stuname - name of student
            roll - roll no of student
            company - company name
            ctc - stipent that company is giving
    """
    stuname = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100,
                                                              'class': 'field'}),
                                label="stuname", required=False)
    roll = forms.CharField(widget=forms.TextInput(attrs={'max_length': 10,
                                                          'class': 'form-control'}),
                            label="roll", required=False)
    company = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100,
                                                              'class': 'field'}),
                                label="company", required=False)
    ctc = forms.IntegerField(label="ctc", required=False)


class ManageHigherRecord(forms.Form):
    """
    The form is used to manage Higher Study records in the database by searching based on given parameters.
    @variables:
            stuname - name of student
            roll - roll no of student
            test_type - type of test
            company - name of university
            test_score - score in the test
    """
    stuname = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100,
                                                              'class': 'field'}),
                                label="stuname", required=False)
    roll = forms.CharField(widget=forms.TextInput(attrs={'max_length': 10,
                                                          'class': 'form-control'}),
                            label="roll", required=False)
    test_type = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100,
                                                              'class': 'field'}),
                                label="test_type", required=False)
    company = forms.CharField(widget=forms.TextInput(attrs={'max_length': 100,
                                                              'class': 'field'}),
                                label="company", required=False)
    test_score = forms.IntegerField(label="test_score", required=False)
