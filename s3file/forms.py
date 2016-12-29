# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import logging

import django
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse_lazy
from django.forms.widgets import (
    FILE_INPUT_CONTRADICTION, CheckboxInput, ClearableFileInput
)
from django.utils.safestring import mark_safe

from .conf import settings

logger = logging.getLogger('s3file')


class S3FileInput(ClearableFileInput):
    """FileInput that uses JavaScript to directly upload to Amazon S3."""

    needs_multipart_form = False
    signing_url = reverse_lazy('s3file-sign')
    template = (
        '<div class="s3file" data-policy-url="{policy_url}">'
        '{input}'
        '<input name="{name}" type="hidden" />'
        '<div class="progress progress-striped active">'
        '<div class="progress-bar" />'
        '</div>'
        '</div>'
    )

    def render(self, name, value, attrs=None):
        parent_input = super(S3FileInput, self).render(name, value, attrs=None)
        parent_input = parent_input.replace('name="{}"'.format(name), '')
        output = self.template.format(
            policy_url=self.signing_url,
            input=parent_input,
            name=name,
        )
        return mark_safe(output)

    def is_initial(self, value):
        return super(S3FileInput, self).is_initial(value)

    def value_from_datadict(self, data, files, name):
        filename = data.get(name, None)
        if not self.is_required and CheckboxInput().value_from_datadict(
                data, files, self.clear_checkbox_name(name)):
            if filename:
                # If the user contradicts themselves (uploads a new file AND
                # checks the "clear" checkbox), we return a unique marker
                # object that FileField will turn into a ValidationError.
                return FILE_INPUT_CONTRADICTION
            # False signals to clear any existing value, as opposed to just None
            return False
        if not filename:
            return None
        try:
            upload = default_storage.open(filename)
        except IOError:
            logger.exception('File "%s" could not be found.', filename)
            return False
        else:
            return upload

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
