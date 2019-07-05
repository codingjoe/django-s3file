import json
import logging
import os

from s3file.storages import local_dev, storage

from . import views

logger = logging.getLogger('s3file')


class S3FileMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        file_fields = json.loads(request.POST.get('s3file', '[]'))
        for field_name in file_fields:
            paths = json.loads(request.POST.get(field_name, '[]'))
            request.FILES.setlist(field_name, list(self.get_files_from_storage(paths)))

        if local_dev and request.path == '/__s3_mock__/':
            return views.S3MockView.as_view()(request)

        return self.get_response(request)

    @staticmethod
    def get_files_from_storage(paths):
        """Return S3 file where the name does not include the path."""
        for path in paths:
            if storage.location:
                path = path.replace(os.path.dirname(storage.location) + '/', '', 1)
            try:
                f = storage.open(path)
                f.name = os.path.basename(path)
                yield f
            except OSError:
                logger.exception("File not found: %s", path)
