from django import forms
from .models import HostelNoticeBoard, Hall


class HostelNoticeBoardForm(forms.ModelForm):
    class Meta:
        model = HostelNoticeBoard
        fields = ('hall', 'head_line', 'content', 'description')
       