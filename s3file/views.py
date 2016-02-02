# -*- coding:utf-8 -*-
from __future__ import absolute_import, unicode_literals

import hashlib
import hmac
import json
import logging
import os
import uuid
from base64 import b64encode

from django.core.files.storage import default_storage
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.encoding import force_text
from django.utils.functional import cached_property
from django.utils.six import binary_type
from django.utils.timezone import datetime, timedelta
from django.views.generic import View

from .conf import settings

logger = logging.getLogger('s3file')


class S3FileViewMixin(object):
    """
    Mixin to handle file upload signing for S3 buckets.

    Can be used in all kinds of views.
    Simply set :attr:`mime_type` and :attr:`file_name`
    and call :func:`sign`.
    The sign method returns a dictionary containing an
    S3 upload signature.
    """

    expires = timedelta(hours=1)
    access_key = settings.AWS_ACCESS_KEY_ID
    secret_access_key = settings.AWS_SECRET_ACCESS_KEY
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    upload_path = settings.S3FILE_UPLOAD_PATH

    def get_expiration_date(self):
        expiration_date = datetime.utcnow() + self.expires
        return expiration_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')

    def get_secret_access_key(self):
        return binary_type(self.secret_access_key.encode('utf-8'))

    def get_policy(self):
        policy_object = {
            "expiration": self.get_expiration_date(),
            "conditions": self.get_conditions(),
        }
        policy_json = json.dumps(policy_object)
        policy_json = policy_json.replace('\n', '').replace('\r', '')
        policy = b64encode(binary_type(policy_json.encode('utf-8')))
        return policy

    def get_conditions(self):
        return [
            {"bucket": self.bucket_name},
            {"acl": "public-read"},
            {"Content-Type": self.mime_type},
            ["starts-with", "$key", self.upload_folder],
            {"success_action_status": "201"}
        ]

    @cached_property
    def upload_folder(self):
        return os.path.join(
            self.upload_path,
            uuid.uuid4().hex,
        )

    def get_key(self):
        return os.path.join(
            self.upload_folder,
            self.file_name
        )

    def get_form_action(self):
        return default_storage.url('')

    def sign(self):
        """
        Return S3 upload signature.

        :rtype: dict
        """
        signature = hmac.new(
            self.get_secret_access_key(),
            self.get_policy(),
            hashlib.sha1
        ).digest()

        signature_b64 = b64encode(signature)

        return {
            "policy": force_text(self.get_policy()),
            "signature": force_text(signature_b64),
            "key": self.get_key(),
            "AWSAccessKeyId": self.access_key,
            "form_action": self.get_form_action(),
            "success_action_status": "201",
            "acl": "public-read",
            "Content-Type": self.mime_type
        }


class S3FileView(S3FileViewMixin, View):
    """View to sign upload requests to an S3 bucket."""

    def post(self, request, *args, **kwargs):
        request_dict = request.POST

        if 'name' not in request_dict or 'type' not in request_dict:
            logger.warning('"name" or "type" are missing request: "%s"', request_dict)
            return HttpResponseBadRequest(
                '"name" or "type" are missing in request.'
            )

        self.file_name = request_dict['name']
        self.mime_type = request_dict['type']

        return HttpResponse(
            json.dumps(self.sign()),
            content_type="application/json"
        )
