import pytest
from django.core.files.base import ContentFile

from s3file.storages_optimized import S3OptimizedUploadStorage


class S3OptimizedMockStorage(S3OptimizedUploadStorage):
    created_objects = {}

    def _compress_content(self, content):
        return content

    class bucket:
        name = "test-bucket"

        class Object:
            def __init__(self, key):
                self.key = key
                self.copy_from_bucket = None
                self.copy_from_key = None
                S3OptimizedMockStorage.created_objects[self.key] = self

            def copy(self, s3_object, ExtraArgs):
                self.copy_from_bucket = s3_object["Bucket"]
                self.copy_from_key = s3_object["Key"]


class TestStorages:
    url = "/__s3_mock__/"

    def test_post__save_optimized(self):
        storage = S3OptimizedMockStorage()
        obj = storage.bucket.Object("tmp/s3file/s3_file.txt")

        class Content:
            def __init__(self, obj):
                self.obj = obj

        content = Content(obj)
        key = storage._save("tmp/s3file/s3_file_copied.txt", content)
        stored_object = storage.created_objects[
            "custom/location/tmp/s3file/s3_file_copied.txt"
        ]

        assert key == "tmp/s3file/s3_file_copied.txt"
        assert stored_object.copy_from_bucket == storage.bucket.name
        assert stored_object.copy_from_key == "tmp/s3file/s3_file.txt"

    def test_post__save_optimized_gzip(self):
        storage = S3OptimizedMockStorage()
        obj = storage.bucket.Object("tmp/s3file/s3_file.css")
        storage.gzip = True

        class Content:
            def __init__(self, obj):
                self.obj = obj

        content = Content(obj)
        key = storage._save("tmp/s3file/s3_file_copied.css", content)
        stored_object = storage.created_objects[
            "custom/location/tmp/s3file/s3_file_copied.css"
        ]

        assert key == "tmp/s3file/s3_file_copied.css"
        assert stored_object.copy_from_bucket == storage.bucket.name
        assert stored_object.copy_from_key == "tmp/s3file/s3_file.css"

    def test_post__save_optimized_fail(self):
        storage = S3OptimizedMockStorage()

        with pytest.raises(TypeError) as excinfo:
            storage._save("tmp/s3file/s3_file_copied.txt", ContentFile(b"s3file"))

        assert "The content object must be a S3 object and contain a valid key." in str(
            excinfo.value
        )
