import base64
import datetime
import json
from contextlib import contextmanager

import pytest
from django.core.files.storage import default_storage
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.expected_conditions import staleness_of
from selenium.webdriver.support.wait import WebDriverWait

from s3file.forms import S3FileInput
from tests.testapp.forms import ClearableUploadForm, UploadForm

try:
    from django.urls import reverse
except ImportError:
    # Django 1.8 support
    from django.core.urlresolvers import reverse


@contextmanager
def wait_for_page_load(driver, timeout=30):
    old_page = driver.find_element_by_tag_name('html')
    yield
    WebDriverWait(driver, timeout).until(
        staleness_of(old_page)
    )


class TestS3FileInput(object):
    @property
    def url(self):
        return reverse('upload')

    @pytest.fixture
    def freeze(self, monkeypatch):
        """Freeze datetime and UUID."""
        monkeypatch.setattr('s3file.forms.S3FileInput.get_expiration_date',
                            lambda _: '1988-11-19T10:10:00.000Z')
        monkeypatch.setattr('s3file.forms.S3FileInput.upload_folder', 'tmp')

    def test_get_expiration_date(self, settings):
        DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.000Z'
        assert S3FileInput().get_expiration_date()[-1] == 'Z', 'is UTC date'
        date_1 = datetime.datetime.strptime(S3FileInput().get_expiration_date(), DATE_FORMAT)
        settings.SESSION_COOKIE_AGE = 60 * 60 * 24 * 7 * 1
        date_2 = datetime.datetime.strptime(S3FileInput().get_expiration_date(), DATE_FORMAT)
        assert date_2 < date_1, S3FileInput().get_expiration_date()

    def test_get_expiration_date_freeze(self, freeze):
        assert S3FileInput().get_expiration_date() == '1988-11-19T10:10:00.000Z'

    def test_value_from_datadict(self, client, upload_file):
        with open(upload_file) as f:
            uploaded_file = default_storage.save('test.jpg', f)
        response = client.post(reverse('upload'), {
            'file': uploaded_file,
            's3file': 'file'
        })

        assert response.status_code == 302

    def test_value_from_datadict_initial_data(self, filemodel):
        form = UploadForm(instance=filemodel)
        assert filemodel.file.name in form.as_p(), form.as_p()
        assert not form.is_valid()

    def test_file_does_not_exist_no_fallback(self, filemodel):
        form = UploadForm(data={'file': 'foo.bar', 's3file': 'file'}, instance=filemodel)
        assert form.is_valid()
        assert form.cleaned_data['file'] == filemodel.file

    def test_initial_no_file_uploaded(self, filemodel):
        form = UploadForm(data={'file': ''}, instance=filemodel)
        assert form.is_valid(), form.errors
        assert not form.has_changed()
        assert form.cleaned_data['file'] == filemodel.file

    def test_initial_fallback(self, filemodel):
        form = UploadForm(data={'file': ''}, instance=filemodel)
        assert form.is_valid()
        assert form.cleaned_data['file'] == filemodel.file

    def test_clear(self, filemodel):
        form = ClearableUploadForm(data={'file-clear': '1'}, instance=filemodel)
        assert form.is_valid()
        assert not form.cleaned_data['file']

    def test_build_attr(self):
        assert set(S3FileInput().build_attrs({}).keys()) == {
            'class',
            'data-AWSAccessKeyId',
            'data-s3-url',
            'data-key',
            'data-policy',
            'data-signature',
        }
        assert S3FileInput().build_attrs({})['class'] == 's3file'
        assert S3FileInput().build_attrs({'class': 'my-class'})['class'] == 'my-class s3file'

    def test_get_policy(self, freeze):
        base64_policy = S3FileInput().get_policy()
        policy = json.loads(base64.b64decode(base64_policy).decode('utf-8'))
        assert policy == {
            'expiration': '1988-11-19T10:10:00.000Z',
            'conditions': [
                {'bucket': 'test-bucket'},
                ['starts-with', '$key', 'tmp'],
                {'success_action_status': '201'},
                ['starts-with', '$Content-Type', ''],
            ],
        }

    def test_get_signature(self, freeze):
        assert S3FileInput().get_signature() in [
            'jdvyRM/sS2frI9oSe6vIXGFswqg=',
            'D3W1aKcI1VkzcFHrvSQbGdqnmPo=',
        ]

    def test_get_conditions(self, freeze):
        conditions = S3FileInput().get_conditions()
        assert all(condition in conditions for condition in [
            {"bucket": 'test-bucket'},
            {"success_action_status": "201"},
            ['starts-with', '$key', 'tmp'],
            ["starts-with", "$Content-Type", ""]
        ])

    def test_accept(self):
        widget = S3FileInput()
        assert widget.mime_type is None
        assert 'accept' not in widget.render(name='file', value='test.jpg')
        assert ["starts-with", "$Content-Type", ""] in widget.get_conditions()

        widget = S3FileInput(attrs={'accept': 'image/*'})
        assert widget.mime_type == 'image/*'
        assert 'accept="image/*"' in widget.render(name='file', value='test.jpg')
        assert ["starts-with", "$Content-Type", "image/"] in widget.get_conditions()

        widget = S3FileInput(attrs={'accept': 'image/jpeg'})
        assert widget.mime_type == 'image/jpeg'
        assert 'accept="image/jpeg"' in widget.render(name='file', value='test.jpg')
        assert {"Content-Type": 'image/jpeg'} in widget.get_conditions()

    def test_no_js_error(self, driver, live_server):
        driver.get(live_server + self.url)

        with pytest.raises(NoSuchElementException):
            error = driver.find_element_by_xpath('//body[@JSError]')
            pytest.fail(error.get_attribute('JSError'))

    def test_file_insert(self, request, driver, live_server, upload_file, freeze):
        driver.get(live_server + self.url)
        file_input = driver.find_element_by_xpath('//input[@type=\'file\']')
        driver.execute_script('arguments[0].setAttribute("data-s3-url", arguments[1])',
                              file_input, live_server + reverse('s3mock'))
        file_input.send_keys(upload_file)
        assert file_input.get_attribute('name') == 'file'
        with wait_for_page_load(driver, timeout=10):
            file_input.submit()
        assert default_storage.exists('tmp/%s.txt' % request.node.name)

        with pytest.raises(NoSuchElementException):
            error = driver.find_element_by_xpath('//body[@JSError]')
            pytest.fail(error.get_attribute('JSError'))
