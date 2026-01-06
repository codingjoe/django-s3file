import base64
import logging
import pathlib
import uuid

from django.conf import settings
from django.utils.functional import cached_property
from storages.utils import safe_join

try:
    from django.forms import Script
except ImportError:
    from django.forms.utils import flatatt
    from django.templatetags.static import static
    from django.utils.html import format_html, html_safe

    # Django < 6.0 backport
    @html_safe
    class MediaAsset:
        element_template = "{path}"

        def __init__(self, path, **attributes):
            self._path = path
            self.attributes = attributes

        def __eq__(self, other):
            return (self.__class__ is other.__class__ and self.path == other.path) or (
                isinstance(other, str) and self._path == other
            )

        def __hash__(self):
            return hash(self._path)

        def __str__(self):
            return format_html(
                self.element_template,
                path=self.path,
                attributes=flatatt(self.attributes),
            )

        def __repr__(self):
            return f"{type(self).__qualname__}({self._path!r})"

        @property
        def path(self):
            if self._path.startswith(("http://", "https://", "/")):
                return self._path
            return static(self._path)

    class Script(MediaAsset):
        element_template = '<script src="{path}"{attributes}></script>'

        def __init__(self, src, **attributes):
            super().__init__(src, **attributes)


from s3file.middleware import S3FileMiddleware
from s3file.storages import get_aws_location, storage

logger = logging.getLogger("s3file")


class S3FileInputMixin:
    """FileInput that uses JavaScript to directly upload to Amazon S3."""

    needs_multipart_form = False
    upload_path = safe_join(
        str(get_aws_location()),
        str(
            getattr(
                settings, "S3FILE_UPLOAD_PATH", pathlib.PurePosixPath("tmp", "s3file")
            )
        ),
    )
    expires = settings.SESSION_COOKIE_AGE

    @property
    def bucket_name(self):
        return storage.bucket.name

    @property
    def client(self):
        return storage.connection.meta.client

    def build_attrs(self, *args, **kwargs):
        attrs = super().build_attrs(*args, **kwargs)

        accept = attrs.get("accept")
        response = self.client.generate_presigned_post(
            self.bucket_name,
            str(pathlib.PurePosixPath(self.upload_folder, "${filename}")),
            Conditions=self.get_conditions(accept),
            ExpiresIn=self.expires,
        )

        defaults = {
            f"data-fields-{key}": value for key, value in response["fields"].items()
        }
        defaults["data-url"] = response["url"]
        # we sign upload location, and will only accept files within the same folder
        defaults["data-s3f-signature"] = S3FileMiddleware.sign_s3_key_prefix(
            self.upload_folder
        )
        defaults.update(attrs)

        try:
            defaults["class"] += " s3file"
        except KeyError:
            defaults["class"] = "s3file"
        return defaults

    def get_conditions(self, accept):
        conditions = [
            {"bucket": self.bucket_name},
            ["starts-with", "$key", str(self.upload_folder)],
            {"success_action_status": "201"},
        ]
        if accept and "," not in accept:
            top_type, sub_type = accept.split("/", 1)
            if sub_type == "*":
                conditions.append(["starts-with", "$Content-Type", f"{top_type}/"])
            else:
                conditions.append({"Content-Type": accept})
        else:
            conditions.append(["starts-with", "$Content-Type", ""])

        return conditions

    @cached_property
    def upload_folder(self):
        return str(
            pathlib.PurePosixPath(
                self.upload_path,
                base64
                .urlsafe_b64encode(uuid.uuid4().bytes)
                .decode("utf-8")
                .rstrip("=\n"),
            )
        )  # S3 uses POSIX paths

    class Media:
        js = [Script("s3file/js/s3file.js", type="module")]
