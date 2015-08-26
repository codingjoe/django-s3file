# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import logging
import os

import django
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse_lazy
from django.forms.widgets import ClearableFileInput
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

from six.moves.urllib.parse import unquote_plus

logger = logging.getLogger('s3file')


class S3FileInput(ClearableFileInput):
    """
    FileInput that uses JavaScript to directly upload to Amazon S3.
    """
    needs_multipart_form = False
    signing_url = reverse_lazy('s3file-sign')
    template = (
        '<div class="s3file" data-policy-url="{policy_url}">'
        '  <a class="file-link" target="_blank" href="{file_url}">{file_name}</a>'
        '  <a class="file-remove" href="#remove">Remove</a>'
        '  <input class="file-url" type="hidden" value="{value}"'
        ' id="{element_id}" name="{name}" />'
        '  <input class="file-input" type="file" />'
        '  <div class="progress progress-striped active">'
        '    <div class="bar"></div>'
        '  </div>'
        '</div>'
    )

    def render(self, name, value, attrs=None):
        final_attrs = self.build_attrs(attrs)
        element_id = final_attrs.get('id')
        if self.is_initial(value):
            file_url = value.url
            file_name = os.path.basename(value.name)
        else:
            file_url = ''
            file_name = ''
        if file_url:
            input_value = 'initial'
        else:
            input_value = ''

        output = self.template.format(
            policy_url=self.signing_url,
            file_url=file_url,
            file_name=file_name,
            element_id=element_id or '',
            name=name,
            value=input_value,
            remove=force_text(self.clear_checkbox_label)
        )

        return mark_safe(output)

    def is_initial(self, value):
        if django.VERSION < (1, 8):
            return bool(value and hasattr(value, 'url'))
        return super(S3FileInput, self).is_initial(value)

    def value_from_datadict(self, data, files, name):
        filename = data.get(name)
        if not filename:
            return False
        elif filename == 'initial':
            return None
        try:
            relative_filename = unquote_plus(filename[len(default_storage.url('')):])
            f = default_storage.open(relative_filename)
            return f
        except IOError:
            logger.exception('File "%s" could not be found.', filename)
            return False

    class Media:
        js = (
            's3file/js/s3file.js',

        )
        css = {
            'all': (
                's3file/css/s3file.css',
            )
        }


if hasattr(settings, 'AWS_SECRET_ACCESS_KEY') \
        and settings.AWS_SECRET_ACCESS_KEY:
    AutoFileInput = S3FileInput
else:
    AutoFileInput = ClearableFileInput
