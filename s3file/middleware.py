import logging
import pathlib

from s3file.storages import local_dev, storage

from . import views

logger = logging.getLogger("s3file")


class S3FileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        file_fields = request.POST.getlist("s3file")
        for field_name in file_fields:
            paths = request.POST.getlist(field_name)
            request.FILES.setlist(field_name, list(self.get_files_from_storage(paths)))

        if local_dev and request.path == "/__s3_mock__/":
            return views.S3MockView.as_view()(request)

        return self.get_response(request)

    @staticmethod
    def get_files_from_storage(paths):
        """Return S3 file where the name does not include the path."""
        for path in paths:
            path = pathlib.PurePosixPath(path)
            try:
                location = storage.aws_location
            except AttributeError:
                location = storage.location
            try:
                f = storage.open(str(path.relative_to(location)))
                f.name = path.name
                yield f
            except (OSError, ValueError):
                logger.exception("File not found: %s", path)
