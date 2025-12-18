import base64
import html
import logging
import pathlib
import uuid
from html.parser import HTMLParser

from django.conf import settings
from django.templatetags.static import static
from django.utils.functional import cached_property
from django.utils.html import format_html, html_safe
from django.utils.safestring import mark_safe
from storages.utils import safe_join

from s3file.middleware import S3FileMiddleware
from s3file.storages import get_aws_location, storage

logger = logging.getLogger("s3file")


class InputToS3FileRewriter(HTMLParser):
    """
    HTML parser that rewrites <input type="file"> tags to <s3-file> custom elements.

    This provides a robust way to transform Django's rendered file input widgets
    into custom elements, handling various attribute orderings and formats.
    """

    def __init__(self):
        super().__init__()
        self.output = []

    def _is_file_input(self, attrs):
        """Check if attributes indicate a file input element."""
        attrs_dict = dict(attrs)
        return attrs_dict.get("type") == "file"

    def handle_starttag(self, tag, attrs):
        if tag == "input" and self._is_file_input(attrs):
            # Replace with s3-file custom element
            self._write_s3_file_tag(attrs)
            return

        # For all other tags, preserve as-is
        self.output.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        self.output.append(f"</{tag}>")

    def handle_data(self, data):
        self.output.append(data)

    def handle_startendtag(self, tag, attrs):
        # For self-closing tags
        if tag == "input" and self._is_file_input(attrs):
            # Replace with s3-file custom element
            self._write_s3_file_tag(attrs)
            return

        self.output.append(self.get_starttag_text())

    def _write_s3_file_tag(self, attrs):
        """
        Write the s3-file opening tag with all attributes except type.

        Note: This creates an opening tag that requires a corresponding closing tag.
        """
        self.output.append("<s3-file")
        for name, value in attrs:
            if name != "type":  # Skip type attribute
                if value is None:
                    self.output.append(f" {name}")
                else:
                    escaped_value = html.escape(value, quote=True)
                    self.output.append(f' {name}="{escaped_value}"')
        self.output.append(">")

    def get_html(self):
        """Return the transformed HTML."""
        return "".join(self.output)


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
            f"data-fields-{key}": value for key, value in response["fields"].items()
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
        html_output = str(super().render(name, value, attrs=attrs, renderer=renderer))
        parser = InputToS3FileRewriter()
        parser.feed(html_output)
        return mark_safe(parser.get_html())  # noqa: S308

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
                base64.urlsafe_b64encode(uuid.uuid4().bytes)
                .decode("utf-8")
                .rstrip("=\n"),
            )
        )  # S3 uses POSIX paths

    class Media:
        js = [ESM("s3file/js/s3file.js")]
