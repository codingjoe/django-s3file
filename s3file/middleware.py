import logging
import pathlib

from django.core import signing
from django.core.exceptions import PermissionDenied, SuspiciousFileOperation
from django.utils.crypto import constant_time_compare

from . import views
from .storages import get_aws_location, local_dev, storage

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

    @classmethod
    def get_files_from_storage(cls, paths, signature):
        """Return S3 file where the name does not include the path."""
        location = get_aws_location()
        for path in paths:
            path = pathlib.PurePosixPath(path)
            if not constant_time_compare(
                cls.sign_s3_key_prefix(path.parent), signature
            ):
                raise PermissionDenied("Illegal signature!")
            try:
                relative_path = str(path.relative_to(location))
            except ValueError as e:
                raise SuspiciousFileOperation(
                    f"Path is outside the storage location: {path}"
                ) from e

            try:
                f = storage.open(relative_path)
                f.name = path.name
                yield f
            except (OSError, ValueError):
                logger.exception("File not found: %s", path)

    @classmethod
    def sign_s3_key_prefix(cls, path):
        """
        Signature to validate the S3 keys passed the middleware before fetching files.

        Return a base64-encoded HMAC-SHA256 of the upload folder aka the S3 key-prefix.
        """
        return signing.Signer(salt="s3file.middleware.S3FileMiddleware").signature(path)
