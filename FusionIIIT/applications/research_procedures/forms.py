from django import forms

from .models import *
from django.contrib.auth.models import User

# class ResearchGroupForm(forms.ModelForm):

#     students = forms.ModelMultipleChoiceField(queryset=User.objects.all(), widget=forms.SelectMultiple(attrs={'class':'ui fluid search dropdown'}))
#     faculty = forms.ModelMultipleChoiceField(queryset=User.objects.all(), widget=forms.SelectMultiple(attrs={'class':'ui fluid search dropdown'}))

#     def __init__(self, *args, **kwargs):
#         if kwargs.get('instance'):      
#             initial = kwargs.setdefault('initial', {})
#             initial['students_under_group'] = [t.pk for t in kwargs['instance'].students_under_group.all()]
#             initial['faculty_under_group'] = [t.pk for t in kwargs['instance'].faculty_under_group.all()]
        
#         forms.ModelForm.__init__(self, *args, **kwargs)

#     def save(self, commit=True):
#         instance = forms.ModelForm.save(self, False)

#         old_save_m2m = self.save_m2m
#         def save_m2m():
#             old_save_m2m()
#             instance.students_under_group.clear()
#             instance.students_under_group.add(*self.cleaned_data['students'])
#             instance.faculty_under_group.clear()
#             instance.faculty_under_group.add(*self.cleaned_data['faculty'])
#         self.save_m2m = save_m2m

#         if commit:
#             instance.save()
#             self.save_m2m()

#         return instance


#     class Meta:
#         model = ResearchGroup
#         fields = ('name','students','faculty','description',)