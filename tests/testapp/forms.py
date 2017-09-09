from django import forms

from .models import FileModel


class UploadForm(forms.ModelForm):
    class Meta:
        model = FileModel
        fields = ('file',)
