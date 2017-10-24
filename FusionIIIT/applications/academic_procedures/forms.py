from django import forms

from applications.academic_information.models import Course


class AddDropCourseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(AddDropCourseForm, self).__init__(*args, **kwargs)

    courses = forms.ModelChoiceField(queryset=Course.objects.all())

    class Meta:
        model = Course
        fields = ('course_id', 'course_name', 'sem', 'credits', 'courses')
