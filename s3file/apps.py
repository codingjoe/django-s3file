from django.apps import AppConfig
from django.conf import settings


class S3FileConfig(AppConfig):
    name = 's3file'
    verbose_name = "S3File"

    def ready(self):
        from django.forms import FileField

        if hasattr(settings, 'AWS_SECRET_ACCESS_KEY') \
                and settings.AWS_SECRET_ACCESS_KEY:
            from .forms import S3FileInput

            FileField.widget = S3FileInput
