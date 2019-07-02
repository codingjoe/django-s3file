import os
import sys
import tempfile

import pytest
from django.core.files.base import ContentFile
from django.utils.encoding import force_text
from selenium import webdriver
from selenium.common.exceptions import WebDriverException


@pytest.yield_fixture(scope='session')
def driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.headless = True
    if sys.platform.startswith('linux') and os.path.exists('/usr/bin/chromium'):
        chrome_options.binary_location = '/usr/bin/chromium'
    try:
        b = webdriver.Chrome(options=chrome_options)
    except WebDriverException as e:
        pytest.skip(force_text(e))
    else:
        yield b
        b.quit()


@pytest.fixture
def upload_directory(request):
    path = tempfile.mkdtemp()
    file_name1 = os.path.join(path, '%s_1.txt' % request.node.name)
    file_name2 = os.path.join(path, '%s_2.txt' % request.node.name)
    file_names = [file_name1, file_name2]
    for name in file_names:
        with open(name, 'w') as f:
            f.write(request.node.name)
    return path


@pytest.fixture
def upload_file(request):
    path = tempfile.mkdtemp()
    file_name = os.path.join(path, '%s.txt' % request.node.name)
    with open(file_name, 'w') as f:
        f.write(request.node.name)
    return file_name


@pytest.fixture
def another_upload_file(request):
    path = tempfile.mkdtemp()
    file_name = os.path.join(path, 'another_%s.txt' % request.node.name)
    with open(file_name, 'w') as f:
        f.write(request.node.name)
    return file_name


@pytest.fixture
def yet_another_upload_file(request):
    path = tempfile.mkdtemp()
    file_name = os.path.join(path, 'yet_another_%s.txt' % request.node.name)
    with open(file_name, 'w') as f:
        f.write(request.node.name)
    return file_name


@pytest.fixture
def filemodel(request, db):
    from tests.testapp.models import FileModel

    return FileModel.objects.create(
        file=ContentFile(request.node.name, '%s.txt' % request.node.name)
    )
