"""A lightweight file uploader input for Django and Amazon S3."""

import django

from . import _version

__version__ = _version.version
VERSION = _version.version_tuple

if django.VERSION < (4, 0):
    default_app_config = "s3file.apps.S3FileConfig"
