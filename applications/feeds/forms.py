from django import forms
from pagedown.widgets import PagedownWidget

from .models import AnsweraQuestion, AskaQuestion, Comments, Profile


class CommentForm(forms.ModelForm):
	class Meta:
		model = Comments
		fields = ('comment_text',)

class AnswerForm(forms.ModelForm):
	content = forms.CharField(widget=PagedownWidget(attrs={"show_preview":False}))
	class Meta:
		model = AnsweraQuestion
		fields = [
			'content'
		]

class QuestionForm(forms.ModelForm):
	description = forms.CharField(widget=PagedownWidget(attrs={"show_preview":False}))
	class Meta:
		model = AskaQuestion
		fields = [
			'description',
		]

class ProfileForm(forms.ModelForm):
	profile_picture = forms.ImageField()
	bio = forms.CharField()
	class Meta:
		model = Profile
		fields = [
			'profile_picture',
			"bio"
		]