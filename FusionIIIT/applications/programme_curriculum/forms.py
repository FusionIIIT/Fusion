from django import forms
from django.db.models import fields
from django.forms import ModelForm, widgets
<<<<<<< HEAD
from .models import Programme, Discipline, Curriculum, Semester, Course, Batch, CourseSlot, PROGRAMME_CATEGORY_CHOICES

=======
from django.forms import Form, ValidationError
from django.forms.models import ModelChoiceField
from .models import Programme, Discipline, Curriculum, Semester, Course, Batch, CourseSlot, PROGRAMME_CATEGORY_CHOICES
from django.utils.translation import gettext_lazy as _
>>>>>>> d3826989aebf1c9252035dd068f1af3ff791d9fe

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
<<<<<<< HEAD
=======
            'acronym' : forms.TextInput(attrs={'placeholder': 'xxx','max_length': 10,'class':'field'}), 
>>>>>>> d3826989aebf1c9252035dd068f1af3ff791d9fe

        }
        labels = {
            'name' : 'Discipline Name',
<<<<<<< HEAD
            'programmes': 'Link Programmes to this Disciplines'
        } 
=======
            'programmes': 'Link Programmes to this Disciplines',
            'acronym' : 'Enter Acronym'
        }

>>>>>>> d3826989aebf1c9252035dd068f1af3ff791d9fe

class CurriculumForm(ModelForm):
    class Meta:
        model = Curriculum
        fields = '__all__'
        widgets = {
<<<<<<< HEAD
            'name' : forms.TextInput(attrs={'placeholder': 'Enter New Discipline Name','max_length': 70,'class':'field'}),
=======
            'name' : forms.TextInput(attrs={'placeholder': 'Enter New Curriculum Name','max_length': 70,'class':'field'}),
>>>>>>> d3826989aebf1c9252035dd068f1af3ff791d9fe
            'programme' : forms.Select(attrs={'class':'ui fluid search selection dropdown',}),
            'version' : forms.NumberInput(attrs={'placeholder': 'Enter the latest version',' class': 'field'}, ),
            'working_curriculum' : forms.CheckboxInput(attrs={'class': 'ui checkbox'}),
            'no_of_semester' : forms.NumberInput(attrs={'placeholder': 'Enter the number of semesters',' class': 'field'}, ),
<<<<<<< HEAD
        }
        labels = {
            'name' : 'Curriculum Name',
            'programme' : 'Select Program for which Curriculum',
=======
            'min_credit' : forms.NumberInput(attrs={'placeholder': 'Minimum Number of Credits',' class': 'field'}, ),
        }
        labels = {
            'name' : 'Curriculum Name',
            'programme' : 'Select for which Programme',
>>>>>>> d3826989aebf1c9252035dd068f1af3ff791d9fe
            'version' : 'Enter Curriculum Version number',
            'working_curriculum' : 'Working Curriculum ?',
            'no_of_semester' : 'No of Semesters',
        }

<<<<<<< HEAD
class SemesterForm(ModelForm):
    class Meta:
        model = Semester
        fields = '__all__'

class CourseForm(ModelForm):
=======
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
                + cleaned_data.get("percent_course_attendance")
            )

        if percentages_sum != 100:
            msg = 'Percentages must add up to 100%, they currently add up to ' + str(percentages_sum) + '%'
            self.add_error('percent_quiz_1', msg)
            self.add_error('percent_midsem', msg)
            self.add_error('percent_quiz_2', msg)
            self.add_error('percent_endsem', msg)
            self.add_error('percent_project', msg)
            self.add_error('percent_course_attendance', msg)

        return cleaned_data

