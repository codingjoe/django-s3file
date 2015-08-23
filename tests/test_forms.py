# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse
from tests.testapp.forms import UploadForm, ClearableUploadForm


class TestS3FileInput(object):

    def test_value_from_datadict(self, client, upload_file):
        with open(upload_file) as f:
            uploaded_file = default_storage.save('test.jpg', f)
        response = client.post(reverse('upload'), {
            'file': default_storage.url(uploaded_file)
        })

        assert response.status_code == 302

    def test_value_from_datadict_initial_data(self, filemodel):
        form = UploadForm(instance=filemodel)
        assert 'initial' in form.as_p(), form.as_p()
        assert not form.is_valid()

    def test_same_url(self, filemodel):
        form = UploadForm(data={'file': filemodel.file.url}, instance=filemodel)
        assert form.is_valid()
        assert form.has_changed()

    def test_file_does_not_exist_no_fallback(self, filemodel):
        form = UploadForm(data={'file': "foo.bar"}, instance=filemodel)
        assert form.is_valid()
        assert form.cleaned_data['file'] == filemodel.file

    def test_file_does_not_exist_fallback(self, filemodel):
        form = ClearableUploadForm(data={'file': "foo.bar"}, instance=filemodel)
        assert form.is_valid()
        assert not form.cleaned_data['file']

    def test_initial_no_file_uploaded(self, filemodel):

        form = UploadForm(data={'file': 'initial'}, instance=filemodel)
        assert form.is_valid(), form.errors
        assert not form.has_changed()
        assert form.cleaned_data['file'] == filemodel.file

    def test_initial_fallback(self, filemodel):
        form = UploadForm(data={'file': ''}, instance=filemodel)
        assert form.is_valid()
        assert form.cleaned_data['file'] == filemodel.file

    def test_initial_no_fallback(self, filemodel):
        form = ClearableUploadForm(data={'file': ''}, instance=filemodel)
        assert form.is_valid()
        assert not form.cleaned_data['file']
