# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse


class TestS3FileInput(object):

    def test_value_from_datadict(self, client, upload_file):
        with open(upload_file) as f:
            uploaded_file = default_storage.save('test.jpg', f)
        response = client.post(reverse('upload'), {
            'file': default_storage.url(uploaded_file)
        })

        assert response.status_code == 302
