import base64
import datetime
import hmac
import json
from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage, default_storage
from django.utils._os import safe_join
from storages.utils import clean_name


class S3MockStorage(FileSystemStorage):
    @property
    def location(self):
        # absolute() keeps the symlink semantics of os.path.abspath().
        return safe_join(Path(self.base_location).absolute(), get_aws_location())

    def open(self, name, mode="rb"):
        name = clean_name(name)
        return super().open(name, mode=mode)

    # S3MockStorage mimics the boto3 resource attributes that S3FileInputMixin
    # accesses as connection.meta.client and bucket.
    class Connection:
        class Meta:
            class Client:
                @staticmethod
                def generate_presigned_post(bucket_name, key, **policy):
                    policy = json.dumps(policy).encode()
                    policy_b64 = base64.b64encode(policy).decode()
                    date = datetime.datetime.now(tz=datetime.UTC).strftime(
                        "%Y%m%dT%H%M%SZ"
                    )
                    aws_id = getattr(
                        settings,
                        "AWS_ACCESS_KEY_ID",
                        "AWS_ACCESS_KEY_ID",
                    )
                    fields = {
                        "x-amz-algorithm": "AWS4-HMAC-SHA256",
                        "x-amz-date": date,
                        "x-amz-credential": aws_id,
                        "policy": policy_b64,
                        "key": key,
                    }
                    signature = hmac.new(
                        settings.SECRET_KEY.encode(),
                        policy + date.encode(),
                        "sha256",
                    ).digest()
                    signature = base64.b64encode(signature).decode()
                    return {
                        "url": "/__s3_mock__/",
                        "fields": {"x-amz-signature": signature, **fields},
                    }

            client = Client

        meta = Meta

    connection = Connection

    class Bucket:
        name = "test-bucket"

    bucket = Bucket


local_dev = isinstance(default_storage, FileSystemStorage)

storage = default_storage if not local_dev else S3MockStorage()


def get_aws_location():
    return getattr(settings, "AWS_LOCATION", "")
