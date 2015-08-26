# -*- coding:utf-8 -*-
from __future__ import absolute_import, unicode_literals

import time

from django.http import response
from django.views import generic


class S3MockView(generic.View):

    def post(self, request):
        time.sleep(1)
        return response.HttpResponse(
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<PostResponse>'
            '<Location>https://localhost/test.png</Location>'
            '<Bucket>AWS_STORAGE_BUCKET_NAME</Bucket>'
            '<Key>_upload/test.png</Key>'
            '<ETag>"1e2580c388265551922a1f73ae5954a3"</ETag>'
            '</PostResponse>',
            status=201)
