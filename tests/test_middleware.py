import os

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile

from s3file.middleware import S3FileMiddleware
from s3file.storages import storage


class TestS3FileMiddleware:
    def test_get_files_from_storage(self):
        content = b"test_get_files_from_storage"
        name = storage.save(
            "tmp/s3file/test_get_files_from_storage", ContentFile(content)
        )
        files = S3FileMiddleware.get_files_from_storage(
            [os.path.join(storage.aws_location, name)]
        )
        file = next(files)
        assert file.read() == content

    def test_process_request(self, rf):
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
            },
        )
        S3FileMiddleware(lambda x: None)(request)
        assert request.FILES.getlist("file")
        assert request.FILES.get("file").read() == b"s3file"

    def test_process_request__multiple_files(self, rf):
        storage.save("tmp/s3file/s3_file.txt", ContentFile(b"s3file"))
        storage.save("tmp/s3file/s3_other_file.txt", ContentFile(b"other s3file"))
        request = rf.post(
            "/",
            data={
                "file": [
                    "custom/location/tmp/s3file/s3_file.txt",
                    "custom/location/tmp/s3file/s3_other_file.txt",
                ],
                "s3file": ["file", "other_file"],
            },
        )
        S3FileMiddleware(lambda x: None)(request)
        files = request.FILES.getlist("file")
        assert files[0].read() == b"s3file"
        assert files[1].read() == b"other s3file"

    def test_process_request__no_location(self, rf, settings):
        settings.AWS_LOCATION = ""
        uploaded_file = SimpleUploadedFile("uploaded_file.txt", b"uploaded")
        request = rf.post("/", data={"file": uploaded_file})
        S3FileMiddleware(lambda x: None)(request)
        assert request.FILES.getlist("file")
        assert request.FILES.get("file").read() == b"uploaded"

        storage.save("tmp/s3file/s3_file.txt", ContentFile(b"s3file"))
        request = rf.post(
            "/", data={"file": "tmp/s3file/s3_file.txt", "s3file": "file"}
        )
        S3FileMiddleware(lambda x: None)(request)
        assert request.FILES.getlist("file")
        assert request.FILES.get("file").read() == b"s3file"

    def test_process_request__no_file(self, rf, caplog):
        request = rf.post("/", data={"file": "does_not_exist.txt", "s3file": "file"})
        S3FileMiddleware(lambda x: None)(request)
        assert not request.FILES.getlist("file")
        assert "File not found: does_not_exist.txt" in caplog.text
