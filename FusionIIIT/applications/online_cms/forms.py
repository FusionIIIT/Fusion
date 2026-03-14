# from django import forms
import datetime
from datetime import time, timedelta
#import information from the models 
from django import forms
# from .models import StoreMarks
from applications.academic_information.models import (Student_attendance,Timetable)


from .models import *
#the types of exam whose marks can be stored from edit marks in assessment, related to StoreMarks table in models
EXAM_TYPES= [
    ('quiz1', 'Quiz 1'),
    ('quiz2', 'Quiz 2'),
    ('midsem', 'Mid-Semester'),
    ('endsem', 'End-Semester'),
    ]
#form for storing the attendance of each student , related to 
class AttendanceForm(forms.Form):
    class Meta:
        model = Student_attendance              #form contains data about student and whether he is present or not
        fields = ('data', 'present',)

#form for generating quiz
class QuizForm(forms.Form): 

    name = forms.CharField(label='Quiz Name', max_length=20,   #store quiz name
                           widget=forms.TextInput(attrs={'placeholder': 'Name'}))  
    startdate = forms.DateTimeField(label='Start Date',
                                    widget=forms.SelectDateWidget(
                                        attrs={'placeholder': 'StartDate'}))  #date of when the quiz is started
    starttime = forms.TimeField(label='Start Time',
                                widget=forms.TimeInput(attrs={'placeholder': 'StartTime'}))
    enddate = forms.DateTimeField(label='End Date',
                                  widget=forms.SelectDateWidget(attrs={'placeholder': 'EndDate'}))
    endtime = forms.TimeField(label='End Time',
                              widget=forms.TimeInput(attrs={'placeholder': 'EndTime'}))
    negative_marks = forms.FloatField(label='Penalty', required=True, max_value = 0)    #it is the penalty and always take the negative value
    
        #description, rules and number of questions in the quiz are also stored 
    description = forms.CharField(label='description', max_length=1500,
                                  widget=forms.Textarea(attrs={'placeholder': 'Description'}))
    rules = forms.CharField(label='rules', max_length=1000,
                            widget=forms.Textarea(attrs={'placeholder': 'Description'}))
    number_of_questions = forms.IntegerField(label='Number Of Questions', min_value = 0)

    def clean(self):

        sdate = self.cleaned_data.get("startdate")
        stime = self.cleaned_data.get("starttime")
        print(sdate, "sdate")
        today = datetime.datetime.now() - timedelta(1)
        print(today, "today")
        k1 = stime.hour
        k2 = stime.minute
        k3 = stime.second
        x = time(k1, k2, k3)
        date = datetime.datetime.combine(sdate, x)
        edate = self.cleaned_data.get("enddate")
        etime = self.cleaned_data.get("endtime")
        k1 = etime.hour
        k2 = etime.minute
        k3 = etime.second
        end_date = datetime.datetime.combine(edate, time(k1, k2, k3))
        print(date, end_date)
        if(date < today):
            raise forms.ValidationError("Invalid quiz Start Date")
        elif(date > end_date):
            raise forms.ValidationError("Start Date but me before End Date")
        return self.cleaned_data

#form for the practice quiz( objective assignment)
class PracticeQuizForm(forms.Form): 

    name = forms.CharField(label='Practice Quiz Name', max_length=20,
                           widget=forms.TextInput(attrs={'placeholder': 'Name'}))
    negative_marks = forms.FloatField(label='Penalty', required=False)
    description = forms.CharField(label='description', max_length=1500,
                                  widget=forms.Textarea(attrs={'placeholder': 'Description'}))
    number_of_questions = forms.IntegerField(label='Number Of Questions')
    per_question_score = forms.IntegerField()

#to store the questions for quiz, related to  Question in models
class QuestionFormObjective(forms.Form):

    problem_statement = forms.CharField(label='Question', max_length=1000,
                                        widget=forms.Textarea(attrs={'placeholder': 'Description'}))
    image = forms.FileField(required=False)
    answer = forms.IntegerField(label='Answer',
                                widget=forms.Textarea(
                                                      attrs={'placeholder': 'Enter in between 1 & 5'}))
    option1 = forms.CharField(label='Option1', max_length=100)
    option2 = forms.CharField(label='Option2', max_length=100)
    option3 = forms.CharField(label='Option3', max_length=100,
                              required=False)
    option4 = forms.CharField(label='Option4', max_length=100,
                              required=False)
    option5 = forms.CharField(label='Option5', max_length=100,
                              required=False)
    score = forms.IntegerField(label='score')

    def __init__(self, *args, **kwargs):

        super(QuestionFormObjective, self).__init__(*args, **kwargs)
        self.fields['image'].widget.attrs.update({'accept': 'image/*'})

#form for storing marks details, related to StoreMarks table
class MarksForm(forms.Form):

    exam_type = forms.CharField(label='Exam Name', widget=forms.Select(choices=EXAM_TYPES))

    entered_marks = forms.FloatField(label='Marks', required=True)

    def clean(self):

        examtype = self.cleaned_data.get("exam_type")
        enteredmarks = self.cleaned_data.get("entered_marks")
        return self.cleaned_data

class GradingSchemeForm(forms.Form):
    quiz_weightage = forms.DecimalField(label='Quiz', max_digits=10, decimal_places=2)
    midsem_weightage = forms.DecimalField(label='Mid Semester', max_digits=10, decimal_places=2)
    assignment_weightage = forms.DecimalField(label='Assignment', max_digits=10, decimal_places=2)
    endsem_weightage = forms.DecimalField(label='End Semester', max_digits=10, decimal_places=2)
    project_weightage = forms.DecimalField(label='Project', max_digits=10, decimal_places=2)


class AcademicTimetableForm(forms.ModelForm):
    """
    the form to add a new academic timetable to the database.
    It consist of year, programme and the timetable file upload

    @attrubutes:
        model - the model used is the Timetable class
        fields - the fields shown in the form for the user to fill up is year, programme and timetable file upload
        widgets - defining the id, required and placeholder of the filed in the form

    """
    class Meta:
        model = Timetable
        fields = ('programme', 'batch', 'branch', 'time_table')
