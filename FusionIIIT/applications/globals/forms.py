from django import forms

from applications.globals.models import Feedback, Issue


class WebFeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["feedback"]


class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ["module", "report_type", "title", "text"]
