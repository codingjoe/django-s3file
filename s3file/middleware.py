import logging
import pathlib

from django.core import signing
from django.core.exceptions import PermissionDenied, SuspiciousFileOperation
from django.http.multipartparser import MultiPartParser
from django.utils.crypto import constant_time_compare
from storages.utils import clean_name

from . import views
from .storages import get_aws_location, local_dev, storage

logger = logging.getLogger("s3file")


class S3FileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        file_fields = request.POST.getlist("s3file")
        for field_name in file_fields:
            if paths := request.POST.getlist(field_name):
                try:
                    signature = request.POST[f"{field_name}-s3f-signature"]
                except KeyError:
                    raise PermissionDenied("No signature provided.")
                try:
                    request.FILES.setlist(
                        field_name, list(self.get_files_from_storage(paths, signature))
                    )
                except SuspiciousFileOperation as e:
                    raise PermissionDenied("Illegal filename!") from e

        if local_dev and request.path == "/__s3_mock__/":
            return views.S3MockView.as_view()(request)

        return self.get_response(request)

    @classmethod
    def get_files_from_storage(cls, paths, signature):
        """Return S3 file where the name does not include the path."""
        location = get_aws_location()
        for vulnerable_path in paths:
            cleaned_path = pathlib.PurePosixPath(clean_name(vulnerable_path))
            if (
                not (
                    filename := MultiPartParser.sanitize_file_name(
                        None, vulnerable_path
                    )
                )
                or filename == "."
            ):
                raise SuspiciousFileOperation("No filename, or dictionary provided.")
            if ".." in cleaned_path.parts or not str(cleaned_path).startswith(location):
                raise SuspiciousFileOperation(
                    "Path traversal attempt, or file not in the upload folder."
                )
            if (
                not (upload_to := str(cleaned_path.parent)[len(location) + 1 :])
                or upload_to == location
            ):
                raise SuspiciousFileOperation(
                    "No upload folder, or file in the root of the upload folder."
                )

            if not constant_time_compare(
                cls.sign_s3_key_prefix(str(cleaned_path.parent)), signature
            ):
                raise SuspiciousFileOperation("Illegal signature!")
            try:
                f = storage.open(cleaned_path.relative_to(location))
                f.name = cleaned_path.name
                yield f
            except (OSError, ValueError):
                logger.exception("File not found: %r", vulnerable_path)

    @classmethod
    def sign_s3_key_prefix(cls, path):
        """
        Signature to validate the S3 keys passed the middleware before fetching files.

        Return a base64-encoded HMAC-SHA256 of the upload folder aka the S3 key-prefix.
        """
        return signing.Signer(salt="s3file.middleware.S3FileMiddleware").signature(path)
