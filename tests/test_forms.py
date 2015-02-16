# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.forms import ClearableFileInput

from s3file.forms import AutoFileInput, S3FileInput


class TestAutoFileInput(object):
    def test_std_file_input(self, settings):
        settings.AWS_SECRET_ACCESS_KEY = None
        assert isinstance(AutoFileInput(), ClearableFileInput), "Should be an ClearableFileInput"

    def test_s3_file_input(self, settings):
        settings.AWS_SECRET_ACCESS_KEY = 'SuperSecretKey'
        assert isinstance(AutoFileInput(), S3FileInput), "Should be a S3FileInput"
