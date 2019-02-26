import base64
import logging
import pathlib
import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from django.utils.functional import cached_property

logger = logging.getLogger('s3file')


class S3FileInputMixin:
    """FileInput that uses JavaScript to directly upload to Amazon S3."""

    needs_multipart_form = False
    upload_path = getattr(settings, 'S3FILE_UPLOAD_PATH', pathlib.PurePosixPath('tmp', 's3file'))
    expires = settings.SESSION_COOKIE_AGE

    @property
    def bucket_name(self):
        return default_storage.bucket.name

    @property
    def client(self):
        return default_storage.connection.meta.client

    def build_attrs(self, *args, **kwargs):
        attrs = super().build_attrs(*args, **kwargs)

        accept = attrs.get('accept')
        response = self.client.generate_presigned_post(
            self.bucket_name, str(pathlib.PurePosixPath(self.upload_folder, '${filename}')),
            Conditions=self.get_conditions(accept),
            ExpiresIn=self.expires,
        )

        defaults = {
            'data-fields-%s' % key: value
            for key, value in response['fields'].items()
        }
        defaults['data-url'] = response['url']
        defaults.update(attrs)

        try:
            defaults['class'] += ' s3file'
        except KeyError:
            defaults['class'] = 's3file'
        return defaults

    def get_conditions(self, accept):
        conditions = [
            {"bucket": self.bucket_name},
            ["starts-with", "$key", str(self.upload_folder)],
            {"success_action_status": "201"},
        ]
        if accept and ',' not in accept:
            top_type, sub_type = accept.split('/', 1)
            if sub_type == '*':
                conditions.append(["starts-with", "$Content-Type", "%s/" % top_type])
            else:
                conditions.append({"Content-Type": accept})
        else:
            conditions.append(["starts-with", "$Content-Type", ""])

        return conditions

    @cached_property
    def upload_folder(self):
        return str(pathlib.PurePosixPath(
            self.upload_path,
            base64.urlsafe_b64encode(
                uuid.uuid4().bytes
            ).decode('utf-8').rstrip('=\n'),
        ))  # S3 uses POSIX paths

    class Media:
        js = (
            's3file/js/s3file.js',
        )
