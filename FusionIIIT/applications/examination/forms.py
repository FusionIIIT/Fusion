# forms.py
from django import forms
from .models import hidden_grades



class HiddenGradesForm(forms.ModelForm):
    class Meta:
        model = hidden_grades
        fields = ('student_id', 'course_id', 'semester_id', 'grade')
