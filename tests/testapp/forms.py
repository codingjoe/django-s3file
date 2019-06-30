from django import forms

from s3file.forms import S3FileInputMixin

from .models import FileModel

if S3FileInputMixin not in forms.ClearableFileInput.__bases__:
    forms.ClearableFileInput.__bases__ = \
        (S3FileInputMixin,) + forms.ClearableFileInput.__bases__


class UploadForm(forms.ModelForm):
    class Meta:
        model = FileModel
        fields = ('file', 'other_file')
        widgets = {
            'file': forms.ClearableFileInput(attrs={'multiple': True}),
        }
