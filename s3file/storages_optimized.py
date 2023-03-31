from storages.backends.s3boto3 import S3Boto3Storage
from storages.utils import clean_name


class S3OptimizedUploadStorage(S3Boto3Storage):
    """
    Class for an optimized S3 storage.

    This storage prevents unnecessary operation to copy with the general ``upload_fileobj``
    command when the object already is a S3 object where the faster copy command can be used.

    The assumption is that ``content`` contains a S3 object from which we can copy.

    See also discussion here: https://github.com/codingjoe/django-s3file/discussions/126
    """

    def _save(self, name, content):
        # Basically copy the implementation of _save of S3Boto3Storage
        # and replace the obj.upload_fileobj with a copy function
        cleaned_name = clean_name(name)
        name = self._normalize_name(cleaned_name)
        params = self._get_write_parameters(name, content)

        if (
            self.gzip
            and params["ContentType"] in self.gzip_content_types
            and "ContentEncoding" not in params
        ):
            content = self._compress_content(content)
            params["ContentEncoding"] = "gzip"

        obj = self.bucket.Object(name)
        # content.seek(0, os.SEEK_SET)  # Disable unnecessary seek operation
        # obj.upload_fileobj(content, ExtraArgs=params)  # Disable upload function

        if not hasattr(content, "obj") or not hasattr(content.obj, "key"):
            raise TypeError(
                "The content object must be a S3 object and contain a valid key."
            )

        # Copy the file instead uf uploading
        obj.copy({"Bucket": self.bucket.name, "Key": content.obj.key}, ExtraArgs=params)

        return cleaned_name
