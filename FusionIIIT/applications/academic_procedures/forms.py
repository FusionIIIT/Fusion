from django import forms
from academic_information.models import Course
from datetime import datetime


class AddDropCourseForm(forms.ModelForm):

    def __init__ (self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(AddDropCourseForm, self).__init__ (*args, **kwargs)
        
    courses = forms.ModelChoiceField(queryset=Course.objects.all())