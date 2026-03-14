from django import forms

class StudentGradeForm(forms.Form):
    grades = forms.CharField(widget=forms.MultipleHiddenInput)
