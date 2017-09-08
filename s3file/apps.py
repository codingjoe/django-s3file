from django.apps import AppConfig
from django.core.files.storage import default_storage

try:
    from storages.backends.s3boto3 import S3Boto3Storage
except ImportError:
    from storages.backends.s3boto import S3BotoStorage as S3BotoStorage


class S3FileConfig(AppConfig):
    name = 's3file'
    verbose_name = 'S3File'

    def ready(self):
        from django import forms

        if isinstance(default_storage, S3Boto3Storage):
            from .forms import S3FileInput

            forms.ClearableFileInput.__new__ = \
                lambda cls, *args, **kwargs: object.__new__(S3FileInput)
