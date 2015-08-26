# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import os

from appconf import AppConf
from django.conf import settings  # NoQA

__all__ = ('settings',)


class S3FileConf(AppConf):
    UPLOAD_PATH = os.path.join('tmp', 's3fine')

    class Meta:
        prefix = "S3FILE"
