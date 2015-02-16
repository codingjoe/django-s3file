# -*- coding:utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django import forms

from s3file.forms import AutoFileInput


class UploadForm(forms.Form):
    file = forms.FileField(widget=AutoFileInput())
