from __future__ import (absolute_import, unicode_literals)

from django.conf.urls import patterns, url

from .views import S3FineView


urlpatterns = patterns(
    '',
    url('^s3fine/sign',
        S3FineView.as_view(), name='s3fine-sign'),
)
