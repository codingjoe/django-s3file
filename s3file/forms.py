import base64
import logging
import pathlib
import uuid

from django.conf import settings
from django.templatetags.static import static
from django.utils.functional import cached_property
from django.utils.html import format_html, html_safe
from storages.utils import safe_join

from s3file.middleware import S3FileMiddleware
from s3file.storages import get_aws_location, storage

logger = logging.getLogger("s3file")


@html_safe
class Asset:
    """A generic asset that can be included in a template."""

    def __init__(self, path):
        self.path = path

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and self.path == other.path) or (
            other.__class__ is str and self.path == other
        )

    def __hash__(self):
        return hash(self.path)

    def __str__(self):
        return self.absolute_path(self.path)

    def absolute_path(self, path):
        if path.startswith(("http://", "https://", "/")):
            return path
        return static(path)

    def __repr__(self):
        return f"{type(self).__qualname__}: {self.path!r}"


class ESM(Asset):
    """A JavaScript asset for ECMA Script Modules (ESM)."""

    def __str__(self):
        path = super().__str__()
        template = '<script src="{}" type="module"></script>'
        return format_html(template, self.absolute_path(path))


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
            "data-fields-%s" % key: value for key, value in response["fields"].items()
        }
        defaults["data-url"] = response["url"]
        # we sign upload location, and will only accept files within the same folder
        defaults["data-s3f-signature"] = S3FileMiddleware.sign_s3_key_prefix(
            self.upload_folder
        )
        defaults.update(attrs)

        return defaults

    def render(self, name, value, attrs=None, renderer=None):
        """Render the widget wrapped in a custom element for Safari compatibility."""
        # Build attributes for the render - this includes data-* attributes
        if attrs is None:
            attrs = {}
        
        # Get all the attributes including data-* attributes from build_attrs
        final_attrs = self.build_attrs(self.attrs, attrs)
        
        # Separate data-* attributes for the wrapper from other attributes for the input
        wrapper_attrs = {k: v for k, v in final_attrs.items() if k.startswith("data-")}
        input_attrs = {k: v for k, v in final_attrs.items() if not k.startswith("data-")}
        
        # Temporarily override build_attrs to return only non-data attributes for the input
        original_build_attrs = self.build_attrs
        def build_attrs_without_data(*args, **kwargs):
            attrs_dict = original_build_attrs(*args, **kwargs)
            return {k: v for k, v in attrs_dict.items() if not k.startswith("data-")}
        
        self.build_attrs = build_attrs_without_data
        try:
            # Call parent's render which will use our modified build_attrs
            input_html = super().render(name, value, input_attrs, renderer)
        finally:
            # Restore original build_attrs
            self.build_attrs = original_build_attrs
        
        # Build wrapper attributes string
        from django.utils.html import format_html_join
        wrapper_attrs_html = format_html_join(
            ' ',
            '{}="{}"',
            wrapper_attrs.items()
        )
        
        # Wrap the input in the s3-file custom element
        if wrapper_attrs_html:
            return format_html('<s3-file {}>{}</s3-file>', wrapper_attrs_html, input_html)
        else:
            return format_html('<s3-file>{}</s3-file>', input_html)

    def get_conditions(self, accept):
        conditions = [
            {"bucket": self.bucket_name},
            ["starts-with", "$key", str(self.upload_folder)],
            {"success_action_status": "201"},
        ]
        if accept and "," not in accept:
            top_type, sub_type = accept.split("/", 1)
            if sub_type == "*":
                conditions.append(["starts-with", "$Content-Type", "%s/" % top_type])
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
                base64.urlsafe_b64encode(uuid.uuid4().bytes)
                .decode("utf-8")
                .rstrip("=\n"),
            )
        )  # S3 uses POSIX paths

    class Media:
        js = [ESM("s3file/js/s3file.js")]
