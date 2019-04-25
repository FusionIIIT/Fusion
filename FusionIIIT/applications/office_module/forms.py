from django import forms

from .models import *
from applications.academic_procedures.models import CoursesMtech


pro1 = Assigned_Teaching_credits.objects.all()
courseoptions = list()
courselist = CoursesMtech.objects.all()
for course in courselist:
	courseoptions.append(course)




class Constants:
  	COURSES = (
        ('Computer Graphics', 'Computer Graphics'),
        ('Machine Learning', 'Machine Learning'),
        ('Image Processing','Image Processing'),
        ('Data Structure','Data Structure')
    )


class Requisitionform(forms.ModelForm):
	class Meta:
		model=Requisitions
		fields=['title','department','building','description']


#Form to create an instance of Teaching Credits model 
#form used to validate clean data
class TeachingCreditsform(forms.ModelForm):
	roll_no = forms.CharField(label='Roll number of student', required=True)
	name = forms.CharField(label='Student name', required=True)
	programme = forms.CharField(label='programme', required=False)
	branch = forms.CharField(label='branch name', required=False)
	course1 = forms.ChoiceField(label='course choice 1', choices=courseoptions)
	course2 = forms.ChoiceField(label='courses choice 2', choices=courseoptions)
	course3 = forms.ChoiceField(label='courses choice 3', choices=courseoptions)
	tag = forms.IntegerField(initial='0')

	class Meta:
		model = Teaching_credits1
		fields=['roll_no','name','programme','branch','course1','course2','course3']
