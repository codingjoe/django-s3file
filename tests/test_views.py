# -*- coding:utf-8 -*-
from __future__ import print_function, unicode_literals

import json

import pytest
from django.core.urlresolvers import reverse
from selenium.common.exceptions import NoSuchElementException

from s3file.forms import S3FileInput


class TestSigningView(object):
    @pytest.mark.urls('s3file.urls')
    @pytest.fixture
    def url(self):
        return reverse('s3file-sign')

    def test_error(self, url, client):
        response = client.post(
            url,
            {},
        )

        assert response.status_code == 400

    @pytest.fixture
    def freeze(self, monkeypatch):
        """Freeze datetime and UUID."""
        monkeypatch.setattr('s3file.views.S3FileViewMixin.get_expiration_date',
                            lambda _: '1988-11-19T10:10:00.000Z')
        monkeypatch.setattr('s3file.views.S3FileViewMixin.upload_folder',
                            'tmp')

    def test_upload_signing(self, url, client):
        response = client.post(
            url,
            {
                'name': 'image.jpeg',
                'type': 'image/jpeg',
            }
        )
        assert response.status_code == 200, response.conent

        data = json.loads(response.content.decode())
        assert 'policy' in data
        assert 'key' in data
        assert 'AWSAccessKeyId' in data
        assert 'signature' in data
        assert len(data['signature']) == 28


class TestUploadView(object):
    @property
    def url(self):
        return reverse('upload')

    def test_get(self, client):
        response = client.get(self.url)

        assert response.status_code == 200
        assert 'form' in response.context, response.content
        assert isinstance(response.context['form'].fields['file'].widget, S3FileInput)

    def test_no_js_error(self, driver, live_server):
        driver.get(live_server + self.url)
        with pytest.raises(NoSuchElementException):
            error = driver.find_element_by_xpath('//body[@JSError]')
            pytest.fail(error.get_attribute('JSError'))

    def test_file_insert(self, monkeypatch, driver, live_server, upload_file):
        monkeypatch.setattr('s3file.views.S3FileView.get_form_action',
                            lambda _: live_server + reverse('s3mock'))
        driver.get(live_server + self.url)
        file_input = driver.find_element_by_xpath('//input[@type=\'file\']')
        file_input.send_keys(upload_file)
        with pytest.raises(NoSuchElementException):
            error = driver.find_element_by_xpath('//body[@JSError]')
            pytest.fail(error.get_attribute('JSError'))
