from django.apps import AppConfig


class S3FileConfig(AppConfig):
    name = 's3file'
    verbose_name = 'S3File'

    def ready(self):
        from django.core.files.storage import default_storage
        from storages.backends.s3boto3 import S3Boto3Storage

        if isinstance(default_storage, S3Boto3Storage):
            from django import forms
            from .forms import S3FileInputMixin

            if S3FileInputMixin not in forms.ClearableFileInput.__bases__:
                forms.ClearableFileInput.__bases__ = \
                    (S3FileInputMixin,) + forms.ClearableFileInput.__bases__
