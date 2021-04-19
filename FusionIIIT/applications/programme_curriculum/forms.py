from django import forms
from django.db.models import fields
from django.forms import ModelForm, widgets
from .models import Programme, Discipline, Curriculum, Semester, Course, Batch, CourseSlot


# class CurriculumSemester(forms.Form):
#     category = 
#     name = 
#     version = 
#     working_curriculum = 

class ProgrammeForm(ModelForm):
    class Meta:
        model = Programme
        fields = '__all__'
        widgets = {
            'category' : forms.Select(attrs={'class':'ui fluid search selection dropdown'}),
        } 

class DisciplineForm(ModelForm):
    class Meta:
        model = Discipline
        fields = '__all__'
        widgets = {
            'programmes' : forms.SelectMultiple(attrs={'class':'ui fluid search selection dropdown',
            'aria-placeholder': 'assign multiple Programmes to this Discipline'}),
        } 

class CurriculumForm(ModelForm):
    class Meta:
        model = Curriculum
        fields = '__all__'
        # widgets = {
        #     'programme': forms.ComboField(attrs={'class':'field'}),
        #     'name': forms.TextInput(attrs={'class':'field'}),
        #     'version': forms.NumberInput(attrs={'class':'field'}),
        #     'working_curriculum': forms.CheckboxInput(attrs={'class':'field'}),
        #     'no_of_semester': forms.NumberInput(attrs={'class':'field'})
        # }

class SemesterForm(ModelForm):
    class Meta:
        model = Semester
        fields = '__all__'

class CourseForm(ModelForm):
    class Meta:
        model = Course
        fields = '__all__'

class BatchForm(ModelForm):
    class Meta:
        model = Batch
        fields = '__all__'

class CourseSlotForm(ModelForm):
    class Meta:
        model = CourseSlot
        fields = '__all__'

