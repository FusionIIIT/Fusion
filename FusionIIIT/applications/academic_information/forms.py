from django import forms

from .models import Exam_timetable, Meeting, Timetable


class MinuteForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ('date', 'minutes_file', )


class AcademicTimetableForm(forms.ModelForm):
    class Meta:
        model = Timetable
        fields = ('year', 'programme', 'time_table',)


class ExamTimetableForm(forms.ModelForm):
    class Meta:
        model = Exam_timetable
        fields = ('year', 'programme', 'exam_time_table',)
