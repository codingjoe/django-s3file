import json
import os
from contextlib import contextmanager

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import ClearableFileInput
from django.urls import reverse_lazy
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import staleness_of
from selenium.webdriver.support.wait import WebDriverWait

from s3file import forms
from s3file.storages import storage
from tests.testapp.forms import FileForm
from tests.testapp.models import FileModel


class TestAsset:
    def test_init(self):
        asset = forms.Asset("path")
        assert asset.path == "path"

    def test_eq(self):
        asset = forms.Asset("path")
        assert asset == "path"
        assert asset == forms.Asset("path")
        assert asset != forms.Asset("other")

    def test_hash(self):
        asset = forms.Asset("path")
        assert hash(asset) == hash("path")

    def test_str(self, settings):
        settings.STORAGES = {
            "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
            },
        }
        asset = forms.Asset("path")
        assert str(asset) == "/static/path"

    def test_absolute_path(self, settings):
        settings.STORAGES = {
            "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
            },
        }
        asset = forms.Asset("path")
        assert asset.absolute_path("path") == "/static/path"
        assert asset.absolute_path("/path") == "/path"
        assert asset.absolute_path("http://path") == "http://path"
        assert asset.absolute_path("https://path") == "https://path"

    def test_repr(self):
        asset = forms.Asset("path")
        assert repr(asset) == "Asset: 'path'"


class TestESM:
    def test_str(self, settings):
        settings.STORAGES = {
            "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
            },
        }
        js = forms.ESM("path")
        assert str(js) == '<script src="/static/path" type="module"></script>'


@contextmanager
def wait_for_page_load(driver, timeout=30):
    old_page = driver.find_element(By.TAG_NAME, "html")
    yield
    WebDriverWait(driver, timeout).until(staleness_of(old_page))


