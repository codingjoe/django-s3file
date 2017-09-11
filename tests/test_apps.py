import importlib

from django import forms

from s3file.apps import S3FileConfig
from s3file.forms import S3FileInputMixin


class TestS3FileConfig:
    def test_ready(self, settings):
        app = S3FileConfig('s3file', importlib.import_module('tests.testapp'))
        app.ready()
        assert not isinstance(forms.ClearableFileInput(), S3FileInputMixin)
        settings.DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
        app.ready()
        assert isinstance(forms.ClearableFileInput(), S3FileInputMixin)
