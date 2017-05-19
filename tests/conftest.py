# -*- coding:utf-8 -*-
from __future__ import absolute_import, unicode_literals

import os
import tempfile
from time import sleep

import pytest
from django.core.files.base import ContentFile
from django.utils.encoding import force_text
from selenium import webdriver
from selenium.common.exceptions import WebDriverException


browsers = {
    'chrome': webdriver.Chrome,
    'firefox': webdriver.Firefox,
}


@pytest.yield_fixture(scope='session', params=sorted(browsers.keys()))
def driver(request):
    if 'DISPLAY' not in os.environ:
        pytest.skip('Test requires display server (export DISPLAY)')

    try:
        b = browsers[request.param]()
    except WebDriverException as e:
        pytest.skip(force_text(e))
    else:
        b.set_window_size(1200, 800)
        b.implicitly_wait(0.1)
        yield b
        if isinstance(b, webdriver.Chrome):
            # chrome needs a couple of seconds before it can be quit
            sleep(5)
        b.quit()


@pytest.fixture
def upload_file():
    path = tempfile.mkdtemp()
    file_name = os.path.join(path, 'test.txt')
    with open(file_name, 'w') as f:
        f.write('Hello World!')
    return file_name


@pytest.fixture
def filemodel(db):
    from tests.testapp.models import FileModel

    return FileModel.objects.create(file=ContentFile('foobar', 'test.txt'))
