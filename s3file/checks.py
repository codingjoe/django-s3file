from django.core.checks import Error
from django.core.files.storage import FileSystemStorage, default_storage


def storage_check(app_configs, **kwargs):
    if isinstance(default_storage, FileSystemStorage):
        return [
            Error(
                'FileSystemStorage should not be used in a production environment.',
                hint='Please verify your DEFAULT_FILE_STORAGE setting.',
                id='s3file.E001',
            )
        ]
    return []
