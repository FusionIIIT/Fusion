from django import forms
from django.db.models import fields
from django.forms import ModelForm, widgets
from django.forms import Form, ValidationError
from django.forms.models import ModelChoiceField
from .models import Programme, Discipline, Curriculum, Semester, Course, Batch, CourseSlot, PROGRAMME_CATEGORY_CHOICES
from django.utils.translation import gettext_lazy as _

class ProgrammeForm(ModelForm):
    class Meta:
        model = Programme
        fields = '__all__'
        widgets = {
            'category' : forms.Select(attrs={'class':'ui fluid search selection dropdown'},),
            'name' : forms.TextInput(attrs={'placeholder': 'Enter New Programme Name','max_length': 70,'class':'field'},),
        }
        labels = {
            'category' : 'Programme Category',
            'name': 'Programme Name'
        }

 
class DisciplineForm(ModelForm):
    class Meta:
        model = Discipline
        fields = '__all__'
        widgets = {
            'name' : forms.TextInput(attrs={'placeholder': 'Enter New Discipline Name','max_length': 70,'class':'field'}),
            'programmes' : forms.SelectMultiple(attrs={'class':'ui fluid search selection dropdown',}),
            'acronym' : forms.TextInput(attrs={'placeholder': 'xxx','max_length': 10,'class':'field'}), 

        }
        labels = {
            'name' : 'Discipline Name',
            'programmes': 'Link Programmes to this Disciplines',
            'acronym' : 'Enter Acronym'
        }


class CurriculumForm(ModelForm):
    class Meta:
        model = Curriculum
        fields = '__all__'
        widgets = {
            'name' : forms.TextInput(attrs={'placeholder': 'Enter New Curriculum Name','max_length': 70,'class':'field'}),
            'programme' : forms.Select(attrs={'class':'ui fluid search selection dropdown',}),
            'version' : forms.NumberInput(attrs={'placeholder': 'Enter the latest version',' class': 'field'}, ),
            'working_curriculum' : forms.CheckboxInput(attrs={'class': 'ui checkbox'}),
            'no_of_semester' : forms.NumberInput(attrs={'placeholder': 'Enter the number of semesters',' class': 'field'}, ),
            'min_credit' : forms.NumberInput(attrs={'placeholder': 'Minimum Number of Credits',' class': 'field'}, ),
        }
        labels = {
            'name' : 'Curriculum Name',
            'programme' : 'Select for which Programme',
            'version' : 'Enter Curriculum Version number',
            'working_curriculum' : 'Working Curriculum ?',
            'no_of_semester' : 'No of Semesters',
        }

class ReplicateCurriculumForm(ModelForm):
    
    name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter New Curriculum Name','max_length': 70,'class':'field'}),)
    programme = forms.ModelChoiceField(queryset=Programme.objects.all(), widget=forms.Select(attrs={'class':'ui fluid search selection dropdown',}),)
    version = forms.IntegerField(widget=forms.NumberInput(attrs={'placeholder': 'Enter the latest version',' class': 'field'}, ),)
    working_curriculum = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'ui checkbox'}),)
    no_of_semester = forms.IntegerField(widget=forms.NumberInput(attrs={'placeholder': 'Enter the number of semesters',' class': 'field'}, ),)
    min_credit = forms.IntegerField(widget=forms.NumberInput(attrs={'placeholder': 'Minimum Number of Credits',' class': 'field'}, ),)

    def clean(self):

        ver = self.cleaned_data.get('version')
        sem = self.cleaned_data.get('no_of_semester')

        if ver < 1: 
            msg = 'Version must be a positive number'
            self.add_error('version', msg)
        if sem < 1:
            msg = 'No of Semester must be a positive number'
            self.add_error('no_of_semester', msg)

        return self.cleaned_data

class SemesterForm(forms.Form):
    
    start_semester = forms.DateField(required=False, widget=forms.DateInput(attrs={'placeholder': 'Start'}), label='Semester Start Date')
    end_semester = forms.DateField(required=False, widget=forms.DateInput(attrs={'placeholder': 'End'}), label='Semester End Date')
    instigate_semester = forms.NullBooleanField(required=False, widget=forms.CheckboxInput(attrs={'tabindex':"0",'class':'hidden'}), label='Instigate This Semester')
    semester_info = forms.CharField(required=False, widget=forms.Textarea(attrs={'placeholder': 'Semester Information'}))

    def clean(self):

        start_date = self.cleaned_data.get('start_semester')
        end_date = self.cleaned_data.get('end_semester')

        if start_date != None and end_date != None:
            if start_date > end_date:
                msg = 'Start date should be before End Date'
                self.add_error('start_semester', msg)
                self.add_error('end_semester', msg)

        return self.cleaned_data

