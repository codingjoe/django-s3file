import hashlib
import hmac
import json
import logging
import os
import uuid
from base64 import b64encode

from django.conf import settings
from django.forms.widgets import ClearableFileInput
from django.utils.encoding import force_text
from django.utils.functional import cached_property
from django.utils.six import binary_type
from django.utils.timezone import datetime, timedelta

logger = logging.getLogger('s3file')


class S3FileInput(ClearableFileInput):
    """FileInput that uses JavaScript to directly upload to Amazon S3."""

    needs_multipart_form = False
    mime_type = None

    def __init__(self, attrs=None):
        self.expires = timedelta(seconds=settings.SESSION_COOKIE_AGE)
        self.access_key = settings.AWS_ACCESS_KEY_ID
        self.secret_access_key = settings.AWS_SECRET_ACCESS_KEY
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        self.upload_path = getattr(settings, 'S3FILE_UPLOAD_PATH', os.path.join('tmp', 's3fine'))
        super(S3FileInput, self).__init__(attrs=attrs)
        try:
            self.mime_type = self.attrs['accept']
        except KeyError:
            pass

    def get_expiration_date(self):
        expiration_date = datetime.utcnow() + self.expires
        return expiration_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')

    def build_attrs(self, *args, **kwargs):
        attrs = super(S3FileInput, self).build_attrs(*args, **kwargs)
        defaults = {
            'data-policy': force_text(self.get_policy()),
            'data-signature': self.get_signature(),
            'data-key': self.upload_folder,
            'data-s3-url': 'https://s3.amazonaws.com/%s' % self.bucket_name,
            'data-AWSAccessKeyId': self.access_key,
        }
        defaults.update(attrs)
        try:
            defaults['class'] += ' s3file'
        except KeyError:
            defaults['class'] = 's3file'
        return defaults

    def get_secret_access_key(self):
        return binary_type(self.secret_access_key.encode('utf-8'))

    def get_policy(self):
        policy = {
            "expiration": self.get_expiration_date(),
            "conditions": self.get_conditions(),
        }
        policy_json = json.dumps(policy)
        policy_json = policy_json.replace('\n', '').replace('\r', '')
        return b64encode(binary_type(policy_json.encode('utf-8')))

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

    def get_signature(self):
        """
        Return S3 upload signature.

        :rtype: dict
        """
        policy_object = self.get_policy()
        signature = hmac.new(
            self.get_secret_access_key(),
            policy_object,
            hashlib.sha1
        ).digest()

        return force_text(b64encode(signature))

    class Media:
        js = (
            's3file/js/s3file.js',

        )
