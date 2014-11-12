from urlparse import urlparse
import urllib2

from django.forms.widgets import ClearableFileInput
from django.core.files.storage import default_storage
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext


class S3FileInput(ClearableFileInput):
    needs_multipart_form = False
    signing_url = reverse_lazy('s3file-sign')
    template = (
        '<div class="s3file" data-url="{signing_url}" data-target="{element_id}">\n'
        '    <a class="link" target="_blank" href="{file_url}">{file_url}</a>\n'
        '    <a class="remove" href="javascript: void(0)">{remove}</a>\n'
        '    <input type="hidden" value="initial" id="{element_id}" name="{name}" />\n'
        '    <input type="file" class="fileinput" id="s3-{element_id}" />\n'
        '    <div class="progress progress-striped active">\n'
        '        <div class="progress-bar"></div>\n'
        '    </div>\n'
        '</div>'
    )

    def render(self, name, value, attrs=None):
        final_attrs = self.build_attrs(attrs)
        element_id = final_attrs.get('id')

        if value:
            file_url = default_storage.url(value)
        else:
            file_url = ''

        output = self.template.format(
            signing_url=self.signing_url,
            file_url=file_url,
            element_id=element_id or '',
            name=name,
            remove=ugettext('remove')
        )

        return mark_safe(output)

    def value_from_datadict(self, data, files, name):
        url = data.get(name)
        upload = files.get(name, False)
        if url:
            if url == 'initial':
                return None
            filename = urllib2.unquote(urlparse(url).path)
            try:
                f = default_storage.open(filename)
                return f
            except IOError:
                return False
        return upload

    class Media:
        js = (
            's3file/js/jquery.iframe-transport.js',
            's3file/js/jquery.ui.widget.js',
            's3file/js/jquery.fileupload.js',
            's3file/js/s3file.js',
        )
        css = {
            'all': (
                's3file/css/s3file.css',
            )
        }
