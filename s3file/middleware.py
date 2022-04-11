import logging
import pathlib

from django.core import signing
from django.core.exceptions import PermissionDenied, SuspiciousFileOperation
from django.utils.crypto import constant_time_compare

from . import views
from .forms import S3FileInputMixin
from .storages import local_dev, storage

logger = logging.getLogger("s3file")


class S3FileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        file_fields = request.POST.getlist("s3file")
        for field_name in file_fields:

            paths = request.POST.getlist(field_name)
            if paths:
                try:
                    signature = request.POST[f"{field_name}-s3f-signature"]
                except KeyError:
                    raise PermissionDenied("No signature provided.")
                try:
                    request.FILES.setlist(
                        field_name, list(self.get_files_from_storage(paths, signature))
                    )
                except SuspiciousFileOperation as e:
                    raise PermissionDenied("Illegal file name!") from e

        if local_dev and request.path == "/__s3_mock__/":
            return views.S3MockView.as_view()(request)

        return self.get_response(request)

    @staticmethod
    def get_files_from_storage(paths, signature):
        """Return S3 file where the name does not include the path."""
        try:
            location = storage.aws_location
        except AttributeError:
            location = storage.location
        signer = signing.Signer(
            salt=f"{S3FileInputMixin.__module__}.{S3FileInputMixin.__name__}"
        )
        for path in paths:
            path = pathlib.PurePosixPath(path)
            print(path)
            print(signer.signature(path.parent), signature)
            if not constant_time_compare(signer.signature(path.parent), signature):
                raise PermissionDenied("Illegal signature!")
            try:
                relative_path = str(path.relative_to(location))
            except ValueError as e:
                raise SuspiciousFileOperation(
                    f"Path is not inside the designated upload location: {path}"
                ) from e

            try:
                f = storage.open(relative_path)
                f.name = path.name
                yield f
            except (OSError, ValueError):
                logger.exception("File not found: %s", path)
