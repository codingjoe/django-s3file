import base64
import datetime
import hmac
import json
import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage, default_storage
from django.utils._os import safe_join


class S3MockStorage(FileSystemStorage):
    @property
    def location(self):
        return getattr(settings, 'AWS_LOCATION', '')

    def path(self, name):
        return safe_join(os.path.abspath(self.base_location), self.location, name)

    class connection:
        class meta:
            class client:
                @staticmethod
                def generate_presigned_post(bucket_name, key, **policy):
                    policy = json.dumps(policy).encode()
                    policy_b64 = base64.b64encode(policy).decode()
                    date = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
                    aws_id = getattr(
                        settings, 'AWS_ACCESS_KEY_ID',
                        'AWS_ACCESS_KEY_ID',
                    )
                    fields = {
                        'x-amz-algorithm': 'AWS4-HMAC-SHA256',
                        'x-amz-date': date,
                        'x-amz-credential': aws_id,
                        'policy': policy_b64,
                        'key': key,
                    }
                    signature = hmac.new(
                        settings.SECRET_KEY.encode(),
                        policy + date.encode(),
                        'sha256',
                    ).digest()
                    signature = base64.b64encode(signature).decode()
                    return {
                        'url': '/__s3_mock__/',
                        'fields': {
                            'x-amz-signature': signature,
                            **fields
                        },
                    }

    class bucket:
        name = 'test-bucket'


local_dev = isinstance(default_storage, FileSystemStorage)

storage = default_storage if not local_dev else S3MockStorage()
