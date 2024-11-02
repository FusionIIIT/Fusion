import django_filters
from django import forms
from .models import Programme, Discipline, Curriculum, Semester, Course, Batch, CourseSlot, PROGRAMME_CATEGORY_CHOICES,CourseInstructor

class CourseFilter(django_filters.FilterSet):
    class Meta:
        model = Course
        fields = {'code': ['icontains'],
                  'name': ['icontains'],
                  'version': ['exact'],
		          'working_course': ['exact'],
                  'disciplines': ['exact'],
                 }
        widgets = {
            'code' : django_filters.CharFilter(forms.TextInput(attrs={'placeholder': 'Course Code','max_length': 10,})),
            'name' : forms.TextInput(attrs={'placeholder': 'Course/Project Name','max_length': 100,}),
            'name' : django_filters.CharFilter(forms.TextInput(attrs={'placeholder': 'Course/Project Name','max_length': 100,})),
            'code' : django_filters.CharFilter(forms.TextInput(attrs={'placeholder': 'Version','max_length': 10,})),
            'working_course' : django_filters.CharFilter(forms.CheckboxInput(attrs={'class': 'ui checkbox'})),
            'disciplines' : django_filters.CharFilter(forms.SelectMultiple(attrs={'class':'ui fluid search selection dropdown',})),
        }

class BatchFilter(django_filters.FilterSet):
    class Meta:
        model = Batch
        fields = {'name': ['icontains'],
                  'year': ['icontains'],
                  'curriculum': ['exact'],
		          'running_batch': ['exact'],
                  'discipline': ['exact'],
                 }

class CurriculumFilter(django_filters.FilterSet):
    class Meta:
        model = Curriculum
        fields = {'name': ['icontains'],
                  'version': ['exact'],
                 }
        widgets = {
                'name' : forms.TextInput(attrs={'placeholder': 'Course/Project Name','max_length': 100,}),
                'name' : django_filters.CharFilter(forms.TextInput(attrs={'placeholder': 'Course/Project Name','max_length': 100,})),
                'code' : django_filters.CharFilter(forms.TextInput(attrs={'placeholder': 'Version','max_length': 10,})),
            }
        
class CourseInstructorFilter(django_filters.FilterSet):
    course_id = django_filters.CharFilter(field_name='course_id__code', lookup_expr='icontains', label='Course Code')  # Course code filter
    instructor_id = django_filters.CharFilter(field_name='instructor_id__id', lookup_expr='icontains', label='Instructor Name')  # Assuming 'username' field in related faculty model
    batch_id = django_filters.CharFilter(field_name='batch_id__name', lookup_expr='icontains', label='Programme')  # Batch name, adjust if necessary
    year = django_filters.NumberFilter(field_name='batch_id__year', lookup_expr='exact', label='Year')  # Year filter
    discipline_acronym = django_filters.CharFilter(field_name='batch_id__discipline__acronym', lookup_expr='icontains', label='Branch')  # Discipline acronym filter

    class Meta:
        model = CourseInstructor
        fields = ['course_id', 'instructor_id', 'batch_id', 'year', 'discipline_acronym']
