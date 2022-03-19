import os
import tempfile

import pytest
from django.core.files.base import ContentFile
from django.utils.encoding import force_str
from selenium import webdriver
from selenium.common.exceptions import WebDriverException


@pytest.fixture(scope="session")
def driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.headless = True
    try:
        b = webdriver.Chrome(options=chrome_options)
    except WebDriverException as e:
        pytest.skip(force_str(e))
    else:
        yield b
        b.quit()


@pytest.fixture
def upload_file(request):
    path = tempfile.mkdtemp()
    file_name = os.path.join(path, "%s.txt" % request.node.name)
    with open(file_name, "w") as f:
        f.write(request.node.name)
    return file_name


@pytest.fixture
def another_upload_file(request):
    path = tempfile.mkdtemp()
    file_name = os.path.join(path, "another_%s.txt" % request.node.name)
    with open(file_name, "w") as f:
        f.write(request.node.name)
    return file_name


@pytest.fixture
def yet_another_upload_file(request):
    path = tempfile.mkdtemp()
    file_name = os.path.join(path, "yet_another_%s.txt" % request.node.name)
    with open(file_name, "w") as f:
        f.write(request.node.name)
    return file_name


@pytest.fixture
def filemodel(request, db):
    from tests.testapp.models import FileModel

    return FileModel.objects.create(
        file=ContentFile(request.node.name, "%s.txt" % request.node.name)
    )
