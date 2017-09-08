import importlib

from django.forms import ClearableFileInput

from s3file.apps import S3FileConfig
from s3file.forms import S3FileInput


class TestS3FileConfig:
    def test_ready(self, settings):
        app = S3FileConfig('s3file', __import__('tests.testapp'))
        app.ready()
        forms = importlib.import_module('django.forms')
        assert forms.FileField.widget == ClearableFileInput
        settings.DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
        app.ready()
        assert forms.FileField.widget == S3FileInput
