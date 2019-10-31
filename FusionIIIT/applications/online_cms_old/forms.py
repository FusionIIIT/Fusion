import datetime
from datetime import time, timedelta

from django import forms


class QuizForm(forms.Form):

    name = forms.CharField(label='Quiz Name', max_length=20,
                           widget=forms.TextInput(attrs={'placeholder': 'Name'}))
    startdate = forms.DateTimeField(label='Start Date',
                                    widget=forms.SelectDateWidget(
                                        attrs={'placeholder': 'StartDate'}))
    starttime = forms.TimeField(label='Start Time',
                                widget=forms.TimeInput(attrs={'placeholder': 'StartTime'}))
    enddate = forms.DateTimeField(label='End Date',
                                  widget=forms.SelectDateWidget(attrs={'placeholder': 'EndDate'}))
    endtime = forms.TimeField(label='End Time',
                              widget=forms.TimeInput(attrs={'placeholder': 'EndTime'}))
    negative_marks = forms.FloatField(label='Penalty', required=False)
    description = forms.CharField(label='description', max_length=1500,
                                  widget=forms.Textarea(attrs={'placeholder': 'Description'}))
    rules = forms.CharField(label='rules', max_length=1000,
                            widget=forms.Textarea(attrs={'placeholder': 'Description'}))
    number_of_questions = forms.IntegerField(label='Number Of Questions')

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


class PracticeQuizForm(forms.Form):

    name = forms.CharField(label='Practice Quiz Name', max_length=20,
                           widget=forms.TextInput(attrs={'placeholder': 'Name'}))
    negative_marks = forms.FloatField(label='Penalty', required=False)
    description = forms.CharField(label='description', max_length=1500,
                                  widget=forms.Textarea(attrs={'placeholder': 'Description'}))
    number_of_questions = forms.IntegerField(label='Number Of Questions')
    per_question_score = forms.IntegerField()


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
