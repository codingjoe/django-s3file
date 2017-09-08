from django import forms

from s3file.forms import S3FileInput

from .models import FileModel


class UploadForm(forms.ModelForm):
    class Meta:
        model = FileModel
        fields = ('file',)
        widgets = {
            'file': S3FileInput
        }
