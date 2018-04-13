from django import forms

from .models import Exam_timetable, Meeting, Timetable


class MinuteForm(forms.ModelForm):
    """
    the form to add a new senate meeting minutes to the database.
    It consist of date and file upload

    @attrubutes:
        model - the model used is the Meeting class
        fields - the fields shown in the form for the user to fill up is date and file upload
        widgets - defining the id, required and placeholder of the filed in the form

    """
    class Meta:
        model = Meeting
        fields = ('date', 'minutes_file', )


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
        fields = ('year', 'programme', 'time_table',)


class ExamTimetableForm(forms.ModelForm):
    """
    the form to add a new eaxam timetable to the database.
    It consist of year, programme and exam timetable file

    @attrubutes:
        model - the model used is the Exan_timetable class
        fileds - the fields shown in the form for the user to fill up is year, programme and exam timtable file to upload
        widgets - defining the id, required and placeholder of the filed in the form

    """
    class Meta:
        model = Exam_timetable
        fields = ('year', 'programme', 'exam_time_table',)
