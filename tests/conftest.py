import tempfile
from pathlib import Path

import pytest
from django.core.files.base import ContentFile
from django.utils.encoding import force_str
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from s3file.storages import storage


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
def freeze_upload_folder(monkeypatch):
    """Freeze datetime and UUID."""
    upload_folder = Path(storage.aws_location) / "tmp" / "s3file"
    monkeypatch.setattr(
        "s3file.forms.S3FileInputMixin.upload_folder",
        str(upload_folder),
    )
    return upload_folder


@pytest.fixture
def upload_file(request, freeze_upload_folder):
    path = Path(tempfile.mkdtemp()) / freeze_upload_folder / f"{request.node.name}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write(request.node.name)
    return str(path.absolute())


@pytest.fixture
def another_upload_file(request, freeze_upload_folder):
    path = (
        Path(tempfile.mkdtemp())
        / freeze_upload_folder
        / f"another_{request.node.name}.txt"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write(request.node.name)
    return str(path.absolute())


@pytest.fixture
def yet_another_upload_file(request, freeze_upload_folder):
    path = (
        Path(tempfile.mkdtemp())
        / freeze_upload_folder
        / f"yet_another_{request.node.name}.txt"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write(request.node.name)
    return str(path.absolute())


@pytest.fixture
def filemodel(request, db):
    from tests.testapp.models import FileModel

    return FileModel.objects.create(
        file=ContentFile(request.node.name, "%s.txt" % request.node.name)
    )
