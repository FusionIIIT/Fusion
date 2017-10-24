from django import forms


class AddDocuments(forms.Form):
    doc = forms.FileField(required=True)
    description = forms.CharField(label='Description', max_length=100,
                                  widget=forms.TextInput(
                                      attrs={'placeholder': 'Enter Description'}))

    def __init__(self, *args, **kwargs):
        super(AddDocuments, self).__init__(*args, **kwargs)
        self.fields['doc'].widget.attrs.update({'accept': '.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx'})


class AddVideos(forms.Form):
    vid = forms.FileField(required=True)
    description = forms.CharField(label='Description', max_length=100,
                                  widget=forms.TextInput(
                                      attrs={'placeholder': 'Enter Description'}))

    def __init__(self, *args, **kwargs):
        super(AddVideos, self).__init__(*args, **kwargs)
        self.fields['vid'].widget.attrs.update({'accept': '.mp4,.3gp,.mpg,.mkv,.amv'})
