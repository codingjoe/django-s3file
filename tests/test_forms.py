import json
from contextlib import contextmanager

import pytest
from django.core.files.storage import default_storage
from django.forms import ClearableFileInput
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.expected_conditions import staleness_of
from selenium.webdriver.support.wait import WebDriverWait

from s3file.forms import S3FileInputMixin
from tests.testapp.forms import UploadForm

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


class TestS3FileInput:
    @property
    def url(self):
        return reverse('upload')

    @pytest.fixture(autouse=True)
    def patch(self):
        if S3FileInputMixin not in ClearableFileInput.__bases__:
            ClearableFileInput.__bases__ = \
                (S3FileInputMixin,) + ClearableFileInput.__bases__
        pass

    @pytest.fixture
    def freeze(self, monkeypatch):
        """Freeze datetime and UUID."""
        monkeypatch.setattr('s3file.forms.S3FileInputMixin.upload_folder', 'tmp')

    def test_value_from_datadict(self, client, upload_file):
        with open(upload_file) as f:
            uploaded_file = default_storage.save('test.jpg', f)
        response = client.post(reverse('upload'), {
            'file': uploaded_file,
            's3file': 'file'
        })

        assert response.status_code == 201

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
        form = UploadForm(data={'file-clear': '1'}, instance=filemodel)
        assert form.is_valid()
        assert not form.cleaned_data['file']

    def test_build_attr(self):
        assert set(ClearableFileInput().build_attrs({}).keys()) == {
            'class',
            'data-url',
            'data-fields-x-amz-algorithm',
            'data-fields-x-amz-date',
            'data-fields-x-amz-signature',
            'data-fields-x-amz-credential',
            'data-fields-policy',
            'data-fields-key',
        }
        assert ClearableFileInput().build_attrs({})['class'] == 's3file'
        assert ClearableFileInput().build_attrs(
            {'class': 'my-class'})['class'] == 'my-class s3file'

    def test_get_conditions(self, freeze):
        conditions = ClearableFileInput().get_conditions(None)
        assert all(condition in conditions for condition in [
            {"bucket": 'test-bucket'},
            {"success_action_status": "201"},
            ['starts-with', '$key', 'tmp'],
            ["starts-with", "$Content-Type", ""]
        ]), conditions

    def test_accept(self):
        widget = ClearableFileInput()
        assert 'accept' not in widget.render(name='file', value='test.jpg')
        assert ["starts-with", "$Content-Type", ""] in widget.get_conditions(None)

        widget = ClearableFileInput(attrs={'accept': 'image/*'})
        assert 'accept="image/*"' in widget.render(name='file', value='test.jpg')
        assert ["starts-with", "$Content-Type", "image/"] in widget.get_conditions('image/*')

        widget = ClearableFileInput(attrs={'accept': 'image/jpeg'})
        assert 'accept="image/jpeg"' in widget.render(name='file', value='test.jpg')
        assert {"Content-Type": 'image/jpeg'} in widget.get_conditions('image/jpeg')

        widget = ClearableFileInput(attrs={'accept': 'application/pdf,image/*'})
        assert 'accept="application/pdf,image/*"' in widget.render(name='file', value='test.jpg')
        assert ["starts-with", "$Content-Type", "image/"] in widget.get_conditions(
            'application/pdf,image/*')
        assert {"Content-Type": 'application/pdf'} in widget.get_conditions(
            'application/pdf,image/*')

        widget = ClearableFileInput(attrs={'accept': 'application/pdf, image/*'})
        assert 'accept="application/pdf, image/*"' in widget.render(name='file', value='test.jpg')
        assert ["starts-with", "$Content-Type", "image/"] in widget.get_conditions(
            'application/pdf, image/*')
        assert {"Content-Type": 'application/pdf'} in widget.get_conditions(
            'application/pdf, image/*')

    def test_no_js_error(self, driver, live_server):
        driver.get(live_server + self.url)

        with pytest.raises(NoSuchElementException):
            error = driver.find_element_by_xpath('//body[@JSError]')
            pytest.fail(error.get_attribute('JSError'))

    def test_file_insert(self, request, driver, live_server, upload_file, freeze):
        driver.get(live_server + self.url)
        file_input = driver.find_element_by_xpath('//input[@type=\'file\']')
        file_input.send_keys(upload_file)
        assert file_input.get_attribute('name') == 'file'
        with wait_for_page_load(driver, timeout=10):
            file_input.submit()
        assert default_storage.exists('tmp/%s.txt' % request.node.name)

        with pytest.raises(NoSuchElementException):
            error = driver.find_element_by_xpath('//body[@JSError]')
            pytest.fail(error.get_attribute('JSError'))

    def test_file_insert_submit_value(self, driver, live_server, upload_file, freeze):
        driver.get(live_server + self.url)
        file_input = driver.find_element_by_xpath('//input[@type=\'file\']')
        file_input.send_keys(upload_file)
        assert file_input.get_attribute('name') == 'file'
        save_button = driver.find_element_by_xpath('//input[@name=\'save\']')
        with wait_for_page_load(driver, timeout=10):
            save_button.click()
        assert 'save' in driver.page_source

        driver.get(live_server + self.url)
        file_input = driver.find_element_by_xpath('//input[@type=\'file\']')
        file_input.send_keys(upload_file)
        assert file_input.get_attribute('name') == 'file'
        save_button = driver.find_element_by_xpath('//button[@name=\'save_continue\']')
        with wait_for_page_load(driver, timeout=10):
            save_button.click()
        assert 'save_continue' in driver.page_source
        assert 'continue_value' in driver.page_source

    def test_media(self):
        assert ClearableFileInput().media._js == ['s3file/js/s3file.js']