class CourseForm(ModelForm):
    
    def clean(self):
        cleaned_data = super().clean()

        percentages_sum = (
                cleaned_data.get("percent_quiz_1")
                + cleaned_data.get("percent_midsem")
                + cleaned_data.get("percent_quiz_2")
                + cleaned_data.get("percent_endsem")
                + cleaned_data.get("percent_project")
                + cleaned_data.get("percent_lab_evaluation")
                + cleaned_data.get("percent_course_attendance")
            )

        if percentages_sum != 100:
            msg = 'Percentages must add up to 100%, they currently add up to ' + str(percentages_sum) + '%'
            self.add_error('percent_quiz_1', msg)
            self.add_error('percent_midsem', msg)
            self.add_error('percent_quiz_2', msg)
            self.add_error('percent_endsem', msg)
            self.add_error('percent_project', msg)
            self.add_error('percent_lab_evaluation', msg)
            self.add_error('percent_course_attendance', msg)

        return cleaned_data

    class Meta:
        model = Course
        fields = '__all__'
        widgets = {
            'code' : forms.TextInput(attrs={'placeholder': 'Course Code','max_length': 10,}),
            'name' : forms.TextInput(attrs={'placeholder': 'Course/Project Name','max_length': 100,}),
            'credit' : forms.NumberInput(attrs={'placeholder': 'Course Credits',}, ), 
            'lecture_hours' : forms.NumberInput(attrs={'placeholder': 'Lecture hours',}, ), 
            'tutorial_hours' : forms.NumberInput(attrs={'placeholder': 'Tutorial hours',}, ), 
            'pratical_hours' : forms.NumberInput(attrs={'placeholder': 'Practical hours',}, ), 
            'discussion_hours' : forms.NumberInput(attrs={'placeholder': 'Group Discussion hours',}, ), 
            'project_hours' : forms.NumberInput(attrs={'placeholder': 'Project hours',}, ), 
            'working_course' : forms.CheckboxInput(attrs={'class': 'ui checkbox'}),
            'disciplines' : forms.SelectMultiple(attrs={'class':'ui fluid search selection dropdown',}),
            'pre_requisits' : forms.Textarea(attrs={'placeholder': 'Text','class':'field'}),
            'pre_requisit_courses' : forms.SelectMultiple(attrs={'class':'ui fluid search selection dropdown',}),
            'syllabus' : forms.Textarea(attrs={'placeholder': 'Text','class':'field'}),
            'ref_books' : forms.Textarea(attrs={'placeholder': 'Text','class':'field'}),
            'percent_quiz_1' : forms.NumberInput(attrs={'placeholder': '%'}, ), 
            'percent_midsem' : forms.NumberInput(attrs={'placeholder': '%'}, ), 
            'percent_quiz_2' : forms.NumberInput(attrs={'placeholder': '%'}, ),
            'percent_endsem' : forms.NumberInput(attrs={'placeholder': '%'}, ),
            'percent_project' : forms.NumberInput(attrs={'placeholder': '%'}, ),
            'percent_lab_evaluation' : forms.NumberInput(attrs={'placeholder': '%'}, ),
            'percent_course_attendance' : forms.NumberInput(attrs={'placeholder': '%'}, ),
        }
        labels = {
            'code' : 'Course Code',
            'name' : 'Course Name',
            'credit' : 'Credits',
            'lecture_hours' : 'Academic Loads', 
            'tutorial_hours' : '',
            'pratical_hours' : '',
            'discussion_hours' : '',
            'project_hours' : '',
            'pre_requisits' : 'Pre-requisits',
            'pre_requisit_courses' : 'Pre-requisit Courses',
            'syllabus' : 'Syllabus',
            'ref_books' : 'References & Books',
            'percent_quiz_1' : 'percent_quiz_1',
            'percent_midsem' : 'percent_midsem',
            'percent_quiz_2' : 'percent_quiz_2',
            'percent_endsem' : 'percent_endsem',
            'percent_project' : 'percent_project',
            'percent_lab_evaluation' : 'percent_lab_evaluation',
            'percent_course_attendance' : 'percent_course_attendance',
            'working_course' : 'working_course',
            'disciplines' : 'disciplines'
        }
        

class BatchForm(ModelForm):
    class Meta:
        model = Batch
        fields = '__all__'
        widgets = {
            'name' : forms.Select(attrs={'placeholder': 'Enter Unique Batch Name','class':'ui fluid search selection dropdown'},),
            'discipline' : forms.Select(attrs={'class':'ui fluid search selection dropdown'},),
            'year' : forms.NumberInput(attrs={'placeholder' : 'Enter Batch Year','class':'field'}),
            'curriculum' : forms.Select(attrs={'class':'ui fluid search selection dropdown'},),
        }
        labels = {
            'name' : 'Batch Name',
            'discipline' : 'Select Discipline',
            'year' : 'Batch Year',
            'curriculum' : 'Select Curriculum For Batch Students',
        }

class CourseSlotForm(ModelForm):

    class Meta:
        model = CourseSlot
        fields = '__all__'
        widgets = {
            'semester' : forms.Select(attrs={'class':'ui fluid search selection dropdown'},),
            'name' : forms.TextInput(attrs={'placeholder': 'Name/Code','max_length': 100,'class':'field'}),
            'type' : forms.Select(attrs={'class':'ui fluid search selection dropdown'},),
            'course_slot_info' : forms.Textarea(attrs={'placeholder': 'Enter Information about this Course Slot',}),
            'courses' : forms.SelectMultiple(attrs={'class':'ui fluid search selection dropdown',}),
            'duration' : forms.NumberInput(attrs={'placeholder': 'Semester Duration of Course/Project',}, ),
            'min_registration_limit' : forms.NumberInput(attrs={'placeholder': 'Minimum Course Slot Reg limit',}, ),
            'max_registration_limit' : forms.NumberInput(attrs={'placeholder': 'Maximum Course Slot Reg limit',}, ),
        }
        labels = {
            'semester' : 'Select Semester',
            'name' : 'Name of Course Slot',
            'type' : 'Type',
            'course_slot_info' : 'Course Slot Info',
            'courses' : 'Add Courses into Course Slot',
            'duration' : "Course/Project Duration",
            'min_registration_limit': 'Min Course Slot Registration Limit',
            'max_registration_limit': 'Max Course Slot Registration Limit',  
        }