from django import forms
from django.db.models import fields
from django.forms import ModelForm, widgets
from django.forms import Form, ValidationError
from django.forms.models import ModelChoiceField
from .models import Programme, Discipline, Curriculum, Semester, Course, Batch, CourseSlot, PROGRAMME_CATEGORY_CHOICES,NewProposalFile,Proposal_Tracking
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from applications.globals.models import (DepartmentInfo, Designation,ExtraInfo, Faculty, HoldsDesignation)
from applications.filetracking.sdk.methods import *


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
            'version' : forms.NumberInput(attrs={'placeholder': 'Enter the latest version',' class': 'field','min': '1.0'}, ),
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
        
        # credits = cleaned_data.get("credit")
        
        if percentages_sum != 100:
            msg = 'Percentages must add up to 100%, they currently add up to ' + str(percentages_sum) + '%'
            self.add_error('percent_quiz_1', msg)
            self.add_error('percent_midsem', msg)
            self.add_error('percent_quiz_2', msg)
            self.add_error('percent_endsem', msg)
            self.add_error('percent_project', msg)
            self.add_error('percent_lab_evaluation', msg)
            self.add_error('percent_course_attendance', msg)
            
        # if credits==0:
        #     msg2="Credits can't be zero"
        #     self.add_error('credits', msg2)
        return cleaned_data
    class Meta:
        model = Course
        fields = '__all__'
        widgets = {
            'code' : forms.TextInput(attrs={'placeholder': 'Course Code','max_length': 10,}),
            'name' : forms.TextInput(attrs={'placeholder': 'Course/Project Name','max_length': 100,}),
            'version' : forms.NumberInput(attrs={'placeholder': 'version_no'}, ), 
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
            'version':'version',
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
        
        

#new
class NewCourseProposalFile(ModelForm):
    
    class Meta:
        model = NewProposalFile
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
            'uploader' : forms.TextInput(attrs={'readonly':'readonly'},),
            'designation' : forms.TextInput(attrs={'readonly':'readonly'},),
            'subject' : forms.Textarea(attrs={'placeholder': 'Subject','class':'field',}),
            'description' : forms.Textarea(attrs={'placeholder': 'Description','class':'field',}),
            'upload_date' : forms.TextInput(),
            
            
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
            'uploader' : 'Uploader name',
            'designation' : 'Uploader design',
            'subject' : 'title',
            'description' : 'Description',
            'upload_date' : '',
            
        }


class CourseProposalTrackingFile(ModelForm):
    
    class Meta:
        model = Proposal_Tracking 
        fields = '__all__'
        widgets = {
            'file_id' :forms.NumberInput(attrs={'placeholder': 'Course Proposal id','readonly':'readonly'}, ),
            'current_id' : forms.TextInput(attrs={'placeholder': 'Enter Uploader','class':'ui fluid search selection dropdown','readonly':'readonly'},),
            'current_design' : forms.TextInput(attrs={'class':'ui fluid search selection dropdown','readonly':'readonly'},),
            'receive_id' : forms.Select(attrs={'class':'ui fluid search selection dropdown',}),
            'receive_design' : forms.Select(attrs={'class':'ui fluid search selection dropdown',}),
            'disciplines' : forms.Select(attrs={'class':'ui fluid search selection dropdown',}),
            'remarks' : forms.Textarea(attrs={'placeholder': 'Remarks','class':'field',}),
        }
        labels = {
            'file_id' : 'file_id',
            'current_id' : 'Uploader name',
            'current_design' : 'Uploader design',
            'receive_id' : 'receiver name',
            'receive_design' : 'receiver design',
            'disciplines':'disciplines',
            'remarks' : 'remarks',
            
        }
        
    def clean(self):

        r_id = self.cleaned_data.get('receive_id')
        r_des = self.cleaned_data.get('receive_design')
        des=HoldsDesignation.objects.filter(user=r_id)
        print(des)
        data2=''
        msg1=''
        if des:
            data2 = ', '.join(str(i) for i in des)
            msg1 = f'{r_id} has only these working designations: {data2}'
            
        else:
            msg1=f'{r_id} has no working designations'
        data = HoldsDesignation.objects.select_related('designation').filter(user=r_id,designation=r_des)
        
        if not data:
            msg = 'Invalid reciever id and reciever designation'
            raise ValidationError({'receive_id': [msg, msg1]})
        
        name=""
        name = name+str(r_des)
        if "hod" in name.lower() :
            pass
        elif "professor" in name.lower() :
            pass
        elif "dean academic" in name.lower():
            pass
        else:
            msg3 = f"You can't send Proposal Form to the user  {r_id}-{r_des}"
            raise ValidationError({'receive_id': [msg3]})
            
        
        
        
        return self.cleaned_data
        
        
    # def sed(self):
    #     r_id = self.cleaned_data.get('receive_id')
    #     return r_id
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     des = HoldsDesignation.objects.select_related('working','designation').filter(user=5333)
    #     self.fields['receive_design'].queryset = Designation.objects.filter(id=list(des.designation))
        

    # def clean(self):
    #     cleaned_data = super().clean()
    #     user_id = cleaned_data.get('receive_id')
    #     if user_id:
    #         self.fields['receive_design'].queryset = HoldsDesignation.objects.select_related('designation').filter(user_id=user_id)
