import os
import pathlib

import pytest
from django.core.exceptions import PermissionDenied, SuspiciousFileOperation
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile

from s3file.middleware import S3FileMiddleware
from s3file.storages import get_aws_location, storage


class TestS3FileMiddleware:
    def test_get_files_from_storage(self, freeze_upload_folder):
        content = b"test_get_files_from_storage"
        name = storage.save(
            "tmp/s3file/test_get_files_from_storage", ContentFile(content)
        )
        files = S3FileMiddleware.get_files_from_storage(
            [os.path.join(get_aws_location(), name)],
            "VRIPlI1LCjUh1EtplrgxQrG8gSAaIwT48mMRlwaCytI",
        )
        file = next(files)
        assert file.read() == content

    def test_get_files_from_storage__relative_path_traversal_windows(
        self, freeze_upload_folder, caplog
    ):
        """
        Relative path traversal into storage-root using a Windows relative path.

        See also: https://github.com/codingjoe/django-s3file/security/advisories/GHSA-67qg-7284-2277
        """
        secret_content = b"secret"
        cooked_key = r"tmp/s3file/..\..\secret"
        storage.save("secret", ContentFile(secret_content))
        files = S3FileMiddleware.get_files_from_storage(
            [os.path.join(get_aws_location(), cooked_key)],
            "VRIPlI1LCjUh1EtplrgxQrG8gSAaIwT48mMRlwaCytI",
        )
        with pytest.raises(
            SuspiciousFileOperation,
            match="Path traversal attempt, or file not in the upload folder.",
        ):
            next(files)

    def test_get_files_from_storage__relative_path_traversal__posix(
        self, freeze_upload_folder, caplog
    ):
        """
        Relative path traversal into storage-root using a POSIX relative path.

        See also: https://github.com/codingjoe/django-s3file/security/advisories/GHSA-67qg-7284-2277
        """
        secret_content = b"secret"
        cooked_key = "tmp/s3file/../../secret"
        storage.save("secret", ContentFile(secret_content))
        files = S3FileMiddleware.get_files_from_storage(
            [os.path.join(get_aws_location(), cooked_key)],
            "VRIPlI1LCjUh1EtplrgxQrG8gSAaIwT48mMRlwaCytI",
        )
        with pytest.raises(
            SuspiciousFileOperation,
            match="No upload folder, or file in the root of the upload folder.",
        ):
            next(files)

    def test_get_files_from_storage__illegal_filename(self):
        """
        Test that relative path traversal is prevented in get_files_from_storage.

        See also: https://github.com/codingjoe/django-s3file/security/advisories/GHSA-67qg-7284-2277
        """
        cooked_key = r"tmp/s3file/something/."
        files = S3FileMiddleware.get_files_from_storage(
            [os.path.join(get_aws_location(), cooked_key)],
            "VRIPlI1LCjUh1EtplrgxQrG8gSAaIwT48mMRlwaCytI",
        )
        with pytest.raises(
            SuspiciousFileOperation, match="No filename, or dictionary provided."
        ):
            next(files)

    def test_get_files_from_storage__illegal_location(self):
        """
        Relative path traversal into the S3 location w/ leaked valid signature.

        See also: https://github.com/codingjoe/django-s3file/security/advisories/GHSA-67qg-7284-2277
        """
        secret_content = b"secret"
        cooked_key = "tmp/s3file/../../secret"
        storage.save("secret", ContentFile(secret_content))
        files = S3FileMiddleware.get_files_from_storage(
            [os.path.join(get_aws_location(), cooked_key)],
            # leaked signature for Storage location
            S3FileMiddleware.sign_s3_key_prefix("custom/location"),
        )
        with pytest.raises(
            SuspiciousFileOperation,
            match="No upload folder, or file in the root of the upload folder.",
        ):
            next(files)

    def test_get_files_from_storage__illegal_location_folder_name(self):
        """
        Relative path traversal into the path that starts with a different name.

        See also: https://github.com/codingjoe/django-s3file/security/advisories/GHSA-67qg-7284-2277
        """
        secret_content = b"secret"
        cooked_key = "tmp/s3file/secret"
        storage.save("secret", ContentFile(secret_content))
        files = S3FileMiddleware.get_files_from_storage(
            [os.path.join("custom/location_evil", cooked_key)],
            # leaked signature for Storage location
            S3FileMiddleware.sign_s3_key_prefix("custom/location/tmp/s3file"),
        )
        with pytest.raises(
            SuspiciousFileOperation,
            match="Path traversal attempt, or file not in the upload folder.",
        ):
            next(files)

    def test_get_files_from_storage__signed_noncanonical_traversal_rejected(
        self, freeze_upload_folder
    ):
        """
        Relative path traversal into the S3 location w/ leaked secret key.

        See also: https://github.com/codingjoe/django-s3file/security/advisories/GHSA-67qg-7284-2277
        """
        storage.save("secret", ContentFile(b"secret"))

        vulnerable_path = "custom/location/tmp/s3file/../../secret"
        filename = "secret"
        unsafe_upload_dir = pathlib.PurePosixPath(vulnerable_path[: -len(filename)])

        files = S3FileMiddleware.get_files_from_storage(
            [vulnerable_path],
            S3FileMiddleware.sign_s3_key_prefix(unsafe_upload_dir),
        )

        with pytest.raises(
            SuspiciousFileOperation,
            match="No upload folder, or file in the root of the upload folder.",
        ):
            next(files)

    def test_get_files_from_storage__signed_noncanonical_traversal_rejected__windows(
        self, freeze_upload_folder
    ):
        """
        Relative path traversal into the S3 location w/ leaked secret key.

        See also: https://github.com/codingjoe/django-s3file/security/advisories/GHSA-67qg-7284-2277
        """
        storage.save("secret", ContentFile(b"secret"))

        vulnerable_path = r"custom/location/tmp/s3file\..\..\secret"
        filename = "secret"
        unsafe_upload_dir = pathlib.PurePosixPath(vulnerable_path[: -len(filename)])

        files = S3FileMiddleware.get_files_from_storage(
            [vulnerable_path],
            S3FileMiddleware.sign_s3_key_prefix(unsafe_upload_dir),
        )

        with pytest.raises(
            SuspiciousFileOperation,
            match="Path traversal attempt, or file not in the upload folder.",
        ):
            next(files)

    def test_get_files_from_storage__illegal_location__root(self):
        """
        Relative path traversal outside the storage location w/ leaked valid signature.

        See also: https://github.com/codingjoe/django-s3file/security/advisories/GHSA-67qg-7284-2277
        """
        secret_content = b"secret"
        cooked_key = "tmp/s3file/../../../secret"
        storage.save("secret", ContentFile(secret_content))
        files = S3FileMiddleware.get_files_from_storage(
            [os.path.join(get_aws_location(), cooked_key)],
            # leaked signature for Storage location
            S3FileMiddleware.sign_s3_key_prefix("custom"),
        )
        with pytest.raises(
            SuspiciousFileOperation,
            match="Path traversal attempt, or file not in the upload folder.",
        ):
            next(files)

    def test_process_request(self, freeze_upload_folder, rf):
        uploaded_file = SimpleUploadedFile("uploaded_file.txt", b"uploaded")
        request = rf.post("/", data={"file": uploaded_file})
        S3FileMiddleware(lambda x: None)(request)
        assert request.FILES.getlist("file")
        assert request.FILES.get("file").read() == b"uploaded"

        storage.save("tmp/s3file/s3_file.txt", ContentFile(b"s3file"))
        request = rf.post(
            "/",
            data={
                "file": "custom/location/tmp/s3file/s3_file.txt",
                "s3file": "file",
                "file-s3f-signature": "VRIPlI1LCjUh1EtplrgxQrG8gSAaIwT48mMRlwaCytI",
            },
        )
        S3FileMiddleware(lambda x: None)(request)
        assert request.FILES.getlist("file")
        assert request.FILES.get("file").read() == b"s3file"

    def test_process_request__location_escape(self, freeze_upload_folder, rf):
        storage.save("secrets/passwords.txt", ContentFile(b"keep this secret"))
        request = rf.post(
            "/",
            data={
                "file": "custom/location/secrets/passwords.txt",
                "s3file": "file",
                "file-s3f-signature": "VRIPlI1LCjUh1EtplrgxQrG8gSAaIwT48mMRlwaCytI",
            },
        )
        with pytest.raises(PermissionDenied, match="Illegal filename!"):
            S3FileMiddleware(lambda x: None)(request)

    def test_process_request__multiple_files(self, freeze_upload_folder, rf):
        storage.save("tmp/s3file/s3_file.txt", ContentFile(b"s3file"))
        storage.save("tmp/s3file/s3_other_file.txt", ContentFile(b"other s3file"))
        request = rf.post(
            "/",
            data={
                "file": [
                    "custom/location/tmp/s3file/s3_file.txt",
                    "custom/location/tmp/s3file/s3_other_file.txt",
                ],
                "file-s3f-signature": "VRIPlI1LCjUh1EtplrgxQrG8gSAaIwT48mMRlwaCytI",
                "other_file-s3f-signature": "VRIPlI1LCjUh1EtplrgxQrG8gSAaIwT48mMRlwaCytI",
                "s3file": ["file", "other_file"],
            },
        )
        S3FileMiddleware(lambda x: None)(request)
        files = request.FILES.getlist("file")
        assert files[0].read() == b"s3file"
        assert files[1].read() == b"other s3file"

    def test_process_request__no_location(self, freeze_upload_folder, rf, settings):
        settings.AWS_LOCATION = ""
        uploaded_file = SimpleUploadedFile("uploaded_file.txt", b"uploaded")
        request = rf.post("/", data={"file": uploaded_file})
        S3FileMiddleware(lambda x: None)(request)
        assert request.FILES.getlist("file")
        assert request.FILES.get("file").read() == b"uploaded"

        storage.save("tmp/s3file/s3_file.txt", ContentFile(b"s3file"))
        request = rf.post(
            "/",
            data={
                "file": "tmp/s3file/s3_file.txt",
                "s3file": "file",
                "file-s3f-signature": "pJYaM4x7RzLDLVXWuphK2dMqqc0oLr_jZFasfGU7BhU",
            },
        )
        S3FileMiddleware(lambda x: None)(request)
        assert request.FILES.getlist("file")
        assert request.FILES.get("file").read() == b"s3file"

    def test_process_request__no_file(self, freeze_upload_folder, rf, caplog):
        request = rf.post(
            "/",
            data={
                "file": "custom/location/tmp/s3file/does_not_exist.txt",
                "s3file": "file",
                "file-s3f-signature": "VRIPlI1LCjUh1EtplrgxQrG8gSAaIwT48mMRlwaCytI",
            },
        )
        S3FileMiddleware(lambda x: None)(request)
        assert not request.FILES.getlist("file")
        assert (
            "File not found: 'custom/location/tmp/s3file/does_not_exist.txt'"
            in caplog.text
        )

    def test_process_request__no_signature(self, rf, caplog):
        request = rf.post(
            "/", data={"file": "tmp/s3file/does_not_exist.txt", "s3file": "file"}
        )
        with pytest.raises(PermissionDenied, match="No signature provided."):
            S3FileMiddleware(lambda x: None)(request)

    def test_process_request__wrong_signature(self, rf, caplog):
        request = rf.post(
            "/",
            data={
                "file": "tmp/s3file/does_not_exist.txt",
                "s3file": "file",
                "file-s3f-signature": "fake",
            },
        )
        with pytest.raises(PermissionDenied, match="Illegal filename!"):
            S3FileMiddleware(lambda x: None)(request)

    def test_sign_s3_key_prefix(self, rf):
        assert (
            S3FileMiddleware.sign_s3_key_prefix("test/test")
            == "a8KINhIf1IpSD5sgdXE4wEQodZorq_8CmwkqZ5V6nr4"
        )
