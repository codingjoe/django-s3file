from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from .views import S3FileView

urlpatterns = [
    url('^s3file/sign',
        S3FileView.as_view(), name='s3file-sign'),
]
