import pytest
from django.core.files.base import ContentFile

from s3file import storages


class TestStorages:
    url = "/__s3_mock__/"

    def test_post__save_optimized(self):
        storage = storages.S3OptimizedMockStorage()
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

    def test_post__save_optimized_fail(self):
        storage = storages.S3OptimizedMockStorage()

        with pytest.raises(RuntimeError) as excinfo:
            storage._save("tmp/s3file/s3_file_copied.txt", ContentFile(b"s3file"))

        assert "The content object must be a S3 object and contain a valid key." in str(
            excinfo.value
        )
