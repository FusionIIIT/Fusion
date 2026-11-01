from django import forms

from .models import Announcement, Assignment, Material, Submission, Workspace


class UploadForm(forms.ModelForm):
    def clean_file(self):
        value = self.cleaned_data.get('file')
        if value and value.size > 10 * 1024 * 1024:
            raise forms.ValidationError('The upload limit is 10 MB.')
        return value


class WorkspaceForm(forms.ModelForm):
    class Meta:
        model = Workspace
        fields = ['syllabus', 'schedule']


class MaterialForm(UploadForm):
    publish = forms.BooleanField(required=False)

    class Meta:
        model = Material
        fields = ['title', 'section', 'kind', 'text', 'link', 'file', 'release_at']

    def clean(self):
        data = super().clean()
        field = {'text': 'text', 'link': 'link', 'file': 'file'}.get(data.get('kind'))
        if field and not data.get(field):
            self.add_error(field, 'Provide the selected material content.')
        return data


class AssignmentForm(UploadForm):
    class Meta:
        model = Assignment
        fields = ['title', 'instructions', 'submission_type', 'points_possible', 'due_at', 'release_at', 'file']

    def clean(self):
        data = super().clean()
        points = data.get('points_possible')
        if points is not None and points <= 0:
            self.add_error('points_possible', 'Points possible must be positive.')
        if data.get('release_at') and data.get('due_at') and data['release_at'] >= data['due_at']:
            self.add_error('release_at', 'Release must precede the due date.')
        return data


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'body']


class SubmissionForm(UploadForm):
    class Meta:
        model = Submission
        fields = ['text', 'link', 'file']


class GradeForm(forms.Form):
    points = forms.DecimalField(min_value=0, max_digits=8, decimal_places=2)
    feedback = forms.CharField(widget=forms.Textarea, required=False, max_length=10000)
    revision = forms.IntegerField(min_value=1)