>>>>>>> d3826989aebf1c9252035dd068f1af3ff791d9fe
    class Meta:
        model = Course
        fields = '__all__'
        widgets = {
<<<<<<< HEAD
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
=======
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
            # 'evaluation_schema' : forms.Textarea(attrs={'placeholder': 'Text','class':'field'}), 
            'ref_books' : forms.Textarea(attrs={'placeholder': 'Text','class':'field'}),
            'percent_quiz_1' : forms.NumberInput(attrs={'placeholder': '%'}, ), 
            'percent_midsem' : forms.NumberInput(attrs={'placeholder': '%'}, ), 
            'percent_quiz_2' : forms.NumberInput(attrs={'placeholder': '%'}, ),
            'percent_endsem' : forms.NumberInput(attrs={'placeholder': '%'}, ),
            'percent_project' : forms.NumberInput(attrs={'placeholder': '%'}, ),
            'percent_course_attendance' : forms.NumberInput(attrs={'placeholder': '%'}, ),
>>>>>>> d3826989aebf1c9252035dd068f1af3ff791d9fe
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
<<<<<<< HEAD
            'syllabus' : 'Syllabus',
            'evaluation_schema' : 'Evaluation Schema', 
            'ref_books' : 'References & Books',
        }
=======
            'pre_requisit_courses' : 'Pre-requisit Courses',
            'syllabus' : 'Syllabus',
            # 'evaluation_schema' : 'Evaluation Schema', 
            'ref_books' : 'References & Books',
            'percent_quiz_1' : 'percent_quiz_1',
            'percent_midsem' : 'percent_midsem',
            'percent_quiz_2' : 'percent_quiz_2',
            'percent_endsem' : 'percent_endsem',
            'percent_project' : 'percent_project',
            'percent_course_attendance' : 'percent_course_attendance',
            'working_course' : 'working_course',
            'disciplines' : 'disciplines'
        }
        
>>>>>>> d3826989aebf1c9252035dd068f1af3ff791d9fe

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
<<<<<<< HEAD
=======

>>>>>>> d3826989aebf1c9252035dd068f1af3ff791d9fe
    class Meta:
        model = CourseSlot
        fields = '__all__'
        widgets = {
<<<<<<< HEAD
            'semester' : forms.Select(attrs={'class':'ui fluid search selection dropdown',}),
            'name' : forms.TextInput(attrs={'placeholder': '','max_length': 100,'class':'field'}),
            'type' : forms.Select(attrs={'class':'ui fluid search selection dropdown'},),
            'course_slot_info' : forms.Textarea(attrs={'placeholder': 'Enter Information about this Course Slot',}),
            'courses' : forms.SelectMultiple(attrs={'class':'ui fluid search selection dropdown',}),
=======
            'semester' : forms.Select(attrs={'class':'ui fluid search selection dropdown'},),
            'name' : forms.TextInput(attrs={'placeholder': 'Name/Code','max_length': 100,'class':'field'}),
            'type' : forms.Select(attrs={'class':'ui fluid search selection dropdown'},),
            'course_slot_info' : forms.Textarea(attrs={'placeholder': 'Enter Information about this Course Slot',}),
            'courses' : forms.SelectMultiple(attrs={'class':'ui fluid search selection dropdown',}),
            'duration' : forms.NumberInput(attrs={'placeholder': 'Semester Duration of Course/Project',}, ),
            'min_registration_limit' : forms.NumberInput(attrs={'placeholder': 'Minimum Course Slot Reg limit',}, ),
            'max_registration_limit' : forms.NumberInput(attrs={'placeholder': 'Maximum Course Slot Reg limit',}, ),
>>>>>>> d3826989aebf1c9252035dd068f1af3ff791d9fe
        }
        labels = {
            'semester' : 'Select Semester',
            'name' : 'Name of Course Slot',
            'type' : 'Type',
<<<<<<< HEAD
            'for_batches' : 'Select Batches',
            'course_slot_info' : 'Course Slot Info',
            'courses' : 'Add Courses into Course Slot',
=======
            'course_slot_info' : 'Course Slot Info',
            'courses' : 'Add Courses into Course Slot',
            'duration' : "Course/Project Duration",
            'min_registration_limit': 'Min Course Slot Registration Limit',
            'max_registration_limit': 'Max Course Slot Registration Limit',  
>>>>>>> d3826989aebf1c9252035dd068f1af3ff791d9fe
        }