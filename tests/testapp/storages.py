from django.core.files.storage import FileSystemStorage

try:
    from django.urls import reverse
except ImportError:
    # Django 1.8 support
    from django.core.urlresolvers import reverse


class DummyS3Boto3Storage(FileSystemStorage):
    class connection:
        class meta:
            class client:
                @staticmethod
                def generate_presigned_post(*args, **kargs):
                    return {
                        'url': reverse('s3mock'),
                        'fields': {
                            'x-amz-algorithm': 'AWS4-HMAC-SHA256',
                            'x-amz-date': '20170908T111600Z',
                            'x-amz-signature': 'asdf',
                            'x-amz-credential': 'testaccessid',
                            'policy': 'asdf',
                            'key': 'tmp/${filename}',
                        },
                    }

    class bucket:
        name = 'test-bucket'
