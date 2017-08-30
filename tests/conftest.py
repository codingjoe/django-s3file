import os
import tempfile

import pytest
from django.core.files.base import ContentFile
from django.utils.encoding import force_text
from selenium import webdriver
from selenium.common.exceptions import WebDriverException


@pytest.yield_fixture(scope='session')
def driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('headless')
    chrome_options.add_argument('window-size=1200x800')
    try:
        b = webdriver.Chrome(chrome_options=chrome_options)
    except WebDriverException as e:
        pytest.skip(force_text(e))
    else:
        yield b
        b.quit()


@pytest.fixture
def upload_file(request):
    path = tempfile.mkdtemp()
    file_name = os.path.join(path, '%s.txt' % request.node.name)
    with open(file_name, 'w') as f:
        f.write(request.node.name)
    return file_name


@pytest.fixture
def filemodel(request, db):
    from tests.testapp.models import FileModel

    return FileModel.objects.create(
        file=ContentFile(request.node.name, '%s.txt' % request.node.name)
    )
