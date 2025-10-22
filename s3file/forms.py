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
        """Render the widget as a custom element for Safari compatibility."""
        # Build attributes for the render - this includes data-* attributes
        if attrs is None:
            attrs = {}
        
        # Ensure name is in attrs
        attrs = attrs.copy() if attrs else {}
        attrs['name'] = name
        
        # Get all the attributes including data-* attributes from build_attrs
        final_attrs = self.build_attrs(self.attrs, attrs)
        
        # Build attributes string for the s3-file element
        from django.utils.html import format_html_join
        from django.utils.safestring import mark_safe
        attrs_html = format_html_join(
            ' ',
            '{}="{}"',
            final_attrs.items()
        )
        
        # Render the s3-file custom element
        # For ClearableFileInput, we also need to show the current value and clear checkbox
        output = []
        if value and hasattr(value, 'url'):
            # Show currently uploaded file (similar to ClearableFileInput)
            output.append(format_html(
                '<div>Currently: <a href="{}">{}</a></div>',
                value.url,
                value
            ))
            # Add clear checkbox
            clear_checkbox_name = self.clear_checkbox_name(name)
            clear_checkbox_id = self.clear_checkbox_id(clear_checkbox_name)
            output.append(format_html(
                '<div><input type="checkbox" name="{}" id="{}"><label for="{}"> Clear</label></div>',
                clear_checkbox_name,
                clear_checkbox_id,
                clear_checkbox_id
            ))
        
        # Add the s3-file custom element
        output.append(format_html('<s3-file {}></s3-file>', attrs_html))
        
        return mark_safe(''.join(str(part) for part in output))

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
