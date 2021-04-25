from django import forms
from django.db.models import fields
from django.forms import ModelForm, widgets
from .models import Programme, Discipline, Curriculum, Semester, Course, Batch, CourseSlot, PROGRAMME_CATEGORY_CHOICES


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

        }
        labels = {
            'name' : 'Discipline Name',
            'programmes': 'Link Programmes to this Disciplines'
        } 

class CurriculumForm(ModelForm):
    class Meta:
        model = Curriculum
        fields = '__all__'
        widgets = {
            'name' : forms.TextInput(attrs={'placeholder': 'Enter New Discipline Name','max_length': 70,'class':'field'}),
            'programme' : forms.Select(attrs={'class':'ui fluid search selection dropdown',}),
            'version' : forms.NumberInput(attrs={'placeholder': 'Enter the latest version',' class': 'field'}, ),
            'working_curriculum' : forms.CheckboxInput(attrs={'class': 'ui checkbox'}),
            'no_of_semester' : forms.NumberInput(attrs={'placeholder': 'Enter the number of semesters',' class': 'field'}, ),
        }
        labels = {
            'name' : 'Curriculum Name',
            'programme' : 'Select Program for which Curriculum',
            'version' : 'Enter Curriculum Version number',
            'working_curriculum' : 'Working Curriculum ?',
            'no_of_semester' : 'No of Semesters',
        }

class SemesterForm(ModelForm):
    class Meta:
        model = Semester
        fields = '__all__'

class CourseForm(ModelForm):
    class Meta:
        model = Course
        fields = '__all__'
        widgets = {
            'code' : forms.TextInput(attrs={'placeholder': 'Enter Course Code','max_length': 10,'class':'field'}),
            'name' : forms.TextInput(attrs={'placeholder': 'Enter Course Name','max_length': 100,'class':'field'}),
            'credit' : forms.NumberInput(attrs={'placeholder': 'Enter Course Credits',' class': 'field'}, ), 
            'lecture_hours' : forms.NumberInput(attrs={'placeholder': 'Lecture hours',' class': 'field'}, ), 
            'tutorial_hours' : forms.NumberInput(attrs={'placeholder': 'Tutorial hours',' class': 'field'}, ), 
            'pratical_hours' : forms.NumberInput(attrs={'placeholder': 'Practical hours',' class': 'field'}, ), 
            'discussion_hours' : forms.NumberInput(attrs={'placeholder': 'Discussion hours',' class': 'field'}, ), 
            'project_hours' : forms.NumberInput(attrs={'placeholder': 'Project hours',' class': 'field'}, ), 
            'pre_requisits' : forms.Textarea(attrs={'placeholder': 'Text','class':'field'}),
            'syllabus' : forms.Textarea(attrs={'placeholder': 'Text','class':'field'}),
            'evaluation_schema' : forms.Textarea(attrs={'placeholder': 'Text','class':'field'}), 
            'ref_books' : forms.Textarea(attrs={'placeholder': 'Text','class':'field'}),
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
            'syllabus' : 'Syllabus',
            'evaluation_schema' : 'Evaluation Schema', 
            'ref_books' : 'References & Books',
        }

class BatchForm(ModelForm):
    class Meta:
        model = Batch
        fields = '__all__'
        widgets = {
            'name' : forms.TextInput(attrs={'placeholder': 'Enter Unique Batch Name','max_length': 50,'class':'field'}),
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
            'semester' : forms.Select(attrs={'class':'ui fluid search selection dropdown',}),
            'name' : forms.TextInput(attrs={'placeholder': '','max_length': 100,'class':'field'}),
            'type' : forms.Select(attrs={'class':'ui fluid search selection dropdown'},),
            'course_slot_info' : forms.Textarea(attrs={'placeholder': 'Enter Information about this Course Slot',}),
            'courses' : forms.SelectMultiple(attrs={'class':'ui fluid search selection dropdown',}),
        }
        labels = {
            'semester' : 'Select Semester',
            'name' : 'Name of Course Slot',
            'type' : 'Type',
            'for_batches' : 'Select Batches',
            'course_slot_info' : 'Course Slot Info',
            'courses' : 'Add Courses into Course Slot',
        }