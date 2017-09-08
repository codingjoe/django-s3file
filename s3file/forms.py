import logging
import os
import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from django.forms.widgets import ClearableFileInput
from django.utils.functional import cached_property

logger = logging.getLogger('s3file')


class S3FileInput(ClearableFileInput):
    """FileInput that uses JavaScript to directly upload to Amazon S3."""

    needs_multipart_form = False
    mime_type = None

    def __init__(self, attrs=None):
        self.expires = settings.SESSION_COOKIE_AGE
        self.upload_path = getattr(settings, 'S3FILE_UPLOAD_PATH', os.path.join('tmp', 's3file'))
        super(S3FileInput, self).__init__(attrs=attrs)
        try:
            self.mime_type = self.attrs['accept']
        except KeyError:
            pass

    @property
    def bucket_name(self):
        return default_storage.bucket.name

    @property
    def client(self):
        return default_storage.connection.meta.client

    def build_attrs(self, *args, **kwargs):
        attrs = super(S3FileInput, self).build_attrs(*args, **kwargs)
        response = self.client.generate_presigned_post(
            self.bucket_name, os.path.join(self.upload_folder, '${filename}'),
            Conditions=self.get_conditions(),
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

    def get_conditions(self):
        conditions = [
            {"bucket": self.bucket_name},
            ["starts-with", "$key", self.upload_folder],
            {"success_action_status": "201"},
        ]
        if self.mime_type:
            top_type, sub_type = self.mime_type.split('/', 1)
            if sub_type == '*':
                conditions.append(["starts-with", "$Content-Type", "%s/" % top_type])
            else:
                conditions.append({"Content-Type": self.mime_type})
        else:
            conditions.append(["starts-with", "$Content-Type", ""])

        return conditions

    @cached_property
    def upload_folder(self):
        return os.path.join(
            self.upload_path,
            uuid.uuid4().hex,
        )

    class Media:
        js = (
            's3file/js/s3file.js',

        )
