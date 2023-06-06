from django import forms

from s3file.forms import S3FileInputMixin

from .models import FileModel

if S3FileInputMixin not in forms.ClearableFileInput.__bases__:
    forms.ClearableFileInput.__bases__ = (
        S3FileInputMixin,
    ) + forms.ClearableFileInput.__bases__


class UploadForm(forms.ModelForm):
    class Meta:
        model = FileModel
        fields = ("file", "other_file")


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class MultiUploadForm(forms.Form):
    file = MultipleFileField(
        required=False, widget=MultipleFileInput(attrs={"multiple": True})
    )
    other_file = forms.FileField(required=False)
