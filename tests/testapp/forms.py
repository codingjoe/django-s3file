# -*- coding:utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django import forms

from s3file.forms import AutoFileInput

from .models import FileModel


class UploadForm(forms.ModelForm):
    file = forms.FileField(widget=AutoFileInput, required=True)

    class Meta:
        model = FileModel
        fields = ('file',)
        widgets = {'file': AutoFileInput}


class ClearableUploadForm(forms.ModelForm):

    class Meta:
        model = FileModel
        fields = ('file',)
        widgets = {'file': AutoFileInput}
