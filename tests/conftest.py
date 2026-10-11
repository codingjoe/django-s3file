import tempfile
from pathlib import Path

import pytest
from django.core.files.base import ContentFile
from django.utils.encoding import force_str
from django.utils.text import slugify
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from s3file.storages import get_aws_location
from s3file.views import S3MockView


def pytest_configure(config):
    config.addinivalue_line("markers", "selenium: skip if selenium is not installed")


# Safari has no headless mode, hence it gets no headless flag.
HEADLESS_ARGS = {"Chrome": "--headless=new", "Firefox": "-headless"}


@pytest.fixture(scope="session", params=["Chrome", "Safari", "Firefox"])
def driver(request):
    options = getattr(webdriver, f"{request.param}Options")()
    if arg := HEADLESS_ARGS.get(request.param):
        options.add_argument(arg)
    try:
        b = getattr(webdriver, request.param)(options=options)
    except WebDriverException as e:
        pytest.skip(force_str(e))
    else:
        yield b
        b.quit()


@pytest.fixture(autouse=True)
def log_rejected_mock_uploads(monkeypatch):
    """Report what a browser sent when the mock S3 endpoint sees no file.

    A browser that drops the file from the presigned POST otherwise only shows
    up as a page load timeout.
    """
    original = S3MockView.post

    def post(self, request):
        if "file" not in request.FILES:
            print(
                "mock upload without a file:"
                f" content_type={request.content_type!r}"
                f" content_length={request.headers.get('content-length')!r}"
                f" post_keys={list(request.POST)!r}"
                f" post_file_length={len(request.POST.get('file', ''))!r}"
                f" files={list(request.FILES)!r}"
            )
        return original(self, request)

    monkeypatch.setattr(S3MockView, "post", post)


@pytest.fixture
def freeze_upload_folder(monkeypatch):
    """Freeze the upload folder which by default contains a random UUID v4."""
    upload_folder = Path(get_aws_location()) / "tmp" / "s3file"
    monkeypatch.setattr(
        "s3file.forms.S3FileInputMixin.upload_folder",
        str(upload_folder),
    )
    return upload_folder


@pytest.fixture
def upload_file(request, freeze_upload_folder):
    path = (
        Path(tempfile.mkdtemp())
        / freeze_upload_folder
        / f"{slugify(request.node.name)}.txt"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write(request.node.name)
    return str(path.absolute())


@pytest.fixture
def another_upload_file(request, freeze_upload_folder):
    path = (
        Path(tempfile.mkdtemp())
        / freeze_upload_folder
        / f"another_{slugify(request.node.name)}.txt"
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
        / f"yet_another_{slugify(request.node.name)}.txt"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write(request.node.name)
    return str(path.absolute())


@pytest.fixture
def filemodel(request, db):
    from tests.testapp.models import FileModel

    return FileModel.objects.create(
        file=ContentFile(request.node.name, f"{request.node.name}.txt")
    )