class TestS3FileInput:
    create_url = reverse_lazy("example-create")

    def test_value_from_datadict(self, freeze_upload_folder, client, upload_file):
        with open(upload_file) as f:
            uploaded_file = storage.save(freeze_upload_folder / "test.jpg", f)
        response = client.post(
            self.create_url,
            {
                "file": f"custom/location/{uploaded_file}",
                "file-s3f-signature": "FxQXie3wnVnCUFqGzFZ8DCFKAXFA3bnQ8tE96U11o80",
                "s3file": "file",
            },
        )

        assert response.status_code == 201

    def test_value_from_datadict_initial_data(self, filemodel):
        form = FileForm(instance=filemodel)
        assert filemodel.file.name in form.as_p(), form.as_p()
        assert not form.is_valid()

    def test_file_does_not_exist_no_fallback(self, filemodel):
        form = FileForm(
            data={"file": "foo.bar", "s3file": "file"},
            instance=filemodel,
        )
        assert form.is_valid()
        assert form.cleaned_data["file"] == filemodel.file

    def test_initial_no_file_uploaded(self, filemodel):
        form = FileForm(data={"file": ""}, instance=filemodel)
        assert form.is_valid(), form.errors
        assert not form.has_changed()
        assert form.cleaned_data["file"] == filemodel.file

    def test_initial_fallback(self, filemodel):
        form = FileForm(data={"file": ""}, instance=filemodel)
        assert form.is_valid()
        assert form.cleaned_data["file"] == filemodel.file

    def test_clear(self, filemodel):
        form = FileForm(data={"file-clear": "1"}, instance=filemodel)
        assert form.is_valid()
        assert not form.cleaned_data["file"]

    def test_build_attr(self, freeze_upload_folder):
        assert set(ClearableFileInput().build_attrs({}).keys()) == {
            "is",
            "data-url",
            "data-fields-x-amz-algorithm",
            "data-fields-x-amz-date",
            "data-fields-x-amz-signature",
            "data-fields-x-amz-credential",
            "data-fields-policy",
            "data-fields-key",
            "data-s3f-signature",
        }
        assert (
            ClearableFileInput().build_attrs({})["data-s3f-signature"]
            == "VRIPlI1LCjUh1EtplrgxQrG8gSAaIwT48mMRlwaCytI"
        )
        assert ClearableFileInput().build_attrs({})["is"] == "s3-file"

    def test_get_conditions(self, freeze_upload_folder):
        conditions = ClearableFileInput().get_conditions(None)
        assert all(
            condition in conditions
            for condition in [
                {"bucket": "test-bucket"},
                {"success_action_status": "201"},
                ["starts-with", "$key", "custom/location/tmp/s3file"],
                ["starts-with", "$Content-Type", ""],
            ]
        ), conditions

    def test_accept(self):
        widget = ClearableFileInput()
        assert "accept" not in widget.render(name="file", value="test.jpg")
        assert ["starts-with", "$Content-Type", ""] in widget.get_conditions(None)

        widget = ClearableFileInput(attrs={"accept": "image/*"})
        assert 'accept="image/*"' in widget.render(name="file", value="test.jpg")
        assert ["starts-with", "$Content-Type", "image/"] in widget.get_conditions(
            "image/*"
        )

        widget = ClearableFileInput(attrs={"accept": "image/jpeg"})
        assert 'accept="image/jpeg"' in widget.render(name="file", value="test.jpg")
        assert {"Content-Type": "image/jpeg"} in widget.get_conditions("image/jpeg")

        widget = ClearableFileInput(attrs={"accept": "application/pdf,image/*"})
        assert 'accept="application/pdf,image/*"' in widget.render(
            name="file",
            value="test.jpg",
        )
        assert ["starts-with", "$Content-Type", ""] in widget.get_conditions(
            "application/pdf,image/*"
        )
        assert {"Content-Type": "application/pdf"} not in widget.get_conditions(
            "application/pdf,image/*"
        )

    @pytest.mark.selenium
    def test_no_js_error(self, driver, live_server):
        driver.get(live_server + self.create_url)

        with pytest.raises(NoSuchElementException):
            error = driver.find_element(By.XPATH, "//body[@JSError]")
            pytest.fail(error.get_attribute("JSError"))

    @pytest.mark.selenium
    def test_file_insert(
        self, request, driver, live_server, upload_file, freeze_upload_folder
    ):
        driver.get(live_server + self.create_url)
        file_input = driver.find_element(By.XPATH, "//input[@name='file']")
        file_input.send_keys(upload_file)
        assert file_input.get_attribute("name") == "file"
        with wait_for_page_load(driver, timeout=10):
            file_input.submit()
        assert storage.exists("tmp/s3file/%s.txt" % request.node.name)

        with pytest.raises(NoSuchElementException):
            error = driver.find_element(By.XPATH, "//body[@JSError]")
            pytest.fail(error.get_attribute("JSError"))

    @pytest.mark.selenium
    def test_file_update(
        self, request, driver, live_server, upload_file, freeze_upload_folder
    ):
        FileModel.objects.create(
            file=SimpleUploadedFile(
                f"{request.node.name}.txt", request.node.name.encode()
            )
        )
        driver.get(live_server + reverse_lazy("example-update", kwargs={"pk": 1}))
        file_input = driver.find_element(By.XPATH, "//input[@name='file']")
        file_input.send_keys(upload_file)
        assert file_input.get_attribute("name") == "file"
        with wait_for_page_load(driver, timeout=10):
            file_input.submit()
        assert storage.exists("tmp/s3file/%s.txt" % request.node.name)

        with pytest.raises(NoSuchElementException):
            error = driver.find_element(By.XPATH, "//body[@JSError]")
            pytest.fail(error.get_attribute("JSError"))

    @pytest.mark.selenium
    def test_file_insert_submit_value(
        self, driver, live_server, upload_file, freeze_upload_folder
    ):
        driver.get(live_server + self.create_url)
        file_input = driver.find_element(By.XPATH, "//input[@name='file']")
        file_input.send_keys(upload_file)
        assert file_input.get_attribute("name") == "file"
        save_button = driver.find_element(By.XPATH, "//button[@name='save_continue']")
        with wait_for_page_load(driver, timeout=10):
            save_button.click()
        assert "save_continue" in driver.page_source
        assert "continue_value" in driver.page_source

    @pytest.mark.selenium
    def test_file_insert_submit_formaction(
        self, driver, live_server, upload_file, freeze_upload_folder
    ):
        driver.get(live_server + self.create_url)
        file_input = driver.find_element(By.XPATH, "//input[@name='file']")
        file_input.send_keys(upload_file)
        assert file_input.get_attribute("name") == "file"
        save_button = driver.find_element(By.XPATH, "//button[@name='custom_save']")
        with wait_for_page_load(driver, timeout=10):
            save_button.click()
        assert "custom_save" in driver.page_source
        assert "custom_target" in driver.page_source
        assert "foo" in driver.page_source
        assert "bar" in driver.page_source

    @pytest.mark.selenium
    def test_file_insert_change_event(
        self,
        driver,
        live_server,
        upload_file,
        another_upload_file,
        freeze_upload_folder,
    ):
        driver.get(live_server + self.create_url)
        file_input = driver.find_element(By.XPATH, "//input[@name='file']")
        file_input.send_keys(upload_file)
        file_input.send_keys(another_upload_file)
        save_button = driver.find_element(By.CSS_SELECTOR, "input[name=save]")
        with wait_for_page_load(driver, timeout=10):
            save_button.click()
        assert "save" in driver.page_source

    @pytest.mark.selenium
    def test_multi_file(
        self,
        driver,
        live_server,
        freeze_upload_folder,
        upload_file,
        another_upload_file,
        yet_another_upload_file,
    ):
        driver.get(live_server + reverse_lazy("upload-multi"))
        file_input = driver.find_element(By.XPATH, "//input[@name='file']")
        file_input.send_keys(
            " \n ".join(
                [
                    str(freeze_upload_folder / upload_file),
                    str(freeze_upload_folder / another_upload_file),
                ]
            )
        )
        file_input = driver.find_element(By.XPATH, "//input[@name='other_file']")
        file_input.send_keys(str(freeze_upload_folder / yet_another_upload_file))
        save_button = driver.find_element(By.XPATH, "//input[@name='save']")
        with wait_for_page_load(driver, timeout=10):
            save_button.click()
        response = json.loads(driver.find_elements(By.CSS_SELECTOR, "pre")[0].text)
        assert response["FILES"] == {
            "file": [
                os.path.basename(upload_file),
                os.path.basename(another_upload_file),
            ],
            "other_file": [os.path.basename(yet_another_upload_file)],
        }

    def test_media(self):
        assert ClearableFileInput().media._js == ["s3file/js/s3file.js"]

    def test_upload_folder(self):
        assert "custom/location/tmp/s3file/" in ClearableFileInput().upload_folder
        assert len(os.path.basename(ClearableFileInput().upload_folder)) == 22
